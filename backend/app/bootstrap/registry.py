
from typing import Callable, List, Tuple
from sqlmodel import Session
from loguru import logger


_INITIALIZERS: List[Tuple[int, str, Callable]] = []


def initializer(name: str, order: int = 100):
    def decorator(func: Callable):
        _INITIALIZERS.append((order, name, func))
        return func
    return decorator


def get_registered_initializers() -> List[Tuple[int, str, Callable]]:
    return sorted(_INITIALIZERS, key=lambda x: x[0])


def discover_initializers():




    pass
pass
def run_initializers(session: Session):
    initializers = get_registered_initializers()

    if not initializers:
        return


    for order, name, func in initializers:
        try:
            func(session)
        except Exception as e:
            raise


def discover_and_run_initializers(session: Session):
    discover_initializers()
    run_initializers(session)
