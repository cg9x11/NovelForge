from app.locales import localized_text
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from app.db.models import Prompt
from app.schemas.prompt import PromptCreate, PromptUpdate
from app.services.builtin_key_registry import PROMPT_NAME_TO_KEY, resolve_builtin_key, slugify_name
from string import Template
import re

def get_prompt(session: Session, prompt_id: int) -> Optional[Prompt]:
    """delayIDdelaydelaydelayseconds"""
    return session.get(Prompt, prompt_id)


def get_prompt_by_key(session: Session, prompt_key: str) -> Optional[Prompt]:
    statement = select(Prompt).where(Prompt.key == prompt_key)
    return session.exec(statement).first()


def resolve_prompt_key(identifier: str) -> str:
    from app.services.builtin_key_registry import PROMPT_NAME_TO_KEY, resolve_builtin_key, slugify_name
    return resolve_builtin_key(identifier, PROMPT_NAME_TO_KEY) or identifier


def get_prompt_by_name(session: Session, prompt_name: str) -> Optional[Prompt]:
    """delaydelaydelaydelaydelaydelaydelaydelayseconds"""
    statement = select(Prompt).where(Prompt.name == prompt_name)
    prompt = session.exec(statement).first()
    if prompt:
        return prompt
    resolved = resolve_prompt_key(prompt_name)
    if resolved and resolved != prompt_name:
        return get_prompt_by_key(session, resolved)
    return None


def get_prompt_by_slug(session: Session, prompt_slug: str) -> Optional[Prompt]:
    normalized = slugify_name(prompt_slug)
    if not normalized:
        return None
    for prompt in session.exec(select(Prompt)).all():
        candidates = [getattr(prompt, 'key', None), getattr(prompt, 'name', None)]
        if any(slugify_name(value or '') == normalized for value in candidates):
            return prompt
    return None


def get_prompt_by_identifier(session: Session, identifier: str) -> Optional[Prompt]:
    prompt = get_prompt_by_key(session, identifier)
    if prompt:
        return prompt
    prompt = get_prompt_by_name(session, identifier)
    if prompt:
        return prompt
    return get_prompt_by_slug(session, identifier)

def get_prompts(session: Session, skip: int = 0, limit: int = 100) -> List[Prompt]:
    statement = select(Prompt).offset(skip).limit(limit)
    return session.exec(statement).all()

def create_prompt(session: Session, prompt_create: PromptCreate) -> Prompt:
    existing_prompt = get_prompt_by_name(session, prompt_create.name)
    if existing_prompt:
        raise ValueError(f"Prompt name '{prompt_create.name}' already exists")

    payload = prompt_create.model_dump()
    payload["key"] = payload.get("key") or resolve_builtin_key(prompt_create.name, PROMPT_NAME_TO_KEY)
    if payload.get("key") and get_prompt_by_key(session, payload["key"]):
        raise ValueError(f"Prompt key '{payload['key']}' already exists")
    db_prompt = Prompt.model_validate(payload)
    session.add(db_prompt)
    session.commit()
    session.refresh(db_prompt)
    return db_prompt

def update_prompt(session: Session, prompt_id: int, prompt_update: PromptUpdate) -> Optional[Prompt]:
    db_prompt = session.get(Prompt, prompt_id)
    if not db_prompt:
        return None
    prompt_data = prompt_update.model_dump(exclude_unset=True)
    next_key = prompt_data.get("key", getattr(db_prompt, "key", None))
    if next_key:
        existing = get_prompt_by_key(session, next_key)
        if existing and existing.id != prompt_id:
            raise ValueError(f"Prompt key '{next_key}' already exists")
    for key, value in prompt_data.items():
        setattr(db_prompt, key, value)
    if not getattr(db_prompt, "key", None):
        db_prompt.key = resolve_builtin_key(db_prompt.name, PROMPT_NAME_TO_KEY)
    session.add(db_prompt)
    session.commit()
    session.refresh(db_prompt)
    return db_prompt

def delete_prompt(session: Session, prompt_id: int) -> bool:
    db_prompt = session.get(Prompt, prompt_id)
    if not db_prompt:
        return False
    session.delete(db_prompt)
    session.commit()
    return True

def render_prompt(prompt_template: str, context: Dict[str, Any]) -> str:
    template = Template(prompt_template)
    try:
        return template.substitute(context)
    except KeyError as e:
        raise ValueError(f"Failed to render prompt: missing variable '{e.args[0]}' in context")
    except Exception as e:
        raise ValueError(f"Unexpected error while rendering prompt: {e}")


_KB_ID_PATTERN = re.compile(r"@KB\{\s*id\s*=\s*(\d+)\s*\}")
_KB_NAME_PATTERN = re.compile(r"@KB\{\s*name\s*=\s*([^}]+)\}")


def inject_knowledge(session: Session, template: str) -> str:
    from app.services.knowledge_service import KnowledgeService

    svc = KnowledgeService(session)

    def fetch_kb_by_id(kid: int) -> str:
        kb = svc.get_by_id(kid)
        return kb.content if kb and kb.content else localized_text('hardcoded.services_prompt_service_59c53296', kid=kid)

    def fetch_kb_by_name(name: str) -> str:
        kb = svc.get_by_identifier(name)
        return kb.content if kb and kb.content else localized_text('hardcoded.services_prompt_service_b16dad8e', name=name)

    lines = template.splitlines()
    i = 0
    out_lines: list[str] = []
    while i < len(lines):
        line = lines[i]
        if re.match(r"^\s*-\s*knowledge\s*:\s*$", line, flags=re.IGNORECASE):
            j = i + 1
            block_lines: list[str] = []
            while j < len(lines) and not re.match(r"^\s*-\s*\w", lines[j]):
                block_lines.append(lines[j])
                j += 1
            placeholders: list[tuple[str, str]] = []  # (mode, value)
            for bl in block_lines:
                for m in _KB_ID_PATTERN.finditer(bl):
                    placeholders.append(("id", m.group(1)))
                for m in _KB_NAME_PATTERN.finditer(bl):
                    placeholders.append(("name", m.group(1).strip().strip('\"\'')))
            out_lines.append(line)
            if placeholders:
                for idx, (mode, val) in enumerate(placeholders, start=1):
                    out_lines.append(f"{idx}.")
                    if mode == "id":
                        try:
                            content = fetch_kb_by_id(int(val))
                        except Exception:
                            content = localized_text('hardcoded.services_prompt_service_87d13f69', val=val)
                    else:
                        content = fetch_kb_by_name(val)
                    out_lines.append(content.strip())
                    if idx < len(placeholders):
                        out_lines.append("")
            i = j
            continue
        else:
            out_lines.append(line)
            i += 1

    enumerated_text = "\n".join(out_lines)

    def repl_id(m: re.Match) -> str:
        try:
            kid = int(m.group(1))
        except Exception:
            return localized_text('hardcoded.services_prompt_service_dfb3b91e', m_group_1=m.group(1))
        return fetch_kb_by_id(kid)

    def repl_name(m: re.Match) -> str:
        name = m.group(1).strip().strip('\"\'')
        return fetch_kb_by_name(name)

    result = _KB_ID_PATTERN.sub(repl_id, enumerated_text)
    result = _KB_NAME_PATTERN.sub(repl_name, result)
    return result
