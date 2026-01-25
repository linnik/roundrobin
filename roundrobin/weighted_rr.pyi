from typing import Any, Callable, Iterable, Tuple


def weighted(dataset: Iterable[Tuple[Any, int]]) -> Callable[[], Any]:
    def get_next() -> Any: ...
