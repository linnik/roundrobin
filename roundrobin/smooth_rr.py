def smooth(dataset):
    """
    Smooth weighted round-robin (as seen in Nginx).

    Dataset items: (key, weight)

    For health-check / slow-start behavior, use `smooth_stateful()`.
    """
    dataset = list(dataset)
    if len(dataset) == 0:
        raise ValueError("dataset must be non-empty")
    dataset_length = len(dataset)
    dataset_extra_weights = [ItemWeight(*x) for x in dataset]

    def get_next():
        if dataset_length == 1:
            return dataset[0][0]

        total_weight = 0
        result = None
        for extra in dataset_extra_weights:
            extra.current_weight += extra.effective_weight
            total_weight += extra.effective_weight
            # In this function-based API `effective_weight` is initialized to
            # `weight` and never reduced; see `smooth_stateful()` for health/
            # slow-start behavior that adjusts `effective_weight` between calls.
            # This block is currently unreachable but kept for consistency.
            if extra.effective_weight < extra.weight:  # pragma: no cover
                extra.effective_weight += 1
            if not result or result.current_weight < extra.current_weight:
                result = extra
        if not result:  # this should be unreachable, but check anyway
            raise RuntimeError  # pragma: no cover
        result.current_weight -= total_weight
        return result.key

    return get_next


class ItemWeight:
    __slots__ = ('key', 'weight', 'current_weight', 'effective_weight', 'disabled')

    def __init__(self, key, weight):
        if weight < 0:
            raise ValueError("weights must be non-negative")
        self.key = key
        self.weight = weight
        self.current_weight = 0
        self.effective_weight = weight
        self.disabled = False

    def __repr__(self):
        parts = [
            "key={!r}".format(self.key),
            "weight={!r}".format(self.weight),
            "current_weight={!r}".format(self.current_weight),
            "effective_weight={!r}".format(self.effective_weight),
        ]
        if self.disabled:
            parts.append("disabled={!r}".format(self.disabled))
        return "{}({})".format(self.__class__.__name__, ", ".join(parts))
