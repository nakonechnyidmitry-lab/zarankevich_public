from itertools import combinations

def cell_var(r, c, n):
    return r * n + c + 1

def no_kst_clauses(m, n, s, t):
    clauses = []
    for R in combinations(range(m), s):
        for C in combinations(range(n), t):
            clauses.append([-cell_var(r, c, n) for r in R for c in C])
    return clauses

def _atmost_seq(lits, r, next_var):
    N = len(lits)
    if r <= 0:
        return ([[-l] for l in lits], next_var)
    s = [[0] * r for _ in range(N)]
    for i in range(N):
        for j in range(r):
            s[i][j] = next_var
            next_var += 1
    clauses = [[-lits[0], s[0][0]]]
    for j in range(1, r):
        clauses.append([-s[0][j]])
    for i in range(1, N - 1):
        clauses.append([-lits[i], s[i][0]])
        clauses.append([-s[i - 1][0], s[i][0]])
        for j in range(1, r):
            clauses.append([-lits[i], -s[i - 1][j - 1], s[i][j]])
            clauses.append([-s[i - 1][j], s[i][j]])
        clauses.append([-lits[i], -s[i - 1][r - 1]])
    clauses.append([-lits[N - 1], -s[N - 2][r - 1]])
    return (clauses, next_var)

def atleast_clauses(xvars, k, next_var):
    N = len(xvars)
    if k <= 0:
        return ([], next_var)
    if k > N:
        return ([[]], next_var)
    return _atmost_seq([-v for v in xvars], N - k, next_var)

def build_cnf(m, n, s, t, k):
    xvars = [cell_var(r, c, n) for r in range(m) for c in range(n)]
    next_var = m * n + 1
    clauses = no_kst_clauses(m, n, s, t)
    card, next_var = atleast_clauses(xvars, k, next_var)
    return (clauses + card, next_var - 1)

def to_dimacs(clauses, nvars):
    lines = [f'p cnf {nvars} {len(clauses)}']
    lines += [' '.join(map(str, cl)) + ' 0' for cl in clauses]
    return '\n'.join(lines) + '\n'

def stats(m, n, s, t, k):
    cl, nv = build_cnf(m, n, s, t, k)
    return {'m': m, 'n': n, 's': s, 't': t, 'k': k, 'vars': nv, 'clauses': len(cl)}
if __name__ == '__main__':
    import sys
    m, n, s, t, k = map(int, sys.argv[1:6])
    cl, nv = build_cnf(m, n, s, t, k)
    sys.stdout.write(to_dimacs(cl, nv))
