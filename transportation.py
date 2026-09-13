"""
Transportation Problem  —  VAM  then  MODI
==========================================
(i) Vogel's Approximation Method (VAM)  ->  initial basic feasible solution
(ii) MODI (Modified Distribution / UV)  ->  optimality test and improvement

Classic balanced 3-source, 4-destination problem (Sharma / Gupta / Taha):

                W1    W2    W3    W4     Supply
        F1      19    30    50    10        7
        F2      70    30    40    60        9
        F3      40     8    70    20       18
        Demand   5     8     7    14       34
"""

from copy import deepcopy
from typing import List, Optional, Sequence, Tuple

INF = 10**9
EPS = 1e-9


def print_matrix(
    cost: Sequence[Sequence[float]],
    supply: Sequence[float],
    demand: Sequence[float],
    alloc: Optional[Sequence[Sequence[Optional[float]]]] = None,
    title: str = "",
    sources: Optional[Sequence[str]] = None,
    dests: Optional[Sequence[str]] = None,
) -> None:
    m, n = len(supply), len(demand)
    sources = list(sources) if sources else [f"S{i+1}" for i in range(m)]
    dests = list(dests) if dests else [f"D{j+1}" for j in range(n)]

    headers = [""] + list(dests) + ["Supply"]
    rows = []
    for i in range(m):
        cells = [sources[i]]
        for j in range(n):
            c = cost[i][j]
            if alloc is None:
                cells.append(str(c))
            else:
                a = alloc[i][j]
                mark = "-" if a is None else (str(int(a) if a == int(a) else a))
                cells.append(f"{c} [{mark}]")
        s = supply[i]
        cells.append(str(int(s) if s == int(s) else s))
        rows.append(cells)
    dem = ["Demand"] + [str(int(d) if d == int(d) else d) for d in demand] + [""]
    rows.append(dem)

    widths = [len(h) for h in headers]
    for row in rows:
        for k, cell in enumerate(row):
            widths[k] = max(widths[k], len(str(cell)))

    def hline() -> str:
        return "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def prow(cells: Sequence[str]) -> str:
        return "|" + "|".join(f" {c:^{w}} " for c, w in zip(cells, widths)) + "|"

    if title:
        print(f"\n{title}")
    print(hline())
    print(prow(headers))
    print(hline())
    for row in rows[:-1]:
        print(prow(row))
    print(hline())
    print(prow(rows[-1]))
    print(hline())


def total_cost(cost, alloc) -> float:
    tot = 0.0
    for i in range(len(alloc)):
        for j in range(len(alloc[0])):
            a = alloc[i][j]
            if a is not None and a > 0:
                tot += a * cost[i][j]
    return tot


def count_basic(alloc) -> int:
    return sum(1 for row in alloc for a in row if a is not None)


# ===========================================================================
# (i) Vogel's Approximation Method
# ===========================================================================
def row_penalty(cost_row: Sequence[float], active_cols: Sequence[int]) -> float:
    vals = sorted(cost_row[j] for j in active_cols)
    if not vals:
        return -1
    if len(vals) == 1:
        return vals[0]
    return vals[1] - vals[0]


def col_penalty(cost, active_rows, j) -> float:
    vals = sorted(cost[i][j] for i in active_rows)
    if not vals:
        return -1
    if len(vals) == 1:
        return vals[0]
    return vals[1] - vals[0]


def vam(
    cost: List[List[float]],
    supply: List[float],
    demand: List[float],
    sources: Sequence[str],
    dests: Sequence[str],
) -> List[List[Optional[float]]]:
    m, n = len(supply), len(demand)
    rem_s = list(supply)
    rem_d = list(demand)
    alloc: List[List[Optional[float]]] = [[None] * n for _ in range(m)]
    active_r = set(range(m))
    active_c = set(range(n))
    step = 0

    print("\n" + "=" * 72)
    print("(i) VOGEL'S APPROXIMATION METHOD  —  Initial Basic Feasible Solution")
    print("=" * 72)
    print("  At each step:")
    print("    1. Penalty of a row/column = (2nd lowest cost) - (lowest cost)")
    print("    2. Choose the row or column with the largest penalty")
    print("    3. Allocate as much as possible to its cheapest available cell")
    print("    4. Cross out the exhausted row or column and repeat")

    while active_r and active_c:
        step += 1
        r_pen = {i: row_penalty(cost[i], list(active_c)) for i in active_r}
        c_pen = {j: col_penalty(cost, list(active_r), j) for j in active_c}

        print(f"\n--- VAM Step {step} ---")
        print("  Remaining supply:", {sources[i]: rem_s[i] for i in sorted(active_r)})
        print("  Remaining demand:", {dests[j]: rem_d[j] for j in sorted(active_c)})
        print("  Row penalties:   ", {sources[i]: r_pen[i] for i in sorted(active_r)})
        print("  Column penalties:", {dests[j]: c_pen[j] for j in sorted(active_c)})

        # Highest penalty; ties broken by cheapest cell in that line.
        best_kind = None  # 'row' or 'col'
        best_idx = None
        best_pen = -1.0
        best_cheap = INF

        for i, p in r_pen.items():
            cheap = min(cost[i][j] for j in active_c)
            if p > best_pen or (p == best_pen and cheap < best_cheap):
                best_pen, best_cheap = p, cheap
                best_kind, best_idx = "row", i
        for j, p in c_pen.items():
            cheap = min(cost[i][j] for i in active_r)
            if p > best_pen or (p == best_pen and cheap < best_cheap):
                best_pen, best_cheap = p, cheap
                best_kind, best_idx = "col", j

        if best_kind == "row":
            i = best_idx
            j = min(active_c, key=lambda jj: cost[i][jj])
            print(f"  Largest penalty is ROW {sources[i]} = {best_pen}")
            print(f"  Cheapest cell in this row: ({sources[i]}, {dests[j]}) cost {cost[i][j]}")
        else:
            j = best_idx
            i = min(active_r, key=lambda ii: cost[ii][j])
            print(f"  Largest penalty is COLUMN {dests[j]} = {best_pen}")
            print(f"  Cheapest cell in this column: ({sources[i]}, {dests[j]}) cost {cost[i][j]}")

        qty = min(rem_s[i], rem_d[j])
        alloc[i][j] = (alloc[i][j] or 0) + qty
        rem_s[i] -= qty
        rem_d[j] -= qty
        print(f"  Allocate {qty} units to ({sources[i]}, {dests[j]})")

        # Cross out exhausted lines. If both become zero, drop one and keep
        # the other as a degenerate basic cell of 0 (needed for m+n-1).
        row_out = rem_s[i] <= EPS
        col_out = rem_d[j] <= EPS
        if row_out and col_out and len(active_r) + len(active_c) > 2:
            # Degeneracy: keep the row, drop the column (0 already allocated).
            active_c.discard(j)
            print(f"  Both {sources[i]} and {dests[j]} exhausted (degenerate). Cross out {dests[j]}.")
        elif row_out:
            active_r.discard(i)
            print(f"  Cross out {sources[i]} (supply exhausted).")
        elif col_out:
            active_c.discard(j)
            print(f"  Cross out {dests[j]} (demand exhausted).")

        if len(active_r) == 1 and len(active_c) == 1:
            i = next(iter(active_r))
            j = next(iter(active_c))
            qty = min(rem_s[i], rem_d[j])
            if qty > EPS or alloc[i][j] is None:
                alloc[i][j] = (alloc[i][j] or 0) + qty
                rem_s[i] -= qty
                rem_d[j] -= qty
                print(f"  Final allocation: {qty} units to ({sources[i]}, {dests[j]})")
            active_r.clear()
            active_c.clear()

    print_matrix(cost, supply, demand, alloc, "VAM allocation  [cost  (quantity)]", sources, dests)
    z = total_cost(cost, alloc)
    print(f"\n  Number of basic cells: {count_basic(alloc)}   (need m+n-1 = {m}+{n}-1 = {m+n-1})")
    print(f"  Initial transportation cost (VAM):  {z:.0f}")
    return alloc


# ===========================================================================
# (ii) MODI  (Modified Distribution / UV method)
# ===========================================================================
def _occupied(alloc) -> List[Tuple[int, int]]:
    return [(i, j) for i, row in enumerate(alloc) for j, a in enumerate(row) if a is not None]


def _ensure_non_degenerate(alloc, m, n) -> None:
    """Add 0-basic cells until there are m+n-1 independents."""
    needed = m + n - 1
    while count_basic(alloc) < needed:
        placed = False
        for i in range(m):
            for j in range(n):
                if alloc[i][j] is not None:
                    continue
                # Independent if it does not close a cycle with current basics.
                trial = deepcopy(alloc)
                trial[i][j] = 0.0
                if _find_cycle(trial, i, j) is None:
                    alloc[i][j] = 0.0
                    print(f"  Degeneracy: add a 0-basic cell at ({i}, {j})")
                    placed = True
                    break
            if placed:
                break
        if not placed:
            break


def _find_cycle(alloc, si, sj) -> Optional[List[Tuple[int, int]]]:
    """
    Closed loop through occupied cells starting at the entering cell (si, sj).
    Moves alternate horizontal / vertical. Returns vertices in order, or None.
    """
    occ = set(_occupied(alloc))
    occ.add((si, sj))

    def neighbors(i, j, horiz: bool):
        if horiz:
            return [(i, jj) for ii, jj in occ if ii == i and jj != j]
        return [(ii, j) for ii, jj in occ if jj == j and ii != i]

    def search(path, used, horiz: bool):
        i, j = path[-1]
        for nxt in neighbors(i, j, horiz):
            if nxt == (si, sj):
                # Even-length cycle: path currently has an even number of vertices.
                if len(path) >= 4 and len(path) % 2 == 0:
                    return path
                continue
            if nxt in used:
                continue
            used.add(nxt)
            got = search(path + [nxt], used, not horiz)
            if got is not None:
                return got
            used.remove(nxt)
        return None

    # Try a horizontal first step, then a vertical first step.
    for first_horiz in (True, False):
        found = search([(si, sj)], {(si, sj)}, first_horiz)
        if found is not None:
            return found
    return None


def _solve_uv(cost, alloc) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    m, n = len(alloc), len(alloc[0])
    u = [None] * m
    v = [None] * n
    basics = _occupied(alloc)
    u[0] = 0.0  # arbitrary origin
    changed = True
    guard = 0
    while changed and guard < m * n + 5:
        changed = False
        guard += 1
        for i, j in basics:
            if u[i] is not None and v[j] is None:
                v[j] = cost[i][j] - u[i]
                changed = True
            elif v[j] is not None and u[i] is None:
                u[i] = cost[i][j] - v[j]
                changed = True
    return u, v


def modi(
    cost: List[List[float]],
    supply: List[float],
    demand: List[float],
    alloc: List[List[Optional[float]]],
    sources: Sequence[str],
    dests: Sequence[str],
) -> List[List[Optional[float]]]:
    m, n = len(supply), len(demand)
    alloc = deepcopy(alloc)

    print("\n" + "=" * 72)
    print("(ii) MODI METHOD  —  Optimality test and iterative improvement")
    print("=" * 72)
    print("  For every basic cell (i, j):   u_i + v_j = c_ij")
    print("  For every non-basic cell:      d_ij = c_ij - u_i - v_j")
    print("  MIN problem is optimal when every d_ij >= 0.")
    print("  If some d_ij < 0, enter the most negative cell, form a closed")
    print("  loop with basic cells, and shift theta = min of (-) positions.")

    iteration = 0
    while True:
        iteration += 1
        _ensure_non_degenerate(alloc, m, n)
        u, v = _solve_uv(cost, alloc)

        print(f"\n{'=' * 60}")
        print(f"MODI Iteration {iteration}")
        print(f"{'=' * 60}")
        print_matrix(cost, supply, demand, alloc, "Current allocation  [cost  (quantity)]", sources, dests)

        def _num(x):
            if x is None:
                return None
            return int(x) if abs(x - round(x)) < 1e-9 else x

        print("  Dual variables  (set u1 = 0):")
        print("    u =", {sources[i]: _num(u[i]) for i in range(m)})
        print("    v =", {dests[j]: _num(v[j]) for j in range(n)})

        if any(x is None for x in u + v):
            print("  Could not determine all u_i, v_j (basis not a tree).")
            break

        d = [[None] * n for _ in range(m)]
        most_neg = 0.0
        enter = None
        print("\n  Opportunity costs  d_ij = c_ij - u_i - v_j  (blank = basic):")
        headers = [""] + list(dests)
        rows = []
        for i in range(m):
            row = [sources[i]]
            for j in range(n):
                if alloc[i][j] is not None:
                    row.append("basic")
                    continue
                dij = cost[i][j] - u[i] - v[j]
                d[i][j] = dij
                row.append(f"{dij:g}")
                if dij < most_neg - 1e-12:
                    most_neg = dij
                    enter = (i, j)
            rows.append(row)

        widths = [max(len(headers[k]), max(len(r[k]) for r in rows)) for k in range(n + 1)]
        line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
        print(line)
        print("|" + "|".join(f" {headers[k]:^{widths[k]}} " for k in range(n + 1)) + "|")
        print(line)
        for r in rows:
            print("|" + "|".join(f" {r[k]:^{widths[k]}} " for k in range(n + 1)) + "|")
        print(line)

        if enter is None:
            print("\n  All d_ij >= 0.  The allocation is OPTIMAL.")
            break

        ei, ej = enter
        print(f"\n  Most negative opportunity cost: d({sources[ei]}, {dests[ej]}) = {most_neg:g}")
        print(f"  Entering cell: ({sources[ei]}, {dests[ej]})")

        cycle = _find_cycle(alloc, ei, ej)
        if cycle is None:
            print("  No closed loop found; cannot improve. Stopping.")
            break

        labels = [f"({sources[i]}, {dests[j]})" for i, j in cycle]
        signs = ["+" if k % 2 == 0 else "-" for k in range(len(cycle))]
        print("  Closed loop (alternating + / -):")
        print("   ", " -> ".join(f"{lab}[{sg}]" for lab, sg in zip(labels, signs)))

        minus_cells = [cycle[k] for k in range(len(cycle)) if k % 2 == 1]
        theta = min(alloc[i][j] for i, j in minus_cells)
        print(f"  theta = min of (-) allocations = {theta:g}")

        for k, (i, j) in enumerate(cycle):
            if k % 2 == 0:
                alloc[i][j] = (alloc[i][j] or 0) + theta
            else:
                alloc[i][j] = alloc[i][j] - theta
                if abs(alloc[i][j]) <= EPS:
                    alloc[i][j] = None  # leaves the basis

        print(f"  Shift {theta:g} units around the loop.")
        print(f"  Cost after this iteration: {total_cost(cost, alloc):.0f}")

    z = total_cost(cost, alloc)
    print("\n" + "=" * 72)
    print("OPTIMAL SHIPMENT PLAN")
    print("=" * 72)
    print_matrix(cost, supply, demand, alloc, "Optimal allocation  [cost  (quantity)]", sources, dests)
    print("\n  Positive shipments:")
    for i in range(m):
        for j in range(n):
            a = alloc[i][j]
            if a is not None and a > EPS:
                print(f"      {sources[i]}  ->  {dests[j]}   :  {a:g} units   (cost {cost[i][j]} each)")
    print(f"\n  Minimum total transportation cost  Z*  =  {z:.0f}")
    print("=" * 72)
    return alloc


def problem_data():
    cost = [
        [19, 30, 50, 10],
        [70, 30, 40, 60],
        [40, 8, 70, 20],
    ]
    supply = [7, 9, 18]
    demand = [5, 8, 7, 14]
    sources = ["F1", "F2", "F3"]
    dests = ["W1", "W2", "W3", "W4"]
    return cost, supply, demand, sources, dests


def print_problem(cost, supply, demand, sources, dests) -> None:
    print("\nASSIGNMENT  —  TRANSPORTATION PROBLEM  (VAM + MODI)\n")
    print("=" * 72)
    print("PROBLEM STATEMENT")
    print("=" * 72)
    print("  Three factories ship to four warehouses.")
    print("  Unit transportation costs, supplies and demands:")
    print_matrix(cost, supply, demand, None, "", sources, dests)
    print(f"  Total supply = {sum(supply)}  =  total demand = {sum(demand)}   (balanced)")
    print("  Objective: minimize total transportation cost.")


def main(method: str = "both") -> None:
    """
    method: 'vam' | 'modi' | 'both'
    MODI always starts from the VAM initial basic feasible solution.
    """
    cost, supply, demand, sources, dests = problem_data()
    print_problem(cost, supply, demand, sources, dests)

    ibfs = vam(cost, supply, demand, sources, dests)
    if method == "vam":
        print("\n  (MODI skipped — run with --method modi or --method both to test optimality.)")
        return
    modi(cost, supply, demand, ibfs, sources, dests)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Solve the transportation problem with VAM and/or MODI.")
    parser.add_argument(
        "--method",
        choices=["vam", "modi", "both"],
        default="both",
        help="vam: initial solution only; modi/both: VAM then MODI optimality test",
    )
    args = parser.parse_args()
    main(args.method)
