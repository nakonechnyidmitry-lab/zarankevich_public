#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
W=$(mktemp -d)
python3 ../../code/tan_split.py 12 21 3 3 127 --emit "$W"
python3 - "$W" <<'PY'
import json, sys
a = json.load(open(sys.argv[1] + "/manifest.json"))
b = json.load(open("manifest.json"))
assert a["instance"] == b["instance"] and a["cubes"] == b["cubes"]
print("manifest: identical partition,", len(a["cubes"]), "cubes")
PY
for f in "$W"/cube_*.cnf; do
  cadical --lrat=true --no-binary -q "$f" "$f.lrat" || [ $? -eq 20 ]
  lrat-check "$f" "$f.lrat" | grep -q "c VERIFIED"
  echo "$(basename "$f") UNSAT verified"
done
python3 ../../code/check_witness.py 12 21 3 3 126 z12-21_geq126.witness
echo "z(12,21;3,3) = 126"
