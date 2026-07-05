from itertools import combinations, product

def kst_free(mat, m, n, s, t):
    for R in combinations(range(m), s):
        common = [c for c in range(n) if all((mat[r][c] for r in R))]
        if len(common) >= t:
            return False
    return True

def zarankiewicz(m, n, s, t):
    best = 0
    for bits in product((0, 1), repeat=m * n):
        e = sum(bits)
        if e <= best:
            continue
        mat = [bits[i * n:(i + 1) * n] for i in range(m)]
        if kst_free(mat, m, n, s, t):
            best = e
    return best

def dpll(clauses, nvars):

    def simplify(assign):
        out = []
        for cl in clauses:
            keep = []
            sat = False
            for lit in cl:
                v = abs(lit)
                if v in assign:
                    if assign[v] == (lit > 0):
                        sat = True
                        break
                else:
                    keep.append(lit)
            if sat:
                continue
            if not keep:
                return None
            out.append(keep)
        return out

    def solve(assign):
        assign = dict(assign)
        while True:
            cur = simplify(assign)
            if cur is None:
                return False
            if not cur:
                return True
            unit = next((c for c in cur if len(c) == 1), None)
            if unit is None:
                break
            lit = unit[0]
            assign[abs(lit)] = lit > 0
        lit = cur[0][0]
        v = abs(lit)
        a = dict(assign)
        a[v] = True
        if solve(a):
            return True
        a = dict(assign)
        a[v] = False
        return solve(a)
    return solve({})
