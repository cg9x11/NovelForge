
import re
from typing import Dict, Any, Optional
from pydantic import ValidationError
from loguru import logger


_ARRAY_INDEX_PATTERN = re.compile(r"\[(\d+)\]")


def normalize_instruction_path(path: Any) -> str:
    if not isinstance(path, str):
        return ""

    normalized = path.strip()
    if not normalized:
        return ""

    if normalized == "$":
        return "/"
    if normalized.startswith("$."):
        normalized = normalized[2:]

    # items[0] -> items/0
    normalized = _ARRAY_INDEX_PATTERN.sub(r"/\1", normalized)
    # config.theme -> config/theme
    normalized = normalized.replace(".", "/")

    if not normalized.startswith("/"):
        normalized = "/" + normalized.lstrip("/")

    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    return normalized



def resolve_schema(schema: Dict[str, Any], root_schema: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(schema, dict):
        return schema

    resolved = schema

    if '$ref' in resolved:
        ref_path = resolved['$ref']
        if ref_path.startswith('#/'):
            parts = ref_path.split('/')
            # parts[0] is '#', parts[1] is '$defs' or 'definitions', parts[2] is model name
            if len(parts) >= 3:
                def_section = parts[1]
                model_name = parts[2]
                if def_section in root_schema and model_name in root_schema[def_section]:
                    return resolve_schema(root_schema[def_section][model_name], root_schema)

    if 'allOf' in resolved:
        merged = {}
        for sub_schema in resolved['allOf']:
            sub_resolved = resolve_schema(sub_schema, root_schema)
            if isinstance(sub_resolved, dict):
                if 'properties' in sub_resolved:
                    if 'properties' not in merged:
                        merged['properties'] = {}
                    merged['properties'].update(sub_resolved['properties'])
                if 'required' in sub_resolved:
                    if 'required' not in merged:
                        merged['required'] = []
                    merged['required'].extend(sub_resolved['required'])
                if 'type' in sub_resolved and 'type' not in merged:
                    merged['type'] = sub_resolved['type']

        for k, v in resolved.items():
            if k != 'allOf':
                if k == 'properties':
                    if 'properties' not in merged:
                        merged['properties'] = {}
                    merged['properties'].update(v)
                elif k == 'required':
                    if 'required' not in merged:
                        merged['required'] = []
                    new_reqs = [r for r in v if r not in merged['required']]
                    merged['required'].extend(new_reqs)
                else:
                    merged[k] = v
        return merged

    return resolved


def get_field_schema_by_path(schema: Dict[str, Any], path: str) -> Optional[Dict[str, Any]]:
    path = normalize_instruction_path(path)
    if not path or not path.startswith('/'):
        return None

    path = path[1:]
    if not path:
        return schema

    parts = path.split('/')
    current_schema = schema

    for part in parts:
        current_schema = resolve_schema(current_schema, schema)

        if part.isdigit():
            if 'items' in current_schema:
                current_schema = current_schema['items']
            elif 'prefixItems' in current_schema:
                 idx = int(part)
                 if idx < len(current_schema['prefixItems']):
                     current_schema = current_schema['prefixItems'][idx]
                 else:
                     return None
            else:
                found_array = False
                for key in ['anyOf', 'oneOf']:
                    if key in current_schema:
                        for option in current_schema[key]:
                            resolved_option = resolve_schema(option, schema)
                            if resolved_option.get('type') == 'array' and 'items' in resolved_option:
                                current_schema = resolved_option['items']
                                found_array = True
                                break
                        if found_array:
                            break
                if not found_array:
                    return None
        else:
            if 'properties' in current_schema and part in current_schema['properties']:
                current_schema = current_schema['properties'][part]
            else:
                found_prop = False
                for key in ['anyOf', 'oneOf']:
                    if key in current_schema:
                        for option in current_schema[key]:
                            resolved_option = resolve_schema(option, schema)
                            if 'properties' in resolved_option and part in resolved_option['properties']:
                                current_schema = resolved_option['properties'][part]
                                found_prop = True
                                break
                        if found_prop:
                            break

                if not found_prop:
                    return None

    return resolve_schema(current_schema, schema)


def validate_type(value: Any, expected_type: Optional[str]) -> bool:
    if expected_type is None:
        return True

    type_mapping = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }

    expected_python_type = type_mapping.get(expected_type)
    if expected_python_type is None:
        return True

    return isinstance(value, expected_python_type)


def _resolve_schema_variant_by_type(
    schema_node: Dict[str, Any],
    root_schema: Dict[str, Any],
    target_type: str,
) -> Optional[Dict[str, Any]]:
    resolved = resolve_schema(schema_node, root_schema)
    if resolved.get('type') == target_type:
        return resolved

    for union_key in ('anyOf', 'oneOf'):
        options = resolved.get(union_key)
        if not isinstance(options, list):
            continue
        for option in options:
            resolved_option = resolve_schema(option, root_schema)
            if resolved_option.get('type') == target_type:
                return resolved_option
    return None


def _validate_constraints(value: Any, schema_node: Dict[str, Any], path: str) -> None:
    expected_type = schema_node.get('type')

    if 'enum' in schema_node and value not in schema_node['enum']:
        raise ValueError(f"\u5b57\u6bb5 {path} \u7684\u503c\u4e0d\u5728\u679a\u4e3e\u8303\u56f4\u5185：{schema_node['enum']}")

    if expected_type in ['integer', 'number']:
        if 'minimum' in schema_node and value < schema_node['minimum']:
            raise ValueError(f"\u5b57\u6bb5 {path} \u7684\u503c {value} \u5c0f\u4e8e\u6700\u5c0f\u503c {schema_node['minimum']}")
        if 'maximum' in schema_node and value > schema_node['maximum']:
            raise ValueError(f"\u5b57\u6bb5 {path} \u7684\u503c {value} \u5927\u4e8e\u6700\u5927\u503c {schema_node['maximum']}")

    if expected_type == 'string':
        if 'minLength' in schema_node and len(value) < schema_node['minLength']:
            raise ValueError(f"\u5b57\u6bb5 {path} \u7684\u957f\u5ea6 {len(value)} \u5c0f\u4e8e\u6700\u5c0f\u957f\u5ea6 {schema_node['minLength']}")
        if 'maxLength' in schema_node and len(value) > schema_node['maxLength']:
            raise ValueError(f"\u5b57\u6bb5 {path} \u7684\u957f\u5ea6 {len(value)} \u5927\u4e8e\u6700\u5927\u957f\u5ea6 {schema_node['maxLength']}")

    if expected_type == 'array' and isinstance(value, list):
        if 'minItems' in schema_node and len(value) < schema_node['minItems']:
            raise ValueError(f"\u6570\u7ec4 {path} \u7684\u957f\u5ea6 {len(value)} \u5c0f\u4e8e\u6700\u5c0f\u957f\u5ea6 {schema_node['minItems']}")
        if 'maxItems' in schema_node and len(value) > schema_node['maxItems']:
            raise ValueError(f"\u6570\u7ec4 {path} \u7684\u957f\u5ea6 {len(value)} \u5927\u4e8e\u6700\u5927\u957f\u5ea6 {schema_node['maxItems']}")


def validate_value_against_schema(
    value: Any,
    schema_node: Dict[str, Any],
    root_schema: Dict[str, Any],
    path: str,
) -> None:
    resolved = resolve_schema(schema_node, root_schema)

    for union_key in ('anyOf', 'oneOf'):
        options = resolved.get(union_key)
        if not isinstance(options, list):
            continue

        matched = False
        last_error: Optional[ValueError] = None
        for option in options:
            resolved_option = resolve_schema(option, root_schema)
            opt_type = resolved_option.get('type')
            if not validate_type(value, opt_type):
                continue
            try:
                validate_value_against_schema(value, resolved_option, root_schema, path)
                matched = True
                break
            except ValueError as exc:
                last_error = exc

        if not matched:
            if last_error:
                raise last_error
            allowed_types = [resolve_schema(opt, root_schema).get('type') for opt in options]
            raise ValueError(
                f"\u5b57\u6bb5\u7c7b\u578b\u6216\u7ed3\u6784\u9519\u8bef：\u8def\u5f84 {path}，\u671f\u671b {allowed_types} \u4e4b\u4e00。\u5b9e\u9645: {type(value).__name__}"
            )
        return

    expected_type = resolved.get('type')
    if expected_type and not validate_type(value, expected_type):
        raise ValueError(f"\u5b57\u6bb5\u7c7b\u578b\u9519\u8bef：\u8def\u5f84 {path}，\u671f\u671b {expected_type}，\u5b9e\u9645 {type(value).__name__}")

    _validate_constraints(value, resolved, path)

    if expected_type == 'object':
        validate_schema_structure(value, resolved, root_schema, path)
        return

    if expected_type == 'array' and isinstance(value, list):
        if isinstance(resolved.get('prefixItems'), list):
            for idx, item_schema in enumerate(resolved['prefixItems']):
                if idx >= len(value):
                    break
                validate_value_against_schema(value[idx], item_schema, root_schema, f"{path}/{idx}")
            return

        item_schema = resolved.get('items')
        if isinstance(item_schema, dict):
            for idx, item in enumerate(value):
                validate_value_against_schema(item, item_schema, root_schema, f"{path}/{idx}")


def validate_instruction(instruction: Dict[str, Any], schema: Dict[str, Any]) -> None:
    op = instruction.get('op')

    if op not in ['set', 'append', 'done']:
        raise ValueError(f"\u672a\u77e5\u7684\u6307\u4ee4\u64cd\u4f5c\u7c7b\u578b: {op}")

    if op == 'done':
        return

    path = instruction.get('path')
    value = instruction.get('value')

    if not path:
        raise ValueError("Instruction validation failed")

    path = normalize_instruction_path(path)
    instruction['path'] = path

    if value is None and op != 'set':
        raise ValueError(f"\u6307\u4ee4 {op} \u7f3a\u5c11 value \u5b57\u6bb5")

    field_schema = get_field_schema_by_path(schema, path)
    if not field_schema:
        raise ValueError(f"\u8def\u5f84 {path} \u4e0d\u5b58\u5728\u4e8e Schema \u4e2d")

    if op == 'append':
        actual_schema = _resolve_schema_variant_by_type(field_schema, schema, 'array')
        if not actual_schema:
            raise ValueError(f"\u8def\u5f84 {path} \u4e0d\u662f\u6570\u7ec4\u7c7b\u578b，\u65e0\u6cd5\u4f7f\u7528 append \u64cd\u4f5c")
        items_schema = actual_schema.get('items')
        if not isinstance(items_schema, dict):
            raise ValueError(f"\u8def\u5f84 {path} \u7684\u6570\u7ec4\u672a\u5b9a\u4e49 items \u7ed3\u6784，\u65e0\u6cd5\u4f7f\u7528 append \u64cd\u4f5c")
        validate_value_against_schema(value, items_schema, schema, f"{path}/-")

    else:
        validate_value_against_schema(value, field_schema, schema, path)

def validate_schema_structure(
    data: Any,
    schema_node: Dict[str, Any],
    root_schema: Dict[str, Any],
    path: str = "",
) -> None:
    if not isinstance(data, dict):
        return

    resolved = resolve_schema(schema_node, root_schema)

    if 'properties' in resolved:
        properties = resolved['properties']
        required_fields = set(resolved.get('required', []))


        for field_name, field_schema_ref in properties.items():
            field_schema = resolve_schema(field_schema_ref, root_schema)

            if field_name not in data:
                if 'default' in field_schema:
                    data[field_name] = field_schema['default']
                elif field_name in required_fields:
                    raise ValueError(f"\u7f3a\u5c11\u5fc5\u586b\u5b57\u6bb5: {field_name}")
                continue

            field_path = f"{path}/{field_name}" if path else f"/{field_name}"

            field_value = data[field_name]

            validate_value_against_schema(field_value, field_schema, root_schema, field_path)



def apply_instruction(data: Dict[str, Any], instruction: Dict[str, Any]) -> None:
    op = instruction.get('op')

    if op == 'done':
        return

    path = normalize_instruction_path(instruction.get('path', ''))
    value = instruction.get('value')

    if path.startswith('/'):
        path = path[1:]

    if not path:
        return

    parts = path.split('/')
    current = data

    for i, part in enumerate(parts[:-1]):
        if part.isdigit():
            idx = int(part)
            if not isinstance(current, list):
                return

            while len(current) <= idx:
                current.append({})

            current = current[idx]
        else:
            if part not in current:
                next_part = parts[i + 1] if i + 1 < len(parts) else None
                if next_part and next_part.isdigit():
                    current[part] = []
                else:
                    current[part] = {}

            current = current[part]

    last_part = parts[-1]

    if op == 'set':
        if last_part.isdigit():
            idx = int(last_part)
            if isinstance(current, list):
                while len(current) <= idx:
                    current.append(None)
                current[idx] = value
        else:
            current[last_part] = value

    elif op == 'append':
        if last_part.isdigit():
            return

        if last_part not in current or current[last_part] is None:
            current[last_part] = []

        if not isinstance(current[last_part], list):
            return

        current[last_part].append(value)


def format_validation_errors(errors: list) -> str:
    lines = []
    for error in errors:
        loc = ' -> '.join(str(l) for l in error.get('loc', []))
        msg = error.get('msg', "Validation error")
        lines.append(f"- {loc}: {msg}")

    return '\n'.join(lines)


def extract_error_fields(validation_error: ValidationError) -> list[str]:
    fields = []
    for error in validation_error.errors():
        loc = error.get('loc', ())
        if loc:
            path = '/' + '/'.join(str(l) for l in loc)
            fields.append(path)

    return fields


class InstructionExecutor:


    def __init__(self, schema: Dict[str, Any], initial_data: Optional[Dict[str, Any]] = None):
        self.schema = schema
        self.data = initial_data.copy() if initial_data else {}
        self.stats = {
            "executed": 0,
            "success": 0,
            "failed": 0
        }

    def execute(self, instruction: Dict[str, Any]) -> None:
        self.stats["executed"] += 1

        try:
            validate_instruction(instruction, self.schema)

            apply_instruction(self.data, instruction)

            self.stats["success"] += 1

        except Exception as e:
            self.stats["failed"] += 1
            raise

    def execute_batch(self, instructions: list[Dict[str, Any]]) -> Dict[str, Any]:
        failed_instructions = []

        for idx, inst in enumerate(instructions):
            try:
                self.execute(inst)
            except Exception as e:
                failed_instructions.append({
                    "index": idx,
                    "instruction": inst,
                    "error": str(e)
                })

        is_complete, missing_fields = self.validate_completeness()

        return {
            "success": is_complete and len(failed_instructions) == 0,
            "data": self.data,
            "applied": self.stats["success"],
            "failed": self.stats["failed"],
            "errors": failed_instructions,
            "is_complete": is_complete,
            "missing_fields": missing_fields
        }

    def validate_completeness(self) -> tuple[bool, list[str]]:
        from app.services.ai.core.model_builder import build_model_from_json_schema

        try:
            DynamicModel = build_model_from_json_schema('ValidationModel', self.schema)
            DynamicModel(**self.data)
            return True, []
        except ValidationError as e:
            missing_fields = []
            for error in e.errors():
                if error.get('type') == 'missing':
                    loc = error.get('loc', ())
                    if loc:
                        path = '/' + '/'.join(str(l) for l in loc)
                        missing_fields.append(path)

            return False, missing_fields

    def get_data(self) -> Dict[str, Any]:
        return self.data

    def get_stats(self) -> Dict[str, int]:
        return self.stats.copy()
