# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.1.0] - 2026-01-25

### Added
- `roundrobin.smooth_stateful()` to support slow-start / health-check behavior by adjusting `effective_weight` between calls.

### Breaking
- All round-robin algorithms now raise `ValueError` when given an empty dataset.
- `roundrobin.weighted()` falls back to `basic()` when all weights are equal (including all zeros).
- `roundrobin.weighted()` and `roundrobin.smooth()` now reject negative weights.


### Migration Guide

Empty datasets now raise `ValueError` instead of returning a selector that yields `None` or raises later.
  This affects `basic()`, `smooth()`, `smooth_stateful()`, and `weighted()`.

```python
# Before: returned a selector that could return None (or error later)
rr = roundrobin.weighted([])
print(rr())  # None

# Now: empty datasets are rejected up front
roundrobin.weighted([])
# ValueError: dataset must be non-empty
```

Negative weights now raise `ValueError` in `smooth()`, `smooth_stateful()`, and `weighted()`.

```python
# Before: accepted negative weights (behavior undefined)
rr = roundrobin.smooth([("A", -1), ("B", 1)])

# Now: explicit error
roundrobin.smooth([("A", -1), ("B", 1)])
# ValueError: weights must be non-negative
```

`weighted()` now falls back to `basic()` when all weights are equal (including all zeros), so it will
  cycle keys instead of returning `None` for all-zero weights.

```python
# Before: all-zero weights yielded None
rr = roundrobin.weighted([("A", 0), ("B", 0)])
print(rr())  # None

# Now: cycles like basic()
rr = roundrobin.weighted([("A", 0), ("B", 0)])
[rr() for _ in range(4)]  # ['A', 'B', 'A', 'B']
```
