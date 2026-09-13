"""
Big-M Simplex Method
====================
Solves a classic mixed-constraint Linear Programming Problem (LPP)
by converting it to standard form (slack / surplus / artificial variables)
and applying the Big-M simplex algorithm.

Textbook problem (Taha / Winston):
    Minimize  Z = 4x1 + x2
    subject to
        3x1 +  x2  =  3
        4x1 + 3x2 >=  6
         x1 + 2x2 <=  4
        x1, x2    >=  0
"""

from fractions import Fraction
from typing import List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Arithmetic: every tableau entry is  (constant) + (coeff) * M
# ---------------------------------------------------------------------------
M_SYMBOL = "M"
Value = Tuple[Fraction, Fraction]  # (const, m_coeff)  =>  const + m_coeff * M


def V(const=0, m=0) -> Value:
    return (Fraction(const), Fraction(m))


def add(a: Value, b: Value) -> Value:
    return (a[0] + b[0], a[1] + b[1])


def sub(a: Value, b: Value) -> Value:
    return (a[0] - b[0], a[1] - b[1])


def mul(a: Value, k: Fraction) -> Value:
    return (a[0] * k, a[1] * k)


def fmt(v: Value) -> str:
    c, m = v
    if m == 0:
        return _frac(c)
    if c == 0:
        if m == 1:
            return M_SYMBOL
        if m == -1:
            return f"-{M_SYMBOL}"
        return f"{_frac(m)}{M_SYMBOL}"
    m_part = M_SYMBOL if m == 1 else (f"-{M_SYMBOL}" if m == -1 else f"{_frac(abs(m))}{M_SYMBOL}")
    if m > 0:
        return f"{_frac(c)}+{m_part}"
    return f"{_frac(c)}-{m_part}"


def _frac(x: Fraction) -> str:
    if x.denominator == 1:
        return str(x.numerator)
    return f"{x.numerator}/{x.denominator}"


def is_neg(v: Value) -> bool:
    """True iff v is strictly negative for a sufficiently large M > 0."""
    c, m = v
    if m < 0:
        return True
    if m > 0:
        return False
    return c < 0


def cmp_more_neg(a: Value, b: Value) -> bool:
    """True iff a < b for large M (used to pick the most negative reduced cost)."""
    dc, dm = sub(a, b)
    if dm != 0:
        return dm < 0
    return dc < 0


# ---------------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------------
def _hline(widths: Sequence[int], left="+", mid="+", right="+") -> str:
    return left + mid.join("-" * (w + 2) for w in widths) + right


def _row(cells: Sequence[str], widths: Sequence[int]) -> str:
    return "|" + "|".join(f" {c:^{w}} " for c, w in zip(cells, widths)) + "|"


def print_table(headers: Sequence[str], rows: Sequence[Sequence[str]], title: str = "") -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    if title:
        print(f"\n{title}")
    print(_hline(widths))
    print(_row(headers, widths))
    print(_hline(widths))
    for row in rows:
        print(_row([str(c) for c in row], widths))
    print(_hline(widths))


# ---------------------------------------------------------------------------
# Big-M Simplex solver
# ---------------------------------------------------------------------------
class BigMSimplex:
    """
    Tableau Big-M simplex.

    constraints: list of (coeffs, sense, rhs)
        sense in {'<=', '>=', '='}
    sense_obj: 'min' or 'max'
    """

    def __init__(
        self,
        c: Sequence[float],
        constraints: Sequence[Tuple[Sequence[float], str, float]],
        sense: str = "min",
        var_names: Optional[Sequence[str]] = None,
    ):
        self.orig_c = [Fraction(x) for x in c]
        self.n_orig = len(c)
        self.sense = sense.lower()
        self.var_names = list(var_names) if var_names else [f"x{i+1}" for i in range(self.n_orig)]
        self.constraints = [
            ([Fraction(a) for a in coeffs], s, Fraction(rhs)) for coeffs, s, rhs in constraints
        ]

        self.col_names: List[str] = []
        self.A: List[List[Value]] = []  # constraint rows (no z-row)
        self.b: List[Value] = []
        self.c_row: List[Value] = []  # original objective coefficients (cj)
        self.basis: List[int] = []
        self.row_names: List[str] = []
        self.artificial_idx: List[int] = []
        self.z0: Value = V(0)

    # ----- formulation -----------------------------------------------------
    def to_standard_form(self) -> None:
        n = self.n_orig
        slack_k = surplus_k = art_k = 0

        # Count extra variables so names / columns are stable.
        extras: List[Tuple[str, int, str]] = []  # (kind, constraint_i, name)
        for i, (_, sense, _) in enumerate(self.constraints):
            if sense == "<=":
                slack_k += 1
                extras.append(("slack", i, f"s{slack_k}"))
            elif sense == ">=":
                surplus_k += 1
                art_k += 1
                extras.append(("surplus", i, f"p{surplus_k}"))
                extras.append(("art", i, f"a{art_k}"))
            elif sense == "=":
                art_k += 1
                extras.append(("art", i, f"a{art_k}"))
            else:
                raise ValueError(f"Unknown sense {sense}")

        self.col_names = list(self.var_names) + [name for _, _, name in extras]
        n_cols = len(self.col_names)

        # Original cj (decision vars). Slack/surplus get 0.
        # Artificials:  +M  if minimize,  -M  if maximize.
        self.c_row = [V(0) for _ in range(n_cols)]
        for j in range(n):
            self.c_row[j] = V(self.orig_c[j], 0)
        extra_pos = n
        for kind, _, name in extras:
            if kind == "art":
                m_pen = Fraction(1) if self.sense == "min" else Fraction(-1)
                self.c_row[extra_pos] = V(0, m_pen)
                self.artificial_idx.append(extra_pos)
            extra_pos += 1

        # Build constraint matrix
        extra_pos = n
        extra_iter = iter(extras)
        self.A = []
        self.b = []
        self.basis = []
        self.row_names = []

        for i, (coeffs, sense, rhs) in enumerate(self.constraints):
            if rhs < 0:
                coeffs = [-a for a in coeffs]
                rhs = -rhs
                sense = {">=": "<=", "<=": ">=", "=": "="}[sense]

            row = [V(0) for _ in range(n_cols)]
            for j in range(n):
                row[j] = V(coeffs[j])

            if sense == "<=":
                kind, _, name = next(extra_iter)
                assert kind == "slack"
                row[extra_pos] = V(1)
                self.basis.append(extra_pos)
                self.row_names.append(name)
                extra_pos += 1
            elif sense == ">=":
                kind, _, name = next(extra_iter)
                assert kind == "surplus"
                row[extra_pos] = V(-1)
                extra_pos += 1
                kind, _, name = next(extra_iter)
                assert kind == "art"
                row[extra_pos] = V(1)
                self.basis.append(extra_pos)
                self.row_names.append(name)
                extra_pos += 1
            else:  # "="
                kind, _, name = next(extra_iter)
                assert kind == "art"
                row[extra_pos] = V(1)
                self.basis.append(extra_pos)
                self.row_names.append(name)
                extra_pos += 1

            self.A.append(row)
            self.b.append(V(rhs))

        self._recompute_cj_zj()

    def _recompute_cj_zj(self) -> None:
        n_cols = len(self.col_names)
        zj = [V(0) for _ in range(n_cols)]
        z_val = V(0)
        for i, bidx in enumerate(self.basis):
            cb = self.c_row[bidx]
            for j in range(n_cols):
                zj[j] = add(zj[j], _mul_val(cb, self.A[i][j]))
            z_val = add(z_val, _mul_val(cb, self.b[i]))
        self.cj_zj = [sub(self.c_row[j], zj[j]) for j in range(n_cols)]
        self.z0 = z_val

    # ----- tableau I/O -----------------------------------------------------
    def print_formulation(self) -> None:
        obj = " + ".join(
            f"{_frac(self.orig_c[j])}{self.var_names[j]}" if self.orig_c[j] != 1
            else self.var_names[j]
            for j in range(self.n_orig)
        )
        print("=" * 72)
        print("ORIGINAL LINEAR PROGRAMMING PROBLEM")
        print("=" * 72)
        print(f"    {self.sense.upper()}IMIZE  Z = {obj}")
        print("    subject to")
        for coeffs, sense, rhs in self.constraints:
            terms = []
            for j, a in enumerate(coeffs):
                if a == 0:
                    continue
                terms.append(f"{_frac(a)}{self.var_names[j]}" if a != 1 else self.var_names[j])
            print(f"        {' + '.join(terms)}  {sense}  {_frac(rhs)}")
        print("        " + ", ".join(self.var_names) + "  >=  0")

    def print_standard_form(self) -> None:
        print("\n" + "=" * 72)
        print("STANDARD FORM  (slack / surplus / artificial variables)")
        print("=" * 72)
        print("  Slack    (s): added to  <=  constraints")
        print("  Surplus  (p): subtracted from  >=  constraints")
        print("  Artificial(a): added to  >=  and  =  constraints")
        print()
        if self.sense == "min":
            print("  Big-M objective (MIN):  Z = original cost  +  M * (sum of artificials)")
        else:
            print("  Big-M objective (MAX):  Z = original profit -  M * (sum of artificials)")
        print()

        n = self.n_orig
        for i, (coeffs, sense, rhs) in enumerate(self.constraints):
            parts = []
            for j in range(len(self.col_names)):
                coeff = self.A[i][j]
                if coeff == V(0):
                    continue
                name = self.col_names[j]
                s = fmt(coeff)
                if s == "1":
                    parts.append(name)
                elif s == "-1":
                    parts.append(f"- {name}")
                else:
                    parts.append(f"{s}{name}")
            pretty = parts[0]
            for p in parts[1:]:
                if p.startswith("- "):
                    pretty += " - " + p[2:]
                else:
                    pretty += " + " + p
            print(f"    {pretty}  =  {fmt(self.b[i])}")

        art_names = [self.col_names[j] for j in self.artificial_idx]
        print()
        print(f"  Artificial variables: {', '.join(art_names) if art_names else '(none)'}")
        print(f"  Initial basis:        {', '.join(self.row_names)}")

    def print_tableau(self, iteration: int) -> None:
        headers = ["BV", "cb"] + self.col_names + ["RHS"]
        rows = []
        for i, bidx in enumerate(self.basis):
            rows.append(
                [self.col_names[bidx], fmt(self.c_row[bidx])]
                + [fmt(self.A[i][j]) for j in range(len(self.col_names))]
                + [fmt(self.b[i])]
            )
        rows.append(
            ["cj - zj", ""]
            + [fmt(v) for v in self.cj_zj]
            + [fmt(self.z0)]
        )
        title = f"SIMPLEX TABLEAU  —  Iteration {iteration}    (current Z = {fmt(self.z0)})"
        print_table(headers, rows, title)

    # ----- simplex iterations ---------------------------------------------
    def _entering(self) -> Optional[int]:
        best = None
        best_val = None
        for j in range(len(self.col_names)):
            v = self.cj_zj[j]
            if self.sense == "min":
                # most negative cj-zj
                if is_neg(v) and (best is None or cmp_more_neg(v, best_val)):
                    best, best_val = j, v
            else:
                # most positive cj-zj  <=>  most negative  -(cj-zj)
                nv = mul(v, Fraction(-1))
                if is_neg(nv) and (best is None or cmp_more_neg(nv, mul(best_val, Fraction(-1)))):
                    best, best_val = j, v
        return best

    def _leaving(self, enter: int) -> Optional[int]:
        best_i = None
        best_ratio = None
        print("\n  Minimum-ratio test (leaving variable):")
        print(f"  {'BV':<8} {'RHS':<12} {'pivot col':<12} {'ratio':<12}")
        for i in range(len(self.A)):
            aij = self.A[i][enter]
            # pivot column must be strictly positive (no M in constraints here)
            if aij[1] != 0 or aij[0] <= 0:
                print(f"  {self.col_names[self.basis[i]]:<8} {fmt(self.b[i]):<12} {fmt(aij):<12} {'--':<12}")
                continue
            ratio = self.b[i][0] / aij[0]
            print(f"  {self.col_names[self.basis[i]]:<8} {fmt(self.b[i]):<12} {fmt(aij):<12} {_frac(ratio):<12}")
            if best_i is None or ratio < best_ratio:
                best_i, best_ratio = i, ratio
        return best_i

    def _pivot(self, leave_row: int, enter_col: int) -> None:
        piv = self.A[leave_row][enter_col]
        assert piv[1] == 0 and piv[0] != 0
        inv = Fraction(1) / piv[0]
        m = len(self.A)
        n = len(self.col_names)

        self.A[leave_row] = [mul(self.A[leave_row][j], inv) for j in range(n)]
        self.b[leave_row] = mul(self.b[leave_row], inv)

        for i in range(m):
            if i == leave_row:
                continue
            factor = self.A[i][enter_col]
            self.A[i] = [sub(self.A[i][j], _mul_val(factor, self.A[leave_row][j])) for j in range(n)]
            self.b[i] = sub(self.b[i], _mul_val(factor, self.b[leave_row]))

        self.basis[leave_row] = enter_col
        self.row_names[leave_row] = self.col_names[enter_col]
        self._recompute_cj_zj()

    def solve(self, max_iter: int = 50) -> None:
        self.print_formulation()
        self.to_standard_form()
        self.print_standard_form()

        print("\n" + "=" * 72)
        print("BIG-M SIMPLEX ITERATIONS")
        print("=" * 72)
        print("  Optimality test:")
        if self.sense == "min":
            print("    MIN problem — stop when every (cj - zj) >= 0")
            print("    Entering variable: most negative (cj - zj)")
        else:
            print("    MAX problem — stop when every (cj - zj) <= 0")
            print("    Entering variable: most positive (cj - zj)")
        print("    Leaving variable:  minimum non-negative RHS / pivot-column ratio")

        for it in range(max_iter + 1):
            self.print_tableau(it)

            enter = self._entering()
            if enter is None:
                print("\n  All reduced costs satisfy the optimality condition.  STOP.")
                self._report()
                return

            print(f"\n  Entering variable: {self.col_names[enter]}    (cj-zj = {fmt(self.cj_zj[enter])})")
            leave = self._leaving(enter)
            if leave is None:
                print("\n  Unbounded problem (no positive pivot).")
                return
            print(f"  Leaving variable:  {self.col_names[self.basis[leave]]}")
            print(f"  Pivot element:     {fmt(self.A[leave][enter])}  at ({self.col_names[self.basis[leave]]}, {self.col_names[enter]})")
            self._pivot(leave, enter)

        print("Iteration limit reached.")

    def _report(self) -> None:
        print("\n" + "=" * 72)
        print("OPTIMAL SOLUTION")
        print("=" * 72)

        values = {name: Fraction(0) for name in self.var_names}
        art_values = {}
        all_vals = {name: Fraction(0) for name in self.col_names}
        for i, bidx in enumerate(self.basis):
            name = self.col_names[bidx]
            val = self.b[i]
            if val[1] != 0:
                print(f"  WARNING: basic variable {name} still contains M.")
            all_vals[name] = val[0]
            if name in values:
                values[name] = val[0]
            if bidx in self.artificial_idx:
                art_values[name] = val[0]

        infeasible = any(v != 0 for v in art_values.values())
        if infeasible:
            print("  INFEASIBLE: a positive artificial variable remains in the basis.")
            for n, v in art_values.items():
                print(f"    {n} = {_frac(v)}")
            return

        print("  Decision variables:")
        for name in self.var_names:
            print(f"      {name}*  =  {_frac(values[name])}   ({float(values[name]):.4f})")

        print("  Slack / surplus / artificial (all artificials must be 0):")
        for name in self.col_names[self.n_orig :]:
            print(f"      {name}   =  {_frac(all_vals[name])}")

        z = self.z0[0]  # M-part must be 0 at a feasible optimum
        print()
        print(f"  Optimal objective value:  Z*  =  {_frac(z)}   ({float(z):.4f})")
        print("=" * 72)


def _mul_val(a: Value, b: Value) -> Value:
    """Product of two (const + m M) values. Constraint entries have m=0."""
    return (a[0] * b[0], a[0] * b[1] + a[1] * b[0])


def main() -> None:
    print("\nASSIGNMENT  —  BIG-M SIMPLEX METHOD\n")
    solver = BigMSimplex(
        c=[4, 1],
        constraints=[
            ([3, 1], "=", 3),
            ([4, 3], ">=", 6),
            ([1, 2], "<=", 4),
        ],
        sense="min",
        var_names=["x1", "x2"],
    )
    solver.solve()


if __name__ == "__main__":
    main()
