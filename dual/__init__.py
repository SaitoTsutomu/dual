import re
import sys
from collections import defaultdict
from itertools import chain, count


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
    return "0" if s == "" else s


def trans(s):
    if s in ("I", "-I"):
        return s
    return s[:-2] if s.endswith("^T") else s + "^T"


def dualvar(ss):
    st = set(re.sub(r"[+-><=^]", " ", " ".join(ss)).split())
    for v in chain(["x", "y", "z", "w"], ("v%d" % j for j in count())):
        if v not in st:
            yield v


def split_term(s, ismat=False):
    dc = defaultdict(list)
    ss = re.sub(r"^\+", "", re.sub(r"-\s*", "+-", s.strip())).split("+")
    for t in ss:
        tt = t.split()
        if not (0 < len(tt) < 3):
            raise ValueError("Format error [%s]" % s)
        c, v = (["I" if ismat else "e^T"] + tt)[-2:]
        if v[0] == "-":
            c, v = minus(c), minus(v)
        if c[0] != "-":
            c = "+" + c
        dc[v].append(c)
    return dc


def dual(mdl):
    ss = []
    for s in mdl.strip().split("\n"):
        if s and not s.startswith("#"):
            ss.append(s.split("#")[0].strip())
    if not ss:
        raise ValueError("Set mathematical optimization model")
    if ss[0][:3] not in ("min", "max"):
        raise ValueError('Must start "min" or "max" [%s]' % ss[0])
    is_min = ss[0][:3] == "min"
    ds = split_term(ss[0][3:])
    dc = defaultdict(lambda: "0^T")
    for v, uu in ds.items():
        if len(uu) != 1:
            raise ValueError("Format error [%s]" % ss[0])
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
    for s, dv in zip(cc, dualvar(ss)):
        m = re.fullmatch(r"([^<>=]+)(>|<|)=\s*(\S+)", s)
        if not m:
            raise ValueError("Format error [%s]" % s)
        t, f, b = m.groups()
        if not b.startswith(("+", "-")):
            b = "+" + b
        tt = split_term(t, True)
        if f:
            if is_min != (f == ">"):
                tt = {v: [minus(u) for u in uu] for v, uu in tt.items()}
                b = minus(b)
            dd.append("%s >= 0" % dv)
        if b not in ("+0", "-0"):
            db.append("%s %s" % (trans(b), dv))
        for v, uu in tt.items():
            da[v].append(addplus(expr(["%s %s" % (trans(u), dv) for u in uu])))
    dr = [("max " if is_min else "min ") + expr(db)]
    for v in sorted(da.keys()):
        dr.append("%s %s %s" % (expr(da[v]), di[v], expr([trans(dc[v])])))
    return "\n".join(dr + dd)


# dualマジックコマンド登録
try:
    import IPython.core.getipython

    def dual_impl(_, s):
        print(dual(s))

    ip = IPython.core.getipython.get_ipython()
    ip.register_magic_function(dual_impl, magic_kind="cell", magic_name="dual")
except (ModuleNotFoundError, AttributeError):
    pass


def main():
    s = sys.stdin.read()
    print(dual(s))
