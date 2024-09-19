import re
import sys
import typing
from collections import defaultdict
from itertools import chain, count

NUM_ONLY_VAR: typing.Final[int] = 1  # 変数のみの個数
NUM_WITH_COEF: typing.Final[int] = 2  # 係数と変数の個数


def addplus(s):
    return s if s.startswith(("+", "-")) else "+" + s


def delplus(s):
    return s[1:] if s.startswith("+") else s


def minus(s):
    return s[1:] if s.startswith("-") else "-" + delplus(s)


def expr(lst):
    s = re.sub("([+-])", "\\1 ", " ".join(lst)).strip("+ ")
    if len(lst) == 1 and s.startswith("- "):
        s = "-" + s[2:]
    return s or "0"


def trans(s):
    if s in {"I", "-I"}:
        return s
    return s[:-2] if s.endswith("^T") else s + "^T"


def dualvar(ss):
    st = set(re.sub(r"[+-><=^]", " ", " ".join(ss)).split())
    for v in chain(["x", "y", "z", "w"], (f"v{j}" for j in count())):
        if v not in st:
            yield v


def split_term(s, *, ismat=False):
    dc = defaultdict(list)
    ss = re.sub(r"^\+", "", re.sub(r"-\s*", "+-", s.strip())).split("+")
    for t in ss:
        tt = t.split()
        if not (NUM_ONLY_VAR <= len(tt) <= NUM_WITH_COEF):
            msg = f"Format error [{s}]"
            raise ValueError(msg)
        c, v = (["I" if ismat else "e^T", *tt])[-2:]
        if v[0] == "-":
            c, v = minus(c), minus(v)
        if c[0] != "-":
            c = "+" + c
        dc[v].append(c)
    return dc


def dual(mdl):  # noqa: C901, PLR0912, PLR0914
    ss = [s.split("#")[0].strip() for s in mdl.strip().split("\n") if s and not s.startswith("#")]
    if not ss:
        msg = "Set mathematical optimization model"
        raise ValueError(msg)
    if ss[0][:3] not in {"min", "max"}:
        msg = f'Must start "min" or "max" [{ss[0]}]'
        raise ValueError(msg)
    is_min = ss[0][:3] == "min"
    ds = split_term(ss[0][3:])
    dc = defaultdict(lambda: "0^T")
    for v, uu in ds.items():
        if len(uu) != 1:
            raise ValueError(f"Format error [{ss[0]}]" % ss[0])
        dc[v] = uu[0]
    di = defaultdict(lambda: "=")
    cc = []
    for s in ss[1:]:
        m = re.fullmatch(r"(\S+)\s*([><])=\s*0", s)
        if m:
            di[m.group(1)] = "<=" if is_min == (m.group(2) == ">") else ">="
        else:
            cc.append(s)
    db, dd, da = [], [], defaultdict(list)
    for s, dv in zip(cc, dualvar(ss), strict=False):
        m = re.fullmatch(r"([^<>=]+)(>|<|)=\s*(\S+)", s)
        if not m:
            msg = f"Format error [{s}]"
            raise ValueError(msg)
        t, f, b = m.groups()
        if not b.startswith(("+", "-")):
            b = "+" + b
        tt = split_term(t, ismat=True)
        if f:
            if is_min != (f == ">"):
                tt = {v: [minus(u) for u in uu] for v, uu in tt.items()}
                b = minus(b)
            dd.append(f"{dv} >= 0")
        if b not in {"+0", "-0"}:
            db.append(f"{trans(b)} {dv}")
        for v, uu in tt.items():
            da[v].append(addplus(expr([f"{trans(u)} {dv}" for u in uu])))
    dr = [("max " if is_min else "min ") + expr(db)] + [
        f"{expr(da[v])} {di[v]} {expr([trans(dc[v])])}" for v in sorted(da.keys())
    ]
    return "\n".join(dr + dd)


def main():
    s = sys.stdin.read()
    print(dual(s))


# dualマジックコマンド登録
try:
    from IPython.core.magic import register_cell_magic

    @register_cell_magic("dual")
    def _dual(_, s):
        print(dual(s))
except (ImportError, NameError, AttributeError):
    pass
