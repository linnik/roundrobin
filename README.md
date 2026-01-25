[![Tests](https://github.com/linnik/roundrobin/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/linnik/roundrobin/actions/workflows/tests.yml)
[![Coverage](https://codecov.io/gh/linnik/roundrobin/branch/master/graph/badge.svg)](https://codecov.io/gh/linnik/roundrobin)
[![PyPI install](https://img.shields.io/badge/pip%20install-roundrobin-informational)](https://pypi.org/project/roundrobin/)
![versions](https://img.shields.io/pypi/pyversions/roundrobin.svg)

# roundrobin

A small collection of round-robin selectors:

- `basic()` - plain round-robin (A, B, C, A, B, C, ...)
- `weighted()` - weighted round-robin (classic LVS-style)
- `smooth()` - smooth weighted round-robin (Nginx-style; avoids long clumps)
- `smooth_stateful()` - smooth weighted RR with runtime controls (health checks / slow-start)

## Install

```bash
pip install roundrobin
```

## Quickstart

```python
>>> import roundrobin
>>> get_roundrobin = roundrobin.basic(["A", "B", "C"])
>>> ''.join([get_roundrobin() for _ in range(7)])
'ABCABCA'
>>> # weighted round-robin balancing algorithm as seen in LVS
>>> get_weighted = roundrobin.weighted([("A", 5), ("B", 1), ("C", 1)])
>>> ''.join([get_weighted() for _ in range(7)])
'AAAAABC'
>>> # smooth weighted round-robin balancing algorithm as seen in Nginx
>>> get_weighted_smooth = roundrobin.smooth([("A", 5), ("B", 1), ("C", 1)])
>>> ''.join([get_weighted_smooth() for _ in range(7)])
'AABACAA'
```

## Stateful smooth weighted round-robin

Use `smooth_stateful()` when you want smooth weighted balancing but also need to change weights at runtime
(health checks, slow-start, draining, etc.). It returns a selector object that you call repeatedly to
pick the next key.

The key idea is that you can temporarily reduce a key's influence without changing its long-term configured
capacity, and the selector will smoothly converge to the new distribution over subsequent calls.

What you do:

- call `rr()` to get the next key
- use `rr.set(key, weight=..., effective=...)` to adjust weights
- use `rr.disable(key)` to take items out of rotation
- use `rr.enable(key, effective_weight=0)` to re-enable (0 for slow-start; omit for full weight)
- use `rr.reset(key)` to restore `effective_weight` to full (the current configured `weight`)

Terminology:

- **weight** - the configured (base) weight representing target capacity
- **effective_weight** - the weight used for selection right now (clamped to `[0, weight]`)

Behavior:

- Lowering `effective_weight` (explicitly via `set(..., effective=...)` or implicitly by lowering `weight`)
  takes effect immediately; the selector also adjusts its accumulated state so a previously heavy key
  doesn't keep dominating after being down-weighted.
- If `effective_weight < weight`, it auto-ramps by +1 after every `rr()` call until it reaches `weight`
  again (unless the item is disabled).

Statefulness note: the selector keeps per-item state, so sequences after changes depend on prior calls.
These methods affect future picks; they do not "restart" the schedule. If you want a clean slate after
changes, create a new selector instance. The examples below create a new selector for each scenario so
outputs are easy to reason about.

```python
>>> take = lambda source, n: ''.join([source() for _ in range(n)])
>>> rr = roundrobin.smooth_stateful([("A", 5), ("B", 1), ("C", 1)])
>>> take(rr, 14)
'AABACAAAABACAA'

>>> # set() changes weights for future picks
>>> rr = roundrobin.smooth_stateful([("A", 5), ("B", 1), ("C", 1)])
>>> rr.set("A", weight=2)
>>> take(rr, 14)
'ABCAABCAABCAAB'

>>> # disable() removes an item from rotation
>>> rr = roundrobin.smooth_stateful([("A", 5), ("B", 1), ("C", 1)])
>>> rr.disable("A")
>>> take(rr, 14)
'BCBCBCBCBCBCBC'

>>> # enable() can bring an item back with slow-start (start at 0 and ramp up)
>>> rr = roundrobin.smooth_stateful([("A", 5), ("B", 1), ("C", 1)])
>>> rr.disable("A")
>>> rr.enable("A", effective_weight=0)
>>> take(rr, 14)
'BCAABAACAAABAA'

>>> # initial_effective supports None | int | dict | callable
>>> rr = roundrobin.smooth_stateful([("A", 3), ("B", 1)], initial_effective=0)
>>> take(rr, 14)
'AABAAABAAABAAA'
>>> rr = roundrobin.smooth_stateful([("A", 3), ("B", 1)], initial_effective={"B": 0})
>>> take(rr, 14)
'AAABAAABAAABAA'
>>> rr = roundrobin.smooth_stateful(
...     [("A", 5), ("B", 1), ("C", 1)],
...     initial_effective=lambda key, weight: 0 if key == "A" else weight,
... )
>>> take(rr, 14)
'BCAABAACAAABAA'

>>> # reset() restores effective_weight back to the current configured weight
>>> rr = roundrobin.smooth_stateful([("A", 5), ("B", 1)])
>>> item_a = rr.items[0]  # "A"
>>> rr.set("A", effective=0)
>>> item_a.effective_weight
0
>>> rr.reset("A")
>>> item_a.effective_weight
5

>>> # effective_weight is clamped to [0, weight] and auto-ramps by +1 per call
>>> rr = roundrobin.smooth_stateful([("A", 3), ("B", 1)])
>>> rr.set("A", effective=0)
>>> take(rr, 14)
'BABAAABAAABAAA'
>>> [item.effective_weight for item in rr.items]
[3, 1]

>>> # methods raise KeyError when no items match key
>>> rr = roundrobin.smooth_stateful([("A", 1), ("B", 1)])
>>> rr.set("missing", weight=1)
Traceback (most recent call last):
...
KeyError: 'missing'

>>> # keys are matched by equality, so unhashable keys work
>>> a = {"name": "A"}
>>> b = {"name": "B"}
>>> rr = roundrobin.smooth_stateful([(a, 1), (b, 1)])
>>> rr.disable({"name": "A"})
>>> rr() is b
True

>>> # dict-based initial_effective requires hashable keys
>>> roundrobin.smooth_stateful([([1, 2], 1)], initial_effective={[1, 2]: 0})
Traceback (most recent call last):
...
TypeError: ...unhashable type: 'list'...
```

## Gotchas

```python
>>> # empty datasets are rejected
>>> roundrobin.basic([])
Traceback (most recent call last):
...
ValueError: dataset must be non-empty

>>> # weights must be non-negative integers
>>> roundrobin.smooth([("A", -1)])
Traceback (most recent call last):
...
ValueError: weights must be non-negative

>>> # weighted() falls back to basic RR when all weights are equal (including 0)
>>> rr = roundrobin.weighted([("A", 0), ("B", 0)])
>>> take(rr, 4)
'ABAB'

>>> # if total effective weight is 0 (e.g. initial_effective=0),
>>> # smooth() / smooth_stateful() fall back to the first item to avoid returning None
>>> rr = roundrobin.smooth_stateful([("A", 1), ("B", 1)], initial_effective=0)
>>> take(rr, 6)
'AABABA'

>>> # smooth_stateful() returns None only when there are no candidates (all disabled)
>>> rr = roundrobin.smooth_stateful([("A", 1), ("B", 1)])
>>> rr.disable("A")
>>> rr.disable("B")
>>> print(rr())
None

>>> # effective=0 is temporary unless the item is disabled (it auto-ramps by +1 per call)
>>> rr = roundrobin.smooth_stateful([("A", 3), ("B", 1)])
>>> rr.set("A", effective=0)
>>> for _ in range(3):
...     _ = rr()
>>> [item.effective_weight for item in rr.items]
[3, 1]
>>> rr.disable("A")
>>> for _ in range(3):
...     _ = rr()
>>> [item.effective_weight for item in rr.items]
[0, 1]

>>> # setting weight=0 removes an item from selection (without using disable())
>>> rr = roundrobin.smooth_stateful([("A", 1), ("B", 1)])
>>> rr.set("A", weight=0)
>>> take(rr, 4)
'BBBB'
```

## Thread Safety

```python
>>> # selectors are not thread-safe; wrap calls with a lock when shared
>>> import threading
>>> rr = roundrobin.smooth_stateful([("A", 2), ("B", 1)])
>>> lock = threading.Lock()
>>> def safe_next():
...     with lock:
...         return rr()
>>> safe_next()
'A'

>>> # use per-thread instances
>>> import threading
>>> def worker():
...     rr = roundrobin.basic(["A", "B"])
...     return rr()
>>> t = threading.Thread(target=worker)
>>> t.start()
>>> t.join()
```

## License

MIT. See `LICENSE`.
