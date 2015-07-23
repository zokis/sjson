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


Errors:
```text
'[#'         -> Expected object, array or value
'[1, , '     -> Expected object, array or value
'[1, , ,]'   -> Expected object, array or value
'[12,]'      -> Expected object, array or value
'[123'       -> Failed to decode an array
'[123, ]'    -> Expected object, array or value
'[@]'        -> Expected object, array or value
'["a","b"'   -> Failed to decode an array
'["marcelo]' -> JSON data truncated
'[nulo]'     -> Unexpected character found when decoding 'null'
'[trur]'     -> Unexpected character found when decoding 'true'
'[false'     -> Failed to decode an array
'[falze]'    -> Unexpected character found when decoding 'false'
'zokis'      -> Expected object, array or value
'{"123"'     -> Expecting ':' delimiter
'{"123":'    -> Expected object, array or value
'{"123"}'    -> Expecting ':' delimiter
'{"a:"b"}'   -> Expecting ':' delimiter
'{'          -> JSON data truncated
'{,}'        -> JSON data truncated
'{123: 456}' -> JSON data truncated
```
