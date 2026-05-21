from app.locales import schema_field_description
from typing import Any, Dict, List, Optional, AsyncIterator
import os
import re
from loguru import logger
from pydantic import Field, BaseModel

from ...registry import register_node
from ..base import BaseNode


class NovelLoadInput(BaseModel):
    root_path: str = Field(
        ...,
        description=schema_field_description("root_path"),
        json_schema_extra={"x-component": "DirectorySelect"}
    )
    file_pattern: str = Field(
        r".*\.(txt|md)$",
        description=schema_field_description("file_pattern")
    )
    volume_pattern: str = Field(
        "Default volume",
        description=schema_field_description("volume_pattern")
    )
    chapter_pattern: str = Field(
        "Default volume",
        description=schema_field_description("chapter_pattern")
    )


class NovelLoadOutput(BaseModel):
    chapter_list: List[Dict[str, Any]] = Field(..., description=schema_field_description("chapter_list"))
    volume_list: List[str] = Field(..., description=schema_field_description("volume_list"))


@register_node
class NovelLoadNode(BaseNode[NovelLoadInput, NovelLoadOutput]):
    node_type = "Novel.Load"
    category = "novel"
    label = "Load Novel"
    description = "Scan a novel directory and load chapter metadata"

    input_model = NovelLoadInput
    output_model = NovelLoadOutput

    async def execute(self, inputs: NovelLoadInput) -> AsyncIterator[NovelLoadOutput]:
        if not os.path.exists(inputs.root_path):
            raise ValueError(f"\u76ee\u5f55\u4e0d\u5b58\u5728: {inputs.root_path}")

        chapter_list = []
        volumes = set()

        try:
            file_re = re.compile(inputs.file_pattern)
            vol_re = re.compile(inputs.volume_pattern)
            chap_re = re.compile(inputs.chapter_pattern)
        except Exception as e:
            raise ValueError(f"\u6b63\u5219\u7f16\u8bd1\u5931\u8d25: {e}")


        for dirpath, dirnames, filenames in os.walk(inputs.root_path):
            rel_path = os.path.relpath(dirpath, inputs.root_path)
            current_volume = "Default volume"

            if rel_path != ".":
                parts = rel_path.split(os.sep)
                if parts:
                    potential_vol = parts[0]
                    if vol_re.search(potential_vol):
                        current_volume = potential_vol
                    else:
                        current_volume = potential_vol

            volumes.add(current_volume)

            for fname in filenames:
                if not file_re.match(fname):
                    continue

                full_path = os.path.join(dirpath, fname)
                title = os.path.splitext(fname)[0]

                idx = 0
                match = chap_re.search(title)
                if match:
                    if match.groups():
                        try:
                            idx = int(match.group(1))
                        except ValueError:
                            pass
                    else:
                        num_match = re.search(r"\d+", match.group())
                        if num_match:
                            idx = int(num_match.group())

                meta = {
                    "title": title,
                    "path": full_path,
                    "volume": current_volume,
                    "index": idx,
                    "filename": fname
                }
                chapter_list.append(meta)

        chapter_list.sort(key=lambda x: (x['volume'], x['index'], x['title']))

        volumes_set = set(item['volume'] for item in chapter_list)

        def natural_sort_key(text):
            import re

            chinese_num_map = {
                "Default volume": 0, "Default volume": 1, "Default volume": 2, "Default volume": 3, "Default volume": 4,
                "Default volume": 5, "Default volume": 6, "Default volume": 7, "Default volume": 8, "Default volume": 9, "Default volume": 10,
                "Default volume": 100, "Default volume": 1000
            }

            def chinese_to_num(s):
                if not s:
                    return 0
                if s in chinese_num_map:
                    return chinese_num_map[s]
                if "Default volume" in s:
                    parts = s.split("Default volume")
                    if len(parts) == 2:
                        left = chinese_num_map.get(parts[0], 1 if not parts[0] else 0)
                        right = chinese_num_map.get(parts[1], 0)
                        return left * 10 + right
                return 0

            match = re.search("Default volume", text)
            if match:
                num_str = match.group(1)
                if num_str.isdigit():
                    return int(num_str)
                return chinese_to_num(num_str)
            return 0

        volumes = sorted(list(volumes_set), key=natural_sort_key)


        yield NovelLoadOutput(
            chapter_list=chapter_list,
            volume_list=volumes
        )
