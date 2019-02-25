from itertools import cycle, islice
from typing import Any, Callable


def basic(dataset: [Any]) -> Callable[[], Any]:
    iterator = cycle(dataset)

    def get_next():
        return next(iterator)

    return get_next
