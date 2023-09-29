[![Build Status](https://travis-ci.org/linnik/roundrobin.svg?branch=master)](https://travis-ci.org/linnik/roundrobin)
[![PyPI install](https://img.shields.io/badge/pip%20install-roundrobin-informational)](https://pypi.org/project/roundrobin/)
![versions](https://img.shields.io/pypi/pyversions/roundrobin.svg)

# roundrobin

This is rather small collection of round robin utilities

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

