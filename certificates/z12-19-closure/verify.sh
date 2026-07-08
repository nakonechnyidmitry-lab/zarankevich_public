#!/usr/bin/env bash
# Самодостаточная проверка z(12,19;3,3)=114.
# Вариант A (быстрый, из архива): для каждой пары cube_X.cnf.xz + cube_X.lrat.xz
#   из пакета z12-19-closure-v2: unxz оба, lrat-check <cnf> <lrat> -> c VERIFIED.
#   Все 222 куба UNSAT => z<=114. Хэши пакета в SHA256SUMS.replayable.
# Вариант B (с нуля): регенерировать кубы и пере-решить.
set -e
cd "$(dirname "$0")"
echo "== вариант B: регенерация + пере-решение (детерминированный эмит) =="
W=$(mktemp -d)
python3 ../../code/tan_split.py 12 19 3 3 115 --emit "$W"
python3 - "$W" <<'PY'
import json,sys
a=json.load(open(sys.argv[1]+"/manifest.json"))["cubes"]
b=json.load(open("manifest.json"))["cubes"]
assert a==b, "манифест разошёлся с регенерацией"
print(f"manifest: identical, {len(a)} cubes")
PY
for f in "$W"/cube_*.cnf; do
  cadical --lrat=true --no-binary -q "$f" "$f.lrat" || [ $? -eq 20 ]
  lrat-check "$f" "$f.lrat" | grep -q "c VERIFIED"
done
python3 ../../code/check_witness.py 12 19 3 3 114 z12-19_geq114.witness
echo "z(12,19;3,3) = 114  [222 куба UNSAT@115 + свидетель@114]"
