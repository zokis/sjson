# sjson
An implementation of a Python JSON parser for educational purposes, implemented in Pure python and Cython


```python
>>> import sjson
>>> a = {
...     'a': 1L,
...     'b': {
...         'a': [
...             1L,
...             2,
...             3,
...             4,
...             5L,
...             'a'
...         ],
...         'b': {
...             'a': [],
...             '1': 'a'
...         }
...     },
...     'c': [1e33, -.01e44]
... }
>>> sjson.loads(sjson.dumps(a)) == a
True
```
