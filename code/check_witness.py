import sys
from bruteforce_verifier import kst_free

def main():
    if len(sys.argv) != 7:
        sys.exit('usage: check_witness.py m n s t k witness_file')
    m, n, s, t, k = map(int, sys.argv[1:6])
    with open(sys.argv[6]) as f:
        lits = [int(x) for x in f.read().split() if x not in ('v', '0')]
    true_cells = {l for l in lits if 0 < l <= m * n}
    mat = [[1 if r * n + c + 1 in true_cells else 0 for c in range(n)] for r in range(m)]
    ones = sum(map(sum, mat))
    free = kst_free(mat, m, n, s, t)
    for row in mat:
        print(''.join(map(str, row)))
    print(f'ones={ones} (want {k})  K_{{{s},{t}}}-free={free}')
    if ones == k and free:
        print(f'WITNESS OK: z({m},{n};{s},{t}) >= {k} confirmed independently')
        sys.exit(0)
    print('WITNESS BAD')
    sys.exit(1)
if __name__ == '__main__':
    main()
