#!/usr/bin/env bash
# Проверка с нуля z(9,23;3,3)=103 (детерминированный эмит tan-кубов + пере-решение).
set -e; cd "$(dirname "$0")"
W=$(mktemp -d)
python3 ../../code/tan_split.py 9 23 3 3 104 --emit "$W"
python3 - "$W" <<'PY'
import json,sys
a=json.load(open(sys.argv[1]+"/manifest.json"))["cubes"]
b=json.load(open("manifest.json"))["cubes"]
assert a==b, "манифест разошёлся с регенерацией"
print(f"manifest identical: {len(a)} cubes")
PY
for f in "$W"/cube_*.cnf; do
  cadical --lrat=true --no-binary -q "$f" "$f.lrat" || [ $? -eq 20 ]
  lrat-check "$f" "$f.lrat" | grep -q "s VERIFIED"
done
python3 ../../code/check_witness.py 9 23 3 3 103 *.witness
echo "z(9,23;3,3) = 103  [все tan-кубы UNSAT@104 + свидетель@103]"
