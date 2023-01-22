# dual

`dual` is a package for dual problem.

## Installation

```
pip install dual
```

## Example

```python
from dual import dual

print(dual("""\
min c^T x
A x >= b
x >= 0
"""))
```

```
max b^T y
A^T y <= c
y >= 0
```
