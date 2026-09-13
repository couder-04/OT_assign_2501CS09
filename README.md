# Optimization Techniques Assignment

**Submit this PDF:** [OT_Assignment_Report.pdf](OT_Assignment_Report.pdf)

It contains the write-up plus screenshot-style Python source and terminal output for **Big-M**, **VAM**, and **MODI** (27 pages). Rebuild with `python3 generate_pdf.py`.

Computational solutions of two classic Operations Research problems:

| # | Method | Problem type | Program |
|---|---|---|---|
| 1 | **Big-M Simplex Method** | Constrained LPP (mixed \(\le\), \(\ge\), \(=\)) | [`big_m_method.py`](big_m_method.py) |
| 2 | **VAM + MODI** | Balanced **transportation problem (TP)** | [`transportation.py`](transportation.py) |

Python 3 standard library only — no `numpy`, `scipy`, or other packages.

```bash
python3 big_m_method.py                       # Part 1: Big-M
python3 transportation.py --method vam        # Part 2(i): VAM only
python3 transportation.py --method modi       # Part 2(ii): VAM, then MODI
python3 transportation.py                     # Part 2: both, in sequence
```

Jupyter: open [`OT_Assignment.ipynb`](OT_Assignment.ipynb) and run the cells.  
Saved terminal logs: [`outputs/`](outputs/).

---

## Part 1 — Big-M Simplex Method

### 1.1 Why Big-M?

Ordinary simplex needs an **initial basic feasible solution**. That is immediate when every constraint is \(\le\) (slack variables form the basis). Equality and \(\ge\) constraints do not: they need **artificial variables**. Big-M puts a huge penalty \(M\) on each artificial in the objective so simplex drives them to zero (if the LPP is feasible).

| Constraint | Extra variables | Role |
|---|---|---|
| \(\le\) | slack \(s\) | unused resource; starts in the basis |
| \(\ge\) | surplus \(p\) **and** artificial \(a\) | surplus takes up the excess; artificial starts in the basis |
| \(=\) | artificial \(a\) | starts in the basis |

- **Minimize:** \(Z = c^\top x + M\sum a_i\)  (artificials are expensive)
- **Maximize:** \(Z = c^\top x - M\sum a_i\)  (artificials destroy profit)

If an artificial remains positive at termination, the original LPP is **infeasible**.

### 1.2 Selected LPP

A standard mixed-constraint textbook problem (Taha / Winston):

\[
\begin{aligned}
\text{Minimize } \quad
  Z &= 4x_1 + x_2 \\
\text{subject to } \quad
  3x_1 + x_2 &= 3 \\
  4x_1 + 3x_2 &\ge 6 \\
  x_1 + 2x_2 &\le 4 \\
  x_1, x_2 &\ge 0
\end{aligned}
\]

All three constraint types appear, so slack, surplus **and** artificial variables are required.

### 1.3 Standard form

\[
\begin{aligned}
3x_1 + x_2 + a_1 &= 3 \\
4x_1 + 3x_2 - p_1 + a_2 &= 6 \\
x_1 + 2x_2 + s_1 &= 4 \\[4pt]
Z &= 4x_1 + x_2 + M(a_1 + a_2)
\end{aligned}
\]

| Variable | Meaning | Opening \(c_j\) |
|---|---|---|
| \(x_1, x_2\) | decision variables | \(4,\ 1\) |
| \(a_1, a_2\) | artificials | \(M,\ M\) |
| \(p_1\) | surplus on the \(\ge\) constraint | \(0\) |
| \(s_1\) | slack on the \(\le\) constraint | \(0\) |

**Initial basis:** \(\{a_1, a_2, s_1\}\).  
The program stores every tableau entry as \(a + bM\) (exact fractions), so \(M\) is never replaced by a large number.

### 1.4 Algorithm (as implemented)

1. Convert to standard form; put artificials/slacks in the basis.
2. Compute reduced costs \(c_j - z_j\) after eliminating basic variables from \(Z\).
3. **MIN optimality test:** stop when every \(c_j - z_j \ge 0\).
4. **Entering variable:** most negative \(c_j - z_j\).
5. **Leaving variable:** minimum-ratio test (smallest non-negative \(\text{RHS}/\text{pivot column}\)).
6. Pivot and repeat.

### 1.5 Iterations (program output)

| Iter. | Basis | \(Z\) | Enter | Leave |
|---|---|---|---|---|
| 0 | \(a_1, a_2, s_1\) | \(9M\) | \(x_1\) (\(4-7M\)) | \(a_1\) |
| 1 | \(x_1, a_2, s_1\) | \(4+2M\) | \(x_2\) (\(-\tfrac13-\tfrac53 M\)) | \(a_2\) |
| 2 | \(x_1, x_2, s_1\) | \(18/5\) | \(p_1\) (\(-1/5\)) | \(s_1\) |
| 3 | \(x_1, x_2, p_1\) | \(17/5\) | — **optimal** | — |

Both artificials have left the basis, so the solution is feasible for the original LPP.

### 1.6 Optimal solution

| Variable | Value |
|---|---|
| \(x_1^*\) | \(2/5 = 0.4\) |
| \(x_2^*\) | \(9/5 = 1.8\) |
| \(p_1\) | \(1\) (second constraint is slack by 1) |
| \(s_1, a_1, a_2\) | \(0\) |
| \(Z^*\) | \(17/5 = 3.4\) |

Check:

- \(3(0.4)+1.8 = 3\)
- \(4(0.4)+3(1.8) = 7 \ge 6\)
- \(0.4+2(1.8) = 4\)
- \(Z = 4(0.4)+1.8 = 3.4\)

```bash
python3 big_m_method.py
```

Screenshot: the source of `big_m_method.py`, then the printed tableaus and this optimal block.

---

## Part 2 — Transportation Problem (TP)

A **transportation problem** ships a homogeneous product from \(m\) sources (capacities \(a_i\)) to \(n\) destinations (demands \(b_j\)) at unit cost \(c_{ij}\):

\[
\min Z = \sum_{i=1}^{m}\sum_{j=1}^{n} c_{ij}\, x_{ij}
\quad\text{s.t.}\quad
\sum_j x_{ij}=a_i,\;
\sum_i x_{ij}=b_j,\;
x_{ij}\ge 0.
\]

It is **balanced** when \(\sum a_i = \sum b_j\). A basic feasible solution has \(m+n-1\) independent occupied cells.

The assignment requires the two methods **one at a time**:

1. **VAM** — Vogel’s Approximation Method → initial basic feasible solution (IBFS)
2. **MODI** — Modified Distribution (UV) method → optimality test and improvement

### 2.1 Selected TP

Three factories \(F_1,F_2,F_3\) supply four warehouses \(W_1,W_2,W_3,W_4\).

|  | \(W_1\) | \(W_2\) | \(W_3\) | \(W_4\) | Supply \(a_i\) |
|---|---|---|---|---|---|
| **\(F_1\)** | 19 | 30 | 50 | 10 | 7 |
| **\(F_2\)** | 70 | 30 | 40 | 60 | 9 |
| **\(F_3\)** | 40 | 8 | 70 | 20 | 18 |
| **Demand \(b_j\)** | 5 | 8 | 7 | 14 | **34 = 34** |

Balanced. Need \(3+4-1 = 6\) basic cells.

### 2.2 (i) Vogel’s Approximation Method (VAM)

Penalty of a row or column = *(second-smallest cost) − (smallest cost)* among remaining cells. A large penalty means that skipping the cheapest cell in that line is expensive, so VAM allocates there first.

**At each step:**

1. Compute all row and column penalties.
2. Pick the line with the **largest** penalty.
3. Allocate as much as possible to that line’s **cheapest** available cell.
4. Cross out the exhausted row or column and repeat.

**VAM allocations (program):**

| Step | Max penalty | Cell | Qty | Cross out |
|---|---|---|---|---|
| 1 | col \(W_2 = 22\) | \(F_3\to W_2\) | 8 | \(W_2\) |
| 2 | col \(W_1 = 21\) | \(F_1\to W_1\) | 5 | \(W_1\) |
| 3 | row \(F_3 = 50\) | \(F_3\to W_4\) | 10 | \(F_3\) |
| 4 | col \(W_4 = 50\) | \(F_1\to W_4\) | 2 | \(F_1\) |
| 5 | col \(W_4 = 60\) | \(F_2\to W_4\) | 2 | \(W_4\) |
| final | — | \(F_2\to W_3\) | 7 | — |

**IBFS (6 basic cells), cost 779:**

|  | \(W_1\) | \(W_2\) | \(W_3\) | \(W_4\) |
|---|---|---|---|---|
| **\(F_1\)** | 5 | — | — | 2 |
| **\(F_2\)** | — | — | 7 | 2 |
| **\(F_3\)** | — | 8 | — | 10 |

\[
Z_{\text{VAM}} = 5\cdot 19 + 2\cdot 10 + 7\cdot 40 + 2\cdot 60 + 8\cdot 8 + 10\cdot 20 = 779
\]

```bash
python3 transportation.py --method vam
```

This IBFS is **not** guaranteed optimal — MODI tests and improves it.

### 2.3 (ii) MODI (Modified Distribution / UV)

For every **basic** cell:

\[
u_i + v_j = c_{ij}
\]

(one dual is fixed, here \(u_1 = 0\)). For every **non-basic** cell the opportunity cost is

\[
d_{ij} = c_{ij} - u_i - v_j.
\]

- **Minimization is optimal iff every \(d_{ij} \ge 0\).**
- If some \(d_{ij} < 0\), enter the most negative cell, form a closed **+ / −** loop with basic cells, and shift \(\theta = \min\) of the \(-\) allocations.

**Iteration 1** (from VAM). Duals: \(u=(0,50,10)\), \(v=(19,-2,-10,10)\).

Most negative: \(d_{F_2,W_2} = -18\). Loop:

\[
(F_2,W_2)^+ \;\to\; (F_2,W_4)^- \;\to\; (F_3,W_4)^+ \;\to\; (F_3,W_2)^-
\]

\(\theta = \min(2,8) = 2\). New cost \(779 - 18\cdot 2 = 743\).

**Iteration 2.** All \(d_{ij} \ge 0\) → **optimal**.

### 2.4 Optimal shipment plan

|  | \(W_1\) | \(W_2\) | \(W_3\) | \(W_4\) | Supply |
|---|---|---|---|---|---|
| **\(F_1\)** | **5** | — | — | **2** | 7 |
| **\(F_2\)** | — | **2** | **7** | — | 9 |
| **\(F_3\)** | — | **6** | — | **12** | 18 |
| **Demand** | 5 | 8 | 7 | 14 | 34 |

| Route | Units | Unit cost | Contribution |
|---|---|---|---|
| \(F_1 \to W_1\) | 5 | 19 | 95 |
| \(F_1 \to W_4\) | 2 | 10 | 20 |
| \(F_2 \to W_2\) | 2 | 30 | 60 |
| \(F_2 \to W_3\) | 7 | 40 | 280 |
| \(F_3 \to W_2\) | 6 | 8 | 48 |
| \(F_3 \to W_4\) | 12 | 20 | 240 |
| **Total \(Z^*\)** | | | **743** |

```bash
python3 transportation.py --method modi
```

Screenshot: VAM function + VAM output (cost 779), then MODI function + MODI iterations and this plan (cost 743).

---

## Files

```
ot_assignment/
├── OT_Assignment_Report.pdf     # SUBMIT THIS — code + output screenshots
├── big_m_method.py              # Part 1 — Big-M simplex (tableaus)
├── transportation.py            # Part 2 — VAM then MODI
├── generate_pdf.py              # rebuilds the PDF
├── OT_Assignment.ipynb          # same two parts, cell by cell
├── README.md
└── outputs/
    ├── big_m_output.txt
    ├── vam_output.txt
    ├── modi_output.txt
    └── transportation_output.txt
```

## Screenshots for the submitted PDF

The PDF [`OT_Assignment_Report.pdf`](OT_Assignment_Report.pdf) already includes editor-style source listings and terminal-style output for Big-M, VAM, and MODI. Submit that file.

To regenerate after changing the programs:

```bash
python3 big_m_method.py > outputs/big_m_output.txt
python3 transportation.py --method vam > outputs/vam_output.txt
python3 transportation.py --method modi > outputs/modi_output.txt
python3 generate_pdf.py
```
