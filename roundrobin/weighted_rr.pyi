from typing import Any, Callable, Tuple


def weighted(dataset: [Tuple[Any, int]]) -> Callable[[], Any]:
    def get_next() -> Any: ...
