import sys
from itertools import product
from bruteforce_verifier import kst_free, dpll
from tan_split import cubes, build_cube_cnf, exactly, lex_ge, nonincr, kst_count_ok, gale_ryser_ok
ok = True

def check(flag, label):
    global ok
    ok = ok and flag
    print(f"  {label}: {('OK' if flag else 'FAIL')}")

def profile_of(mat, m, n):
    R = tuple(sorted((sum(row) for row in mat), reverse=True))
    C = tuple(sorted((sum((mat[i][j] for i in range(m))) for j in range(n)), reverse=True))
    return (R, C)

def matrices_with_k(m, n, s, t, k):
    for bits in product((0, 1), repeat=m * n):
        if sum(bits) != k:
            continue
        mat = [bits[i * n:(i + 1) * n] for i in range(m)]
        if kst_free(mat, m, n, s, t):
            yield mat

def solve_cube(m, n, s, t, k, desc, lex):
    cl, nv = build_cube_cnf(m, n, s, t, k, R=desc.get('R'), C=desc.get('C'), prefix=desc.get('prefix'), lex=lex)
    return dpll(cl, nv)
print('=== (1) exactly(): exhaustive popcount check ===')
for N, r in [(4, 2), (5, 0), (5, 5), (6, 3)]:
    good = True
    xvars = list(range(1, N + 1))
    cl, _ = exactly(xvars, r, N + 1)
    for bits in product((0, 1), repeat=N):
        units = [[i + 1 if bits[i] else -(i + 1)] for i in range(N)]
        mx = max([N] + [abs(l) for c in cl for l in c])
        if dpll(cl + units, mx) != (sum(bits) == r):
            good = False
            break
    check(good, f'exactly({N},{r})')
print('=== (2) lex_ge(): exhaustive equivalence with >=lex ===')
for L in (2, 3, 4):
    good = True
    A = list(range(1, L + 1))
    B = list(range(L + 1, 2 * L + 1))
    cl, nv = lex_ge(A, B, 2 * L + 1)
    for abits in product((0, 1), repeat=L):
        for bbits in product((0, 1), repeat=L):
            units = [[A[i]] if abits[i] else [-A[i]] for i in range(L)] + [[B[i]] if bbits[i] else [-B[i]] for i in range(L)]
            want = list(abits) >= list(bbits)
            if dpll(cl + units, nv - 1) != want:
                good = False
    check(good, f'lex_ge, vectors of length {L}')
CASES = [(2, 3, 2, 2), (3, 3, 2, 2), (3, 4, 2, 2), (4, 4, 3, 3)]
MODES = [('rowsfull', None), ('both', None), ('prefix', 2)]
print('=== (3) enumeration completeness (coverage lemma guard) ===')
for m, n, s, t in CASES:
    for k in range(1, m * n + 1):
        mats = list(matrices_with_k(m, n, s, t, k))
        if not mats:
            continue
        for mode, depth in MODES:
            cube_list = list(cubes(m, n, s, t, k, mode, depth))
            if mode == 'rowsfull':
                have = {d['R'] for d in cube_list}
                need = {profile_of(mat, m, n)[0] for mat in mats}
            elif mode == 'both':
                have = {(d['R'], d['C']) for d in cube_list}
                need = {profile_of(mat, m, n) for mat in mats}
            else:
                have = {d['prefix'] for d in cube_list}
                need = {profile_of(mat, m, n)[0][:depth] for mat in mats}
            if not need <= have:
                check(False, f'({m},{n};{s},{t}) k={k} mode={mode}')
                break
        else:
            continue
        break
    else:
        check(True, f'({m},{n};{s},{t}) all k, all modes')
print('=== (4) OR-over-cubes == brute-force existence, lex on/off ===')
for m, n, s, t in CASES:
    good = True
    for k in range(1, m * n + 1):
        exists = any((True for _ in matrices_with_k(m, n, s, t, k)))
        for mode, depth in MODES:
            for lex in (False, True):
                got = any((solve_cube(m, n, s, t, k, d, lex) for d in cubes(m, n, s, t, k, mode, depth)))
                if got != exists:
                    print(f'    MISMATCH ({m},{n};{s},{t}) k={k} mode={mode} lex={lex}: cubes={got} bf={exists}')
                    good = False
    check(good, f'({m},{n};{s},{t})')
print('=== (5) mini-gate: z(4,4;3,3)=13 via the split ===')
for mode, depth in MODES:
    sat13 = any((solve_cube(4, 4, 3, 3, 13, d, True) for d in cubes(4, 4, 3, 3, 13, mode, depth)))
    uns14 = not any((solve_cube(4, 4, 3, 3, 14, d, True) for d in cubes(4, 4, 3, 3, 14, mode, depth)))
    check(sat13 and uns14, f'mode={mode}: SAT@13 and UNSAT@14')
print('\nALL', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
