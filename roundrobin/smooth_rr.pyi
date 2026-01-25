from typing import Any, Callable, Iterable, Tuple


def smooth(dataset: Iterable[Tuple[Any, int]]) -> Callable[[], Any]:
    def get_next() -> Any: ...


class ItemWeight:
    key: Any
    weight: int
    current_weight: int
    effective_weight: int
