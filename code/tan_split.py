from fractions import Fraction
from itertools import combinations
from math import comb
from zarankiewicz_encoder import cell_var, no_kst_clauses, _atmost_seq

def _roman1(s, t, m, n):
    f = lambda p: int(Fraction(t - 1, comb(p, s - 1)) * comb(m, s) + Fraction((p + 1) * (s - 1), s) * n)
    p = s - 1
    prev = f(p)
    while True:
        nxt = f(p + 1)
        if nxt >= prev:
            return prev
        prev = nxt
        p += 1

def roman_ub(s, t, m, n):
    return min(_roman1(s, t, m, n), _roman1(t, s, n, m))

def zub(s, t, m, n, table=None):
    if s > m or t > n:
        return m * n
    ub = roman_ub(s, t, m, n)
    if table:
        ub = min(ub, table.get((m, n), ub), table.get((n, m), ub))
    return ub

def nonincr(total, parts, hi):
    if parts == 0:
        if total == 0:
            yield ()
        return
    lo = -(-total // parts)
    for v in range(min(hi, total), lo - 1, -1):
        for rest in nonincr(total - v, parts - 1, v):
            yield ((v,) + rest)

def kst_count_ok(profile, opposite, need, size):
    return sum((comb(p, size) for p in profile)) <= (need - 1) * comb(opposite, size)

def gale_ryser_ok(R, C):
    for t in range(1, len(C) + 1):
        if sum(C[:t]) > sum((min(r, t) for r in R)):
            return False
    return True

def arg_i_ok(profile, s, t, other, table=None):
    run = 0
    for j, p in enumerate(profile, 1):
        run += p
        if j < len(profile) and run > zub(s, t, j, other, table):
            return False
    return True

def arg_d_ok(R, C, s, t):
    m, n = (len(R), len(C))
    if R[0] > 0:
        nz = [c for c in C if c > 0]
        if len(nz) < R[0]:
            return False
        if sum((comb(c - 1, s - 1) for c in nz[-R[0]:])) > (t - 1) * comb(m - 1, s - 1):
            return False
    if C[0] > 0:
        nz = [r for r in R if r > 0]
        if len(nz) < C[0]:
            return False
        if sum((comb(r - 1, t - 1) for r in nz[-C[0]:])) > (s - 1) * comb(n - 1, t - 1):
            return False
    return True

def prefix_feasible(prefix, m, n, k, s, t):
    d = len(prefix)
    rem = k - sum(prefix)
    if rem < 0:
        return False
    cap = prefix[-1] if d else n
    free = m - d
    if rem > free * cap:
        return False
    if free and rem >= 0:
        q, r = divmod(rem, free)
        min_free = r * comb(q + 1, t) + (free - r) * comb(q, t)
    else:
        min_free = 0
    return sum((comb(p, t) for p in prefix)) + min_free <= (s - 1) * comb(n, t)

def cubes(m, n, s, t, k, mode='rowsfull', depth=None, table=None):
    if mode == 'rowsfull':
        for R in nonincr(k, m, n):
            if kst_count_ok(R, n, s, t) and arg_i_ok(R, s, t, n, table):
                yield {'R': R}
    elif mode == 'both':
        Cs = [C for C in nonincr(k, n, m) if kst_count_ok(C, m, t, s) and arg_i_ok(C, t, s, m, table)]
        for R in nonincr(k, m, n):
            if not (kst_count_ok(R, n, s, t) and arg_i_ok(R, s, t, n, table)):
                continue
            for C in Cs:
                if arg_d_ok(R, C, s, t) and gale_ryser_ok(R, C):
                    yield {'R': R, 'C': C}
    elif mode == 'prefix':
        if not depth or not 0 < depth <= m:
            raise ValueError('prefix mode needs --depth in 1..m')
        for p in nonincr_prefix(k, depth, n, m, s, t):
            if arg_i_ok(p, s, t, n, table):
                yield {'prefix': p}
    else:
        raise ValueError(f'unknown mode {mode!r}')

def nonincr_prefix(k, depth, n, m, s, t):

    def rec(prefix, budget, hi):
        if len(prefix) == depth:
            if prefix_feasible(prefix, m, n, k, s, t):
                yield tuple(prefix)
            return
        for v in range(min(hi, budget), -1, -1):
            prefix.append(v)
            yield from rec(prefix, budget - v, v)
            prefix.pop()
    yield from rec([], k, n)

def atmost(lits, r, next_var):
    if r >= len(lits):
        return ([], next_var)
    return _atmost_seq(lits, r, next_var)

def exactly(lits, r, next_var):
    if r < 0 or r > len(lits):
        return ([[]], next_var)
    cls_hi, next_var = atmost(lits, r, next_var)
    cls_lo, next_var = atmost([-l for l in lits], len(lits) - r, next_var)
    return (cls_hi + cls_lo, next_var)

def lex_ge(A, B, next_var):
    cls = [[A[0], -B[0]]]
    e_prev = None
    for i in range(1, len(A)):
        e = next_var
        next_var += 1
        if e_prev is None:
            cls.append([-A[0], -B[0], e])
            cls.append([A[0], B[0], e])
        else:
            cls.append([-e_prev, -A[i - 1], -B[i - 1], e])
            cls.append([-e_prev, A[i - 1], B[i - 1], e])
        cls.append([-e, A[i], -B[i]])
        e_prev = e
    return (cls, next_var)

def build_cube_cnf(m, n, s, t, k, R=None, C=None, prefix=None, lex=True):
    if (R is None) == (prefix is None):
        raise ValueError('give exactly one of R= / prefix=')
    rows = [[cell_var(i, c, n) for c in range(n)] for i in range(m)]
    cols = [[cell_var(r, j, n) for r in range(m)] for j in range(n)]
    clauses = no_kst_clauses(m, n, s, t)
    nv = m * n + 1
    if R is not None:
        assert sum(R) == k and all((R[i] >= R[i + 1] for i in range(m - 1)))
        for i, r in enumerate(R):
            cl, nv = exactly(rows[i], r, nv)
            clauses += cl
    else:
        d = len(prefix)
        for i, r in enumerate(prefix):
            cl, nv = exactly(rows[i], r, nv)
            clauses += cl
        cap = prefix[-1] if d else n
        for i in range(d, m):
            cl, nv = atmost(rows[i], cap, nv)
            clauses += cl
        free_cells = [v for i in range(d, m) for v in rows[i]]
        cl, nv = exactly(free_cells, k - sum(prefix), nv)
        clauses += cl
    if C is not None:
        assert sum(C) == k and all((C[j] >= C[j + 1] for j in range(n - 1)))
        for j, c in enumerate(C):
            cl, nv = exactly(cols[j], c, nv)
            clauses += cl
    if lex:
        prof = R if R is not None else prefix
        for i in range(len(prof) - 1):
            if prof[i] == prof[i + 1]:
                cl, nv = lex_ge(rows[i], rows[i + 1], nv)
                clauses += cl
        if C is not None:
            for j in range(n - 1):
                if C[j] == C[j + 1]:
                    cl, nv = lex_ge(cols[j], cols[j + 1], nv)
                    clauses += cl
        else:
            for j in range(n - 1):
                cl, nv = lex_ge(cols[j], cols[j + 1], nv)
                clauses += cl
    return (clauses, nv - 1)

def to_dimacs(clauses, nvars):
    lines = [f'p cnf {nvars} {len(clauses)}']
    lines += [' '.join(map(str, cl)) + ' 0' for cl in clauses]
    return '\n'.join(lines) + '\n'

def _cube_cnf_from_desc(m, n, s, t, k, desc, lex):
    return build_cube_cnf(m, n, s, t, k, R=desc.get('R'), C=desc.get('C'), prefix=desc.get('prefix'), lex=lex)
if __name__ == '__main__':
    import argparse
    import json
    import os
    import sys
    ap = argparse.ArgumentParser(description='Tan-style sum-profile split')
    ap.add_argument('m', type=int)
    ap.add_argument('n', type=int)
    ap.add_argument('s', type=int)
    ap.add_argument('t', type=int)
    ap.add_argument('k', type=int)
    ap.add_argument('--mode', choices=['rowsfull', 'both', 'prefix'], default='rowsfull')
    ap.add_argument('--depth', type=int, default=None, help='prefix length for --mode prefix')
    ap.add_argument('--count', action='store_true', help='only count cubes (streams; prints every 100k)')
    ap.add_argument('--emit', metavar='DIR', help='write cube_NNNNNN.cnf files + manifest.json')
    ap.add_argument('--limit', type=int, default=None, help='stop after this many cubes (smoke tests)')
    ap.add_argument('--no-lex', action='store_true', help='disable partitioned double-lex clauses')
    a = ap.parse_args()
    gen = cubes(a.m, a.n, a.s, a.t, a.k, a.mode, a.depth)
    if a.count:
        cnt = 0
        first = None
        for d in gen:
            if first is None:
                first = d
            cnt += 1
            if a.limit and cnt >= a.limit:
                print(f'(stopped at --limit {a.limit})')
                break
            if cnt % 100000 == 0:
                print(f'... {cnt}', file=sys.stderr)
        print(f'cubes: {cnt}')
        if first:
            cl, nv = _cube_cnf_from_desc(a.m, a.n, a.s, a.t, a.k, first, not a.no_lex)
            print(f'first cube {first}: {nv} vars, {len(cl)} clauses')
        sys.exit(0)
    if a.emit:
        os.makedirs(a.emit, exist_ok=True)
        manifest = {'instance': [a.m, a.n, a.s, a.t, a.k], 'mode': a.mode, 'depth': a.depth, 'lex': not a.no_lex, 'cubes': []}
        for i, d in enumerate(gen):
            if a.limit and i >= a.limit:
                break
            cl, nv = _cube_cnf_from_desc(a.m, a.n, a.s, a.t, a.k, d, not a.no_lex)
            name = f'cube_{i:06d}.cnf'
            with open(os.path.join(a.emit, name), 'w') as f:
                f.write(to_dimacs(cl, nv))
            manifest['cubes'].append({'file': name, **{key: list(v) for key, v in d.items()}})
        with open(os.path.join(a.emit, 'manifest.json'), 'w') as f:
            json.dump(manifest, f, indent=1)
        print(f"emitted {len(manifest['cubes'])} cubes -> {a.emit}/")
        sys.exit(0)
    ap.error('choose --count or --emit DIR')
