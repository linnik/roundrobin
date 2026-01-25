from roundrobin.smooth_rr import ItemWeight


def smooth_stateful(dataset, initial_effective=None):
    """
    Stateful smooth weighted round-robin.

    Unlike `smooth()`, this returns an object that allows adjusting
    per-item `effective_weight` between calls to implement health checks
    and slow-start behavior.

    `initial_effective` can be:
      - None: start at full weight
      - int: start all items at this effective weight (clamped)
      - dict: {key: effective_weight} (missing keys start at full weight)
      - callable: f(key, weight) -> effective_weight
    """
    return SmoothRR(dataset, initial_effective=initial_effective)


class SmoothRR(object):
    """
    Stateful smooth weighted round-robin selector.

    Call the instance to get the next key:
        rr()

    You can adjust per-key `effective_weight` between calls to implement:
      - health-check / load shedding (reduce effective weight temporarily)
      - slow-start (start low and let it ramp up)

    If an item's `effective_weight` is below `weight`, it increases by +1 on
    every call to the instance (regardless of which item is selected) until
    it reaches `weight`, unless the item is disabled.
    """

    def __init__(self, dataset, initial_effective=None):
        dataset = list(dataset)
        if len(dataset) == 0:
            raise ValueError("dataset must be non-empty")

        self.items = [ItemWeight(*x) for x in dataset]

        if initial_effective is None:
            return

        if callable(initial_effective):
            for item in self.items:
                self._set_item_effective(item, initial_effective(item.key, item.weight))
            return

        if isinstance(initial_effective, dict):
            for key, effective_weight in initial_effective.items():
                for item in self.items:
                    if item.key == key:
                        self._set_item_effective(item, effective_weight)
            return

        for item in self.items:
            self._set_item_effective(item, initial_effective)

    def set(self, key, weight=None, effective=None):
        """
        Set `weight` and/or `effective` weight for items matching `key`.

        - `weight`: sets the configured (base) weight. Negative raises ValueError.
        - `effective`: sets effective_weight (clamped to [0, weight]).
        - If lowering effective (explicitly or via weight clamp),
          `current_weight` is scaled down immediately.
        """
        items = [item for item in self.items if item.key == key]
        if not items:
            raise KeyError(key)
        if weight is not None and weight < 0:
            raise ValueError("weights must be non-negative")
        for item in items:
            prev_effective = item.effective_weight
            if weight is not None:
                item.weight = weight
                if item.effective_weight > item.weight:
                    item.effective_weight = item.weight
            if effective is not None:
                self._set_item_effective(item, effective)
            if prev_effective > 0 and item.effective_weight < prev_effective:
                # Keep accumulated current_weight proportional to the new effective weight.
                item.current_weight = (item.current_weight * item.effective_weight) // prev_effective

    def reset(self, key):
        """Reset `effective_weight` for `key` back to its configured `weight`."""
        items = [item for item in self.items if item.key == key]
        if not items:
            raise KeyError(key)
        for item in items:
            self._set_item_effective(item, None)

    def disable(self, key):
        """Convenience: remove items from selection until enable()."""
        items = [item for item in self.items if item.key == key]
        if not items:
            raise KeyError(key)
        for item in items:
            prev_effective = item.effective_weight
            self._set_item_effective(item, 0)
            if prev_effective > 0 and item.effective_weight < prev_effective:
                item.current_weight = (item.current_weight * item.effective_weight) // prev_effective
            item.disabled = True

    def enable(self, key, effective_weight=None):
        """Re-enable items and set effective weight (default: full weight)."""
        items = [item for item in self.items if item.key == key]
        if not items:
            raise KeyError(key)
        for item in items:
            item.disabled = False
            prev_effective = item.effective_weight
            self._set_item_effective(item, effective_weight)
            if prev_effective > 0 and item.effective_weight < prev_effective:
                item.current_weight = (item.current_weight * item.effective_weight) // prev_effective

    def _set_item_effective(self, item, effective_weight):
        if effective_weight is None:
            effective_weight = item.weight
        if effective_weight < 0:
            effective_weight = 0
        if effective_weight > item.weight:
            effective_weight = item.weight
        item.effective_weight = effective_weight

    def __call__(self):
        # Smooth weighted round-robin (Nginx-style):
        # Each call adds each item's effective_weight to its current_weight.
        # The item with the highest current_weight wins this round.
        # After selection, subtract total_weight from the winner's current_weight
        # to "pay back" its lead, which spreads picks smoothly over time.
        # effective_weight can be temporarily lower than weight; when it is,
        # it auto-ramps by +1 per call until it reaches weight again.
        total_weight = 0
        best_any = None
        best_active = None
        for item in self.items:
            if item.disabled:
                continue
            effective = item.effective_weight
            # Accumulate weight for this round.
            item.current_weight += effective
            total_weight += effective
            # Slow-start / recovery: ramp effective_weight up toward weight.
            if item.effective_weight < item.weight:
                item.effective_weight += 1

            # Track the highest current_weight across all items,
            # and across active items (effective_weight > 0).
            if not best_any or best_any.current_weight < item.current_weight:
                best_any = item
            if effective > 0 and (not best_active or best_active.current_weight < item.current_weight):
                best_active = item

        # If total_weight is 0 (all items disabled or all weights are 0),
        # return the first candidate to avoid returning None.
        result = best_active if total_weight > 0 else best_any
        if not result:
            return None
        # Reduce the winner by the total to balance future rounds.
        result.current_weight -= total_weight
        return result.key
