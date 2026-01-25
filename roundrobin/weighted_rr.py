try:
    from math import gcd
except ImportError:
    from fractions import gcd


# python2 workaround for python3 nonlocal keyword
class Store:
    __slots__ = ('index', 'weight')

    def __init__(self, index, weight):
        self.index = index
        self.weight = weight


def weighted(dataset):
    """
    Weighted round-robin (as seen in LVS).

    Falls back to `basic()` round-robin if all weights in the dataset are
    equal (including the case where all weights are 0).
    """
    dataset = list(dataset)
    if len(dataset) == 0:
        raise ValueError("dataset must be non-empty")
    current = Store(index=-1, weight=0)

    dataset_length = len(dataset)
    dataset_max_weight = 0
    dataset_gcd_weight = 0

    for _, weight in dataset:
        if weight < 0:
            raise ValueError("weights must be non-negative")
        if dataset_max_weight < weight:
            dataset_max_weight = weight
        dataset_gcd_weight = gcd(dataset_gcd_weight, weight)

    if all(weight == dataset[0][1] for _, weight in dataset):
        from roundrobin.basic_rr import basic
        return basic([key for key, _ in dataset])

    def get_next():
        while True:
            current.index = (current.index + 1) % dataset_length
            if current.index == 0:
                current.weight = current.weight - dataset_gcd_weight
                if current.weight <= 0:
                    current.weight = dataset_max_weight
                    # When all weights are 0, weighted() returns basic() above.
                    # This is retained as an additional guard.
                    if current.weight == 0:  # pragma: no cover
                        return None  # pragma: no cover
            if dataset[current.index][1] >= current.weight:
                return dataset[current.index][0]

    return get_next
