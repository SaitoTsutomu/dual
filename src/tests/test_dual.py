# flake8: noqa: S101
from textwrap import dedent

from dual import dual


def test_dual():
    model1 = dedent("""\
        min c^T x
        A x >= b
        x >= 0""")
    model2 = dedent("""\
        max b^T y
        A^T y <= c
        y >= 0""")
    assert dual(model1) == model2
    assert dual(model2) == model1
