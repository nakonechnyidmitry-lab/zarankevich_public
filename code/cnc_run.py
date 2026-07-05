import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def find_tool(name, explicit, fallbacks):
    if explicit:
        return explicit
    p = shutil.which(name)
    if p:
        return p
    for f in fallbacks:
        f = os.path.expanduser(f)
        if os.path.exists(f):
            return f
    sys.exit(f'cannot find {name}; pass --{name}')

def run_cube(cnf, cadical, lratcheck, keep_proofs, stop=None, cube_timeout=None):
    base = cnf[:-4]
    verdict_path = base + '.verdict'
    if os.path.exists(verdict_path):
        with open(verdict_path) as f:
            return json.load(f)
    if stop is not None and stop.is_set():
        return {'cnf': os.path.basename(cnf), 'status': 'SKIPPED'}
    lrat = base + '.lrat'
    t0 = time.time()
    try:
        r = subprocess.run([cadical, '--lrat=true', '--no-binary', '-q', cnf, lrat], capture_output=True, text=True, timeout=cube_timeout)
    except subprocess.TimeoutExpired:
        v = {'cnf': os.path.basename(cnf), 'status': 'TIMEOUT', 'solve_s': round(time.time() - t0, 2)}
        with open(verdict_path, 'w') as f:
            json.dump(v, f)
        return v
    solve_s = round(time.time() - t0, 2)
    v = {'cnf': os.path.basename(cnf), 'solve_s': solve_s, 'rc': r.returncode}
    if r.returncode == 20:
        c = subprocess.run([lratcheck, cnf, lrat], capture_output=True, text=True)
        verified = 'c VERIFIED' in c.stdout + c.stderr
        v.update(status='UNSAT', verified=verified, lrat_bytes=os.path.getsize(lrat) if os.path.exists(lrat) else 0)
        if not keep_proofs and verified:
            os.remove(lrat)
    elif r.returncode == 10:
        w = subprocess.run([cadical, cnf], capture_output=True, text=True)
        model = ' '.join((line[2:] for line in w.stdout.splitlines() if line.startswith('v ')))
        v.update(status='SAT', witness=model)
        with open(base + '.witness', 'w') as f:
            f.write(model + '\n')
    else:
        v.update(status='ERROR', stderr=r.stderr[-500:])
    with open(verdict_path, 'w') as f:
        json.dump(v, f)
    return v

def main():
    ap = argparse.ArgumentParser(description='CnC runner over emitted cubes')
    ap.add_argument('cubedir', help='directory produced by tan_split.py --emit')
    ap.add_argument('--jobs', type=int, default=max(1, os.cpu_count() - 2), help='parallel solvers (default: cores-2, keeps the calibration gate breathing)')
    ap.add_argument('--cadical', default=None)
    ap.add_argument('--lrat-check', dest='lratcheck', default=None)
    ap.add_argument('--keep-proofs', action='store_true', help='keep every .lrat (default: drop after verification; re-derivable by re-running that cube)')
    ap.add_argument('--stop-on-sat', action='store_true', help='witness hunt: stop dispatching once any cube is SAT (running solvers finish their current cube)')
    ap.add_argument('--cube-timeout', type=float, default=None, help='per-cube solver timeout in seconds; timed-out cubes make the verdict INCOMPLETE (delete their .verdict files to retry)')
    a = ap.parse_args()
    cadical = find_tool('cadical', a.cadical, ['~/tools/cadical/build/cadical'])
    lratcheck = find_tool('lrat-check', a.lratcheck, ['~/tools/drat-trim/lrat-check'])
    with open(os.path.join(a.cubedir, 'manifest.json')) as f:
        manifest = json.load(f)
    cnfs = [os.path.join(a.cubedir, c['file']) for c in manifest['cubes']]
    print(f"instance {manifest['instance']}  mode={manifest['mode']}  cubes={len(cnfs)}  jobs={a.jobs}")
    stop = threading.Event() if a.stop_on_sat else None
    results, t0 = ([], time.time())
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futs = {pool.submit(run_cube, c, cadical, lratcheck, a.keep_proofs, stop, a.cube_timeout): c for c in cnfs}
        for i, fut in enumerate(as_completed(futs), 1):
            v = fut.result()
            results.append(v)
            if v['status'] == 'SAT' and stop is not None:
                stop.set()
            if v['status'] not in ('UNSAT', 'SKIPPED') or not v.get('verified', True):
                print(f"  [{i}/{len(cnfs)}] {v['cnf']}: {v['status']}{('' if v.get('verified', True) else ' NOT-VERIFIED')}")
            if i % 50 == 0 or i == len(cnfs):
                el = time.time() - t0
                eta = el / i * (len(cnfs) - i)
                print(f'  progress {i}/{len(cnfs)}  elapsed {el:.0f}s  ETA {eta:.0f}s', flush=True)
    sat = [v for v in results if v['status'] == 'SAT']
    skipped = [v for v in results if v['status'] == 'SKIPPED']
    timeouts = [v for v in results if v['status'] == 'TIMEOUT']
    bad = [v for v in results if v['status'] == 'ERROR' or (v['status'] == 'UNSAT' and (not v['verified']))]
    summary = {'instance': manifest['instance'], 'mode': manifest['mode'], 'cubes': len(cnfs), 'sat': len(sat), 'errors': len(bad), 'skipped': len(skipped), 'timeouts': len(timeouts), 'wall_s': round(time.time() - t0, 1), 'solve_s_total': round(sum((v.get('solve_s', 0) for v in results)), 1)}
    if sat:
        summary['verdict'] = f"SAT at k={manifest['instance'][4]} (witness: {sat[0]['cnf']})"
    elif bad:
        summary['verdict'] = 'INCOMPLETE (errors/unverified cubes)'
    elif timeouts:
        summary['verdict'] = f'INCOMPLETE ({len(timeouts)} cube timeouts, no SAT found)'
    elif skipped:
        summary['verdict'] = 'INCOMPLETE (skipped cubes, no SAT found)'
    else:
        summary['verdict'] = f"UNSAT at k={manifest['instance'][4]}: all {len(cnfs)} cubes UNSAT, every LRAT verified"
    with open(os.path.join(a.cubedir, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))
    sys.exit(0 if not (bad or timeouts) else 2)
if __name__ == '__main__':
    main()
