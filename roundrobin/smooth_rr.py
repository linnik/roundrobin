from typing import Callable, Optional, Tuple


def smooth(dataset: [Tuple[str, int]]) -> Callable[[], Optional[str]]:
    dataset_length = len(dataset)
    dataset_extra_weights = [ItemWeight(*x) for x in dataset]

    def get_next() -> Optional[str]:
        if dataset_length == 0:
            return None
        if dataset_length == 1:
            return dataset[0][0]

        total_weight = 0
        result = None
        for extra in dataset_extra_weights:
            extra.current_weight += extra.effective_weight
            total_weight += extra.effective_weight
            if extra.effective_weight < extra.weight:
                extra.effective_weight += 1
            if not result or result.current_weight < extra.current_weight:
                result = extra
        if result:
            result.current_weight -= total_weight
            return result.key
        return None

    return get_next


class ItemWeight:
    key: str
    weight: int
    current_weight: int
    effective_weight: int

    def __init__(self, key, weight):
        self.key = key
        self.weight = weight
        self.current_weight = 0
        self.effective_weight = weight
