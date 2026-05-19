"""提示词初始化

从文件系统加载提示词模板并初始化到数据库。
"""

import os
from sqlmodel import Session, select
from loguru import logger

from app.db.models import Prompt
from app.services.builtin_key_registry import PROMPT_NAME_TO_KEY, resolve_builtin_key
from app.core.config import settings
from .registry import initializer


def _parse_prompt_file(file_path: str) -> dict:
    """解析单个提示词文件
    
    Args:
        file_path: 提示词文件路径
        
    Returns:
        包含name, description, template的字典
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    filename = os.path.basename(file_path)
    name = os.path.splitext(filename)[0]
    description = f"AI任务提示词: {name}"
            
    return {
        "name": name,
        "description": description,
        "template": content.strip()
    }


def get_all_prompt_files() -> dict:
    """从文件系统加载所有提示词
    
    Returns:
        提示词字典，key为提示词名称
    """
    prompt_dir = os.path.join(os.path.dirname(__file__), 'prompts')
    if not os.path.exists(prompt_dir):
        logger.warning(f"Prompt directory not found at {prompt_dir}. Cannot load prompts.")
        return {}

    prompt_files = {}
    for filename in os.listdir(prompt_dir):
        if filename.endswith(('.prompt', '.txt')):
            file_path = os.path.join(prompt_dir, filename)
            name = os.path.splitext(filename)[0]
            prompt_files[name] = _parse_prompt_file(file_path)
    return prompt_files


@initializer(name="提示词", order=10)
def init_prompts(session: Session) -> None:
    """初始化默认提示词
    
    行为受配置项 BOOTSTRAP_OVERWRITE 控制：
    - True: 覆盖更新已存在的提示词
    - False: 跳过已存在的提示词
    
    Args:
        session: 数据库会话
    """
    overwrite = settings.bootstrap.should_overwrite
    existing_prompts = session.exec(select(Prompt)).all()
    for existing_prompt in existing_prompts:
        mapped_key = PROMPT_NAME_TO_KEY.get((existing_prompt.name or '').strip())
        if mapped_key or not getattr(existing_prompt, "key", None):
            existing_prompt.key = mapped_key or resolve_builtin_key(existing_prompt.name, PROMPT_NAME_TO_KEY)
    existing_by_name = {p.name: p for p in existing_prompts}
    existing_by_key = {p.key: p for p in existing_prompts if getattr(p, "key", None)}

    all_prompts_data = get_all_prompt_files()

    new_count = 0
    updated_count = 0
    skipped_count = 0
    prompts_to_add = []
    
    for name, prompt_data in all_prompts_data.items():
        prompt_key = prompt_data.get('key') or resolve_builtin_key(name, PROMPT_NAME_TO_KEY)
        existing_prompt = existing_by_key.get(prompt_key) or existing_by_name.get(name)
        if existing_prompt:
            if overwrite:
                existing_prompt.name = name
                existing_prompt.template = prompt_data['template']
                existing_prompt.description = prompt_data.get('description')
                existing_prompt.key = prompt_key or existing_prompt.key
                existing_prompt.built_in = True
                updated_count += 1
            else:
                if not getattr(existing_prompt, "key", None) and prompt_key:
                    existing_prompt.key = prompt_key
                    session.add(existing_prompt)
                skipped_count += 1
        else:
            prompts_to_add.append(Prompt(**prompt_data, built_in=True))
            new_count += 1
    
    if prompts_to_add:
        session.add_all(prompts_to_add)

    if new_count > 0 or updated_count > 0:
        session.commit()
        logger.info(f"提示词更新完成: 新增 {new_count} 个，更新 {updated_count} 个（overwrite={overwrite}，跳过 {skipped_count} 个）。")
    else:
        logger.info(f"所有提示词已是最新状态（overwrite={overwrite}，跳过 {skipped_count} 个）。")
