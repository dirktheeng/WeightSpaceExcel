# Weight block notes: lookup search core (ids 360 to 374)

Hand-written. Not generated. Log: log/func-lookup-agent.md (2026-11-06); decision LK1 in log/WORKLOG.md. Value tags: encodings/value.md. Text heap layout: encodings/memory-map.md section 9. Primitives: encodings/primitives.md (IS_K, ROUND, FLOOR, MUX, MUX_INT, UNPACK3). Tests: tests/output/func_lookup/test_core.py (115 cases).

## 1. What the core does

Given a lookup value v and a one-dimensional vector of n cells, it returns the 0-based position chosen by a mode M, or "not found". Every match-type function (MATCH, VLOOKUP, HLOOKUP, LOOKUP, XMATCH, XLOOKUP) is a thin wrapper around it (weights/func/lookup/README.md).

| M | Search | Result | Used by |
|---|---|---|---|
| 1 | linear, first to last | first cell equal to v (wildcards if W) | MATCH 0, VLOOKUP/HLOOKUP FALSE, XMATCH 0 and 2 with search 1 |
| 2 | linear, first to last | first exact match, else the largest value < v (first of equals) | XMATCH -1, search 1 |
| 3 | linear, first to last | first exact match, else the smallest value > v | XMATCH 1, search 1 |
| 4, 5, 6 | as 1, 2, 3 from last to first | | search_mode -1 |
| 7 | binary, ascending data | last cell <= v | MATCH 1, VLOOKUP/HLOOKUP TRUE, LOOKUP, XMATCH -1 / 2 |
| 8 | binary, descending data | last cell >= v | MATCH -1, XMATCH 1 / -2 |
| 9 | binary, ascending | first cell >= v | XMATCH 1 / 2 |
| 10 | binary, descending | first cell <= v | XMATCH -1 / -2 |
| 11, 12 | as 7, 8 | found only if that cell equals v | XMATCH 0 / 2, 0 / -2 |

Equality and order are Excel's lookup rules: numbers compare numerically (exact equality, no 15-digit tolerance), text case-insensitively (A..Z folded to a..z, then UTF-16 code-unit order, as ev_cmp), booleans as 0/1 among booleans. A value only ever matches a cell of its own class: 1 does not match "1" or TRUE; blank lookup values and error cells never match. In binary modes, a cell of another class steers the search by Excel's class order (number < text < boolean < error) and a blank cell always moves the search to the left (trailing blanks are skipped), but only a cell of the lookup value's class can become the result. So MATCH(9.99E+307, A:A) finds the last number, MATCH("b", {1;2;3}, 1) is #N/A.

## 2. Register map (core convention; caller to lk_start)

| Word | Entry (set by the caller) | Inside the core | Exit |
|---|---|---|---|
| 8, 9 | LR, LP: return link | LR, LP of CELL_GET calls | clobbered |
| 12 | | CELL_GET status | STATUS: 0 found, 1 not found |
| 13, 14 | | A = probed cell value | clobbered |
| 15, 16 | B = lookup value (dereferenced) | preserved | preserved |
| 17, 18 | | C = best candidate (M 2, 3, 5, 6) | clobbered |
| 19, 20, 21 | AS = sheet, AR1 = R0, AC1 = C0 (first cell) | probe address | clobbered |
| 22, 23, 24 | (evaluator's GEN, HT, CYC) | R0, C0, dir | restored |
| 25 | | CELL_GET P0 | clobbered |
| 26, 27 | (evaluator's P1, N0) | M, lo | restored |
| 28 | N1 = n (n >= 1) | hi | clobbered |
| 29, 30 | | CELL_GET T0, T1 | clobbered |
| 31 | T2 = dir (0 down a column, 1 along a row) | probe index idx | clobbered |
| 32 | T3 = M | res (-1 none) | T3 = result index |
| 33, 34 | | T4, T5 = caller link | clobbered |
| 35 | | T6 = c, compare result in {-1, 0, 1} | clobbered |
| 36 | T7 = W (1: wildcards for text) | W | preserved |
| 37 | | T8 = eqRes (cell at res equals v) | clobbered |
| 38 | | T9 = s (same class, and class number/text/boolean) | clobbered |
| 39 | | T10 = pattern length (wildcards) | clobbered |
| 40..47 | (kernel locals L0..L7) | text compare and wildcard scratch | restored |
| 10 | RSP | RSP + 14 (spill) | RSP |

The core takes 14 words of RET_STACK. Words 22..27 and 40..47 are saved by one block write in lk_start and restored by one block read issued by lk_nx and consumed by lk_fin, so every word of the function ABI preserve set (encodings/functions.md section 2) is intact on return. Memory: PATBUF 0x0BF000..0x0BF7FF (pattern tokens) and TXTBUF 0x0BF800..0x0BFFFF (unpacked cell text), the top 4 KiB of EVAL_SCRATCH, used only during one search (requested of the memory-map owner; patterns and cell texts up to 2047 units).

## 3. Control flow and step counts

    lk_start -> [lk_pt2 <-> lk_pt1 ... ] -> lk_nx -> CELL_GET (16..19) -> lk_cmp -> lk_upd -> lk_nx ... -> lk_fin -> (T4, T5)
    lk_cmp text, ordering:  -> lk_tl0 -> lk_tl1 -> (lk_tw <-> lk_tv)* -> lk_upd
    lk_cmp text, wildcard:  -> lk_un2 <-> lk_un1 ... -> (lk_wa <-> lk_wb)* -> lk_upd
    lk_upd candidate vs best (M 2, 3, 5, 6): -> lk_cmp PC 1 -> (text loop) -> lk_upd PC 1

Per probe of a number cell: lk_nx 1, CELL_GET 4 (2 for an empty cell), lk_cmp 1, lk_upd 1 = 7 steps. Text adds 2 + 2 per 3 characters compared; wildcard matching adds 2 per 3 characters to unpack and 2 per matcher iteration. Entry 1 step, exit 2. A binary search over n cells takes about 7 log2(n) steps for numbers (test_step_counts_are_logarithmic_for_binary).

## 4. Networks

| Id | File | Step | Params |
|---|---|---|---|
| 360 | lk_start | spill (block write 14), initialise, route to lk_nx or the pattern loader | 413 |
| 361 | lk_nx | done = lo > hi: block read of the spill -> lk_fin; else idx and probe address, CELL_GET | 613 |
| 362 | lk_cmp | class and value compare of A with Y (B at PC 0, C at PC 1), route by text kind | 699 |
| 363 | lk_fin | block consumer (79 inputs): restore, STATUS, return | 123 |
| 364 | lk_upd | mode logic: window, result, best candidate | 3099 |
| 365 | lk_tl0 | text: store len(A), read len(Y) | 21 |
| 366 | lk_tl1 | text: store len(Y); both empty -> equal; else read word 0 of A | 77 |
| 367 | lk_tw | text: KEY of A's word i (masked past its length), read Y's word i | 144 |
| 368 | lk_tv | text: KEY of Y's word, compare; finish or read the next word of A | 273 |
| 369 | lk_pt1 | pattern word -> 3 tokens with tilde escapes, block write to PATBUF | 1002 |
| 370 | lk_pt2 | pattern loop head (PC 0 read length, PC 1 store it, PC 2 next word or done) | 199 |
| 371 | lk_un1 | cell text word -> 3 folded units, block write to TXTBUF | 126 |
| 372 | lk_un2 | text loop head (PC 0 stores the length); done: matcher start, read PATBUF[0] | 217 |
| 373 | lk_wa | matcher: store pattern token, read text unit | 16 |
| 374 | lk_wb | matcher step (one star backtrack point) | 1197 |
| | total | | 8219 |

Parameters count every dense weight and bias typed (zeros included).

## 5. Derivations

**lk_nx.** done = step(lo - hi - 0.5) (integers). Mode class from thresholds: bin = step(M - 6.5), ge4 = step(M - 3.5), rev = ge4 - bin, fwd = 1 - ge4. mid = FLOOR((lo + hi) / 2): x = 0.5 lo + 0.5 hi is an exact half-integer; r = ROUND(x) by the C = 1.5 2^52 bias pair; g = step(r - x) (r rounded up); mid = r - g. idx = MUX_INT(fwd; lo) + MUX_INT(rev; hi) + MUX_INT(bin; mid) with M = 2^23 (all |values| < 2^21), each MUX_INT(g; a) = relu(a - M (1 - g)) - relu(-a - M (1 - g)). AR1 = R0 + MUX_INT(1 - dir; idx), AC1 = C0 + MUX_INT(dir; idx). Done: mem_op 4, addr = relu(RSP - 14 - M (1 - done)), value = (64 2^20 + 14) done, next = 16 + 347 done.

**lk_cmp.** Y = MUX(q; C, B) by one mul layer on [q, q, 1 - q, 1 - q] x [tC, pC, tB, pB] (q = PC in {0, 1}); one product of each pair is exactly 0, so the sums are exact. gt = step(pA - pY), lt = step(pY - pA) (R2 rows, exact signs, V1 safe: only step reads them). Class: cls = tag - 1 + 5 [tag = 0] gives number 0, text 1, boolean 2, error 3, blank 4, so dcls = tA - tY - 5 nzA + 5 nzY, dp = step(dcls - 0.5), dm = step(-dcls - 0.5). inS = [1 <= tA <= 3] = nzA - [tA >= 4]. s = step(inS - dp - dm - 0.5); sNum = s and not text; sTxt = s and text (text = [tA >= 2] - [tA >= 3]). c = AND(sNum, gt) - AND(sNum, lt) + dp - dm. wild = step(sTxt + W - PC - 1.5). next = 364 + 7 wild + sTxt (lk_upd, lk_tl0 365, lk_un2 372). addr = sTxt pA by a mul layer (pA can be any double when not text, so MUX_INT would be wrong there). L0 = pA, L1 = pY, L2 = 0.

**lk_upd.** Indicators: thermometer g_k = step(M - k + 0.5), k = 1..13, and one-hot m_k = g_k - g_(k+1); q = [PC >= 1]; cp = [c = 1], cn = [c = -1], cz = 1 - cp - cn; nzA = [A not blank]; hasRes = [res >= 0]. Mode flags (sums of m_k): fwd = g1 - g4, rev = g4 - g7, lin = g1 - g7, bin = g7, Lsm = m2 + m5, Llg = m3 + m6, desc = m8 + m10 + m12, varF = m9 + m10, varL = m7 + m8 + m11 + m12. Gates (each an AND or AND-NOT of 0/1 words by one step unit):
- u1 = !desc & cp, u2 = desc & cn, u3 = !desc & cn, u4 = desc & cp; le = [c' <= 0] = 1 - u1 - u2 and ge = [c' >= 0] = 1 - u3 - u4 where c' = -c for descending data.
- lin0 = lin & !q, lin1 = lin & q; hS = s & cz (hit); candS = s & Lsm & cn, candL = s & Llg & cp (a candidate on the wanted side); betS = Lsm & cp, betL = Llg & cn (candidate beats the best, PC 1).
- gH = lin0 & hS; gCN = lin0 & cand & !hasRes; gCC = lin0 & cand & hasRes; gBT = lin1 & bet; kL = varL & le, kF = varF & ge, jL = varL & !le, jF = varF & !ge.
- gFA = fwd & !gH & !gCC, gRA = rev & !gH & !gCC (advance); gBR = (kL or jF) & nzA (move right), gBL = bin & (blank or jL or kF) (move left), gRec = (kL or kF) & s & nzA (record), gEq = gRec & cz, gEqOld = gRec & eqRes.
Outputs: lo' = lo + gFA + MUX_INT(gH; hi + 1 - lo) + MUX_INT(gBR; idx + 1 - lo); hi' = hi - gRA + MUX_INT(gBL; idx - 1 - hi); res' = res + MUX_INT(gH + gCN + gBT + gRec; idx - res); eqRes' = eqRes + gEq - gEqOld; C' = MUX(gCN + gBT; A, C) by a mul layer; next = 361 + gCC (lk_cmp to compare with the best), PC' = gCC. A hit sets lo = hi + 1, which ends both forward and reverse scans. Every gate is exclusive with the others it is summed with (they need different modes, PC values or c values), so every sum is 0 or 1.

**lk_fin.** found = step(hasRes - exReq + eqRes - 0.5), exReq = [M >= 11]; STATUS = 1 - found; next = T4, PC = T5; words 22..27 and 40..47 from block inputs 65..78.

**Text ordering (lk_tl0..lk_tv).** Strings are compared one packed word (3 units) at a time. KEY(w) for a heap word w < 2^48: q1 = w 2^-16 (exact), f1 = FLOOR(q1), c0 = w - 2^16 f1; f2 = FLOOR(f1 2^-16), c1 = f1 - 2^16 f2, c2 = f2 (UNPACK3 by two FLOORs, all exact integers). Fold f(u) = u + 32 ([u >= 65] - [u >= 91]). KEY = 2^32 f(c0) + 2^16 f(c1) + f(c2) puts the earliest unit in the most significant place, so integer order of keys is string order for one word. A word whose index is at or past the string's length counts as 0 (mul gate), and the padding units of a last word are 0, so a proper prefix compares lower, and equal keys over max(la, ly) units mean equal strings. d = KEY_A - KEY_Y (R2 integer row, exact below 2^49): c = step(d - 0.5) - step(-d - 0.5); the loop ends at the first d != 0 or when 3 (i + 1) >= max(la, ly), with max = la + relu(ly - la).

**Wildcards (lk_pt1, lk_pt2, lk_un1, lk_un2, lk_wa, lk_wb).** The pattern (B) is tokenized once per search into PATBUF, one token per unit: escaped unit -> fold(u); unescaped '~' -> -3 (NOP, escapes the next unit), '*' -> -2, '?' -> -1, else fold(u). With e the escape flag, gl = ['~'] & !e, gs = ['*'] & !e, gq = ['?'] & !e, e' = gl, chained through the three units of a word (e of unit 1 is gl of unit 0, and so on); token = fold(u) - 129 gl - 44 gs - 64 gq (126 - 129 = -3, 42 - 44 = -2, 63 - 64 = -1). Each text cell is unpacked and folded into TXTBUF (one unit per word). The matcher keeps p, t, star, mark (L3..L6), pattern length pl (T10) and text length tl (L1), and implements:

    if t = tl:   if P is STAR or NOP: p += 1  elif p = pl: match  else: no match
    else:        if p < pl and (P = ANY or P literal = T): p += 1, t += 1
                 elif p < pl and P = STAR:  star = p, mark = t, p += 1
                 elif p < pl and P = NOP:   p += 1
                 elif star >= 0:            p = star + 1, mark += 1, t = mark
                 else: no match

which is the standard linear-space matcher with one backtrack point (correct for '*' and '?'). Indicators: pE = [p >= pl], tE = [t >= tl], token classes from a threshold bank on P (-3.5, -2.5, -1.5, -0.5, 0.5), literal equality from step(P - T - 0.5) + step(T - P - 0.5), hasStar = [star >= 0]; every class indicator is ANDed with !pE because P is stale memory when p >= pl. Outputs use MUX_INT for star + 1, mark + 1, p and t.

## 6. Known limits

- Text order is code-unit order after ASCII folding, not Excel's locale collation (punctuation, accents). Shared with ev_cmp.
- A tilde before a character other than '*', '?' or '~' escapes that character (so "~a" matches "a") and a trailing tilde is ignored; Excel's handling of these is not documented (open question LK-Q1).
- Binary search with interior blank or other-class cells can differ from Excel, whose exact skipping rule is not documented (LK-Q2). Trailing blanks, numbers followed by text, and sorted data agree.
- Equality of numbers is exact (no 15-digit snapping); MATCH(0.1+0.2, {0.3}, 0) is #N/A here (open question LK-Q3).
- Patterns and cell texts in wildcard mode are limited to 2047 units (buffer size).
- Lookup values of errors are the wrapper's business (they propagate before the core is called).

## 7. Multi-role words

- **L0, L1, L2** hold the two handles and the word index of the text ordering compare, or the cell text handle, length and word index of the wildcard path. The two paths never run in the same compare (lk_cmp chooses one), and both reset what they use at their start (lk_cmp writes L0, L1, L2 = 0).
- **L3..L7** are lengths and the A key in the ordering compare, and p, t, star, mark, P in the matcher; same exclusivity. L3 is also the escape flag of the pattern tokenizer, which runs before any compare.
- **PC** is the compare phase (0: A vs B, 1: A vs best) for lk_cmp, the text loop and lk_upd, and the loader phase for lk_pt2 / lk_un2. The wildcard path only starts at PC 0 (wild needs !PC) and returns PC 0, so the loaders may use PC freely in between. Crosstalk tests: test_next_smaller_larger_text (PC 1 text compares), test_wildcards_forward (loaders and matcher).
- **T3** is the mode on entry and the result index on exit (lk_start copies M to P1 first).
