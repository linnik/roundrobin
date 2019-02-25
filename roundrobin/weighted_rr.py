import math
from typing import Callable, Optional, Tuple


def weighted(dataset: [Tuple[str, int]]) -> Callable[[], Optional[str]]:
    current_index = -1
    current_weight = 0
    dataset_length = len(dataset)
    dataset_max_weight = 0
    dataset_gcd_weight = 0

    for _, weight in dataset:
        if dataset_max_weight < weight:
            dataset_max_weight = weight
        dataset_gcd_weight = math.gcd(dataset_gcd_weight, weight)

    def get_next() -> Optional[str]:
        nonlocal current_index
        nonlocal current_weight
        while True:
            current_index = (current_index + 1) % dataset_length
            if current_index == 0:
                current_weight = current_weight - dataset_gcd_weight
                if current_weight <= 0:
                    current_weight = dataset_max_weight
                    if current_weight == 0:
                        return None
            if dataset[current_index][1] >= current_weight:
                return dataset[current_index][0]

    return get_next
