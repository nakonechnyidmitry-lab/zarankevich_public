import sys
from itertools import product
from zarankiewicz_encoder import build_cnf, no_kst_clauses, atleast_clauses
from bruteforce_verifier import zarankiewicz, kst_free, dpll

def z_via_sat(m, n, s, t):
    for k in range(m * n, -1, -1):
        cl, nv = build_cnf(m, n, s, t, k)
        if dpll(cl, nv):
            return k
    return 0

def test_equiv_nokst(m, n, s, t):
    cl = no_kst_clauses(m, n, s, t)
    for bits in product((0, 1), repeat=m * n):
        assign = {i + 1: bool(bits[i]) for i in range(m * n)}
        sat_all = all((any((assign[abs(l)] == (l > 0) for l in c)) for c in cl))
        mat = [bits[i * n:(i + 1) * n] for i in range(m)]
        if sat_all != kst_free(mat, m, n, s, t):
            return False
    return True

def test_cardinality(N, k):
    xvars = list(range(1, N + 1))
    cl, _ = atleast_clauses(xvars, k, N + 1)
    mx = N
    for c in cl:
        for l in c:
            mx = max(mx, abs(l))
    for bits in product((0, 1), repeat=N):
        units = [[i + 1 if bits[i] else -(i + 1)] for i in range(N)]
        if dpll(cl + units, mx) != (sum(bits) >= k):
            return False
    return True
KNOWN = {(2, 2, 2, 2): 3, (3, 3, 2, 2): 6, (4, 4, 2, 2): 9}
CASES = [(2, 2, 2, 2), (2, 3, 2, 2), (3, 3, 2, 2), (3, 4, 2, 2), (4, 4, 2, 2), (3, 3, 3, 3), (4, 4, 3, 3)]
ok = True
print('=== (1) encoder (max-k SAT) vs brute-force z ===')
for m, n, s, t in CASES:
    zbf = zarankiewicz(m, n, s, t)
    zst = z_via_sat(m, n, s, t)
    tag = 'OK' if zbf == zst else 'FAIL'
    lit = ''
    if (m, n, s, t) in KNOWN:
        good = KNOWN[m, n, s, t] == zbf
        lit = f"  (literature={KNOWN[m, n, s, t]} {('OK' if good else 'MISMATCH')})"
        ok = ok and good
    ok = ok and zbf == zst
    print(f'  z({m},{n};{s},{t}): brute={zbf}  sat={zst}  [{tag}]{lit}')
print('=== (2) no-K_{s,t} clause <-> kst_free equivalence (exhaustive) ===')
for m, n, s, t in [(3, 3, 2, 2), (3, 3, 3, 3), (3, 4, 2, 2)]:
    r = test_equiv_nokst(m, n, s, t)
    ok = ok and r
    print(f"  ({m},{n};{s},{t}): {('OK' if r else 'FAIL')}")
print('=== (3) at-least-k cardinality encoding (exhaustive) ===')
for N, k in [(5, 3), (6, 4), (6, 0), (6, 6), (7, 2)]:
    r = test_cardinality(N, k)
    ok = ok and r
    print(f"  atleast({N},{k}): {('OK' if r else 'FAIL')}")
print('\nALL', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
