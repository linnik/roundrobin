from typing import Any, Callable, Tuple


def smooth(dataset: [Tuple[Any, int]]) -> Callable[[], Any]:
    def get_next() -> Any: ...


class ItemWeight:
    key: Any
    weight: int
    current_weight: int
    effective_weight: int
