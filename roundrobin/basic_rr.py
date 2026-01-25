from itertools import cycle


def basic(dataset):
    dataset = list(dataset)
    if len(dataset) == 0:
        raise ValueError("dataset must be non-empty")
    iterator = cycle(dataset)

    def get_next():
        return next(iterator)

    return get_next
