
from typing import Dict, Callable, List, Optional
from loguru import logger
import inspect

from .types import NodeMetadata


_NODE_REGISTRY: Dict[str, NodeMetadata] = {}


def register_node(cls):
    if not inspect.isclass(cls):
        raise TypeError("@register_node must be used on a class")

    node_type = getattr(cls, "node_type", None)
    if not node_type:
        raise ValueError(f"Node class {cls.__name__} must define 'node_type'")

    metadata = cls.get_metadata()

    _NODE_REGISTRY[node_type] = metadata
    logger.debug(f"[NodeRegister] {node_type} ({metadata.category}) -> {cls.__name__}")
    return cls


def get_registered_nodes() -> Dict[str, Callable]:
    return {type_name: meta.executor for type_name, meta in _NODE_REGISTRY.items()}


def get_node_metadata(node_type: str) -> Optional[NodeMetadata]:
    return _NODE_REGISTRY.get(node_type)


def get_all_node_metadata() -> List[NodeMetadata]:
    return list(_NODE_REGISTRY.values())


def get_node_types() -> List[str]:
    return list(_NODE_REGISTRY.keys())


def get_nodes_by_category(category: str) -> List[NodeMetadata]:
    return [meta for meta in _NODE_REGISTRY.values() if meta.category == category]


class NodeRegistry:


    def has_node(self, node_type: str) -> bool:
        return node_type in _NODE_REGISTRY

    def get(self, node_type: str) -> Optional[Callable]:
        meta = _NODE_REGISTRY.get(node_type)
        return meta.executor if meta else None

    def list_nodes(self) -> List[str]:
        return list(_NODE_REGISTRY.keys())


def discover_workflow_nodes():
    logger.info(f"[NodeDiscovery] Loaded {len(_NODE_REGISTRY)} workflow nodes")

    categories = {}
    for meta in _NODE_REGISTRY.values():
        categories[meta.category] = categories.get(meta.category, 0) + 1

    for cat, count in categories.items():
        logger.debug(f"  - {cat}: {count} nodes")
