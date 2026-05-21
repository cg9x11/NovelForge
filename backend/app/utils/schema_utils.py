
from typing import Any, Dict, List
from copy import deepcopy


def filter_schema_for_ai(schema: Dict[str, Any]) -> Dict[str, Any]:
    def prune(node: Any, parent_required: List[str] | None = None) -> Any:
        if isinstance(node, dict):
            if node.get('type') == 'object' and isinstance(node.get('properties'), dict):
                props = node.get('properties') or {}
                required = list(node.get('required') or [])
                new_props: Dict[str, Any] = {}
                for name, sch in props.items():
                    if isinstance(sch, dict) and sch.get('x-ai-exclude') is True:
                        if name in required:
                            required = [r for r in required if r != name]
                        continue
                    new_props[name] = prune(sch)
                node = dict(node)
                node['properties'] = new_props
                if required:
                    node['required'] = required
                elif 'required' in node:
                    node.pop('required', None)
            if node.get('type') == 'array':
                if 'items' in node:
                    node = dict(node)
                    node['items'] = prune(node['items'])
                if 'prefixItems' in node and isinstance(node.get('prefixItems'), list):
                    node = dict(node)
                    node['prefixItems'] = [prune(it) for it in node.get('prefixItems', [])]
            for kw in ('anyOf', 'oneOf', 'allOf'):
                if isinstance(node.get(kw), list):
                    node = dict(node)
                    node[kw] = [prune(it) for it in node.get(kw, [])]
            if isinstance(node.get('$defs'), dict):
                defs = node.get('$defs') or {}
                new_defs: Dict[str, Any] = {}
                for k, v in defs.items():
                    new_defs[k] = prune(v)
                node = dict(node)
                node['$defs'] = new_defs
            if 'x-ai-exclude' in node:
                node = dict(node)
                node.pop('x-ai-exclude', None)
            return node
        elif isinstance(node, list):
            return [prune(it) for it in node]
        return node

    try:
        root = deepcopy(schema) if isinstance(schema, dict) else {}
        return prune(root)
    except Exception:
        return schema
