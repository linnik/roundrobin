This is rather small collection of round robin utilites

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

