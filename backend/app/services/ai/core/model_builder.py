
from typing import Dict, Any, List, Type
from pydantic import create_model, Field as PydanticField, BaseModel
from typing import Any as _Any, Dict as _Dict, List as _List


def json_schema_to_py_type(sch: Dict[str, Any], schema_root: Dict[str, Any] = None) -> Any:
    if not isinstance(sch, dict):
        return _Any

    if '$ref' in sch:
        ref_path = sch['$ref']
        if ref_path.startswith('#/$defs/') and schema_root and '$defs' in schema_root:
            def_name = ref_path.split('/')[-1]
            ref_schema = schema_root['$defs'].get(def_name)
            if ref_schema:
                return build_model_from_json_schema(def_name, ref_schema, schema_root)

        return _Dict[str, _Any]

    t = sch.get('type')

    if t == 'string':
        return str
    if t == 'integer':
        return int
    if t == 'number':
        return float
    if t == 'boolean':
        return bool
    if t == 'array':
        item_sch = sch.get('items') or {}
        return _List[json_schema_to_py_type(item_sch, schema_root)]  # type: ignore[index]
    if t == 'object':
        if 'properties' in sch:
            import hashlib
            schema_str = str(sorted(sch.get('properties', {}).keys()))
            model_hash = hashlib.md5(schema_str.encode()).hexdigest()[:8]
            nested_model_name = f'NestedModel_{model_hash}'
            return build_model_from_json_schema(nested_model_name, sch, schema_root)
        else:
            return _Dict[str, _Any]

    return _Any


def build_model_from_json_schema(model_name: str, schema: Dict[str, Any], root_schema: Dict[str, Any] = None) -> Type[BaseModel]:
    if root_schema is None:
        root_schema = schema

    if '$ref' in schema:
         return json_schema_to_py_type(schema, root_schema)

    props: Dict[str, Any] = (schema or {}).get('properties') or {}
    required: List[str] = list((schema or {}).get('required') or [])
    field_defs: Dict[str, tuple] = {}

    for fname, fsch in props.items():
        anno = json_schema_to_py_type(fsch if isinstance(fsch, dict) else {}, root_schema)

        desc = fsch.get('description') if isinstance(fsch, dict) else None

        is_required = fname in required

        if desc is not None:
            default_val = PydanticField(... if is_required else None, description=desc)
        else:
            default_val = ... if is_required else None

        field_defs[fname] = (anno, default_val)

    return create_model(model_name, **field_defs)

