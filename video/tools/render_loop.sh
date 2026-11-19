#!/bin/bash
# Фоновый цикл: записывает готовые выпуски по одному.
# Останавливается, когда появится файл out/STOP.
cd "$(dirname "$0")/.." || exit 1
while [ ! -f out/STOP ]; do
  while pgrep -f "tools/render.js" >/dev/null; do sleep 20; done
  git pull -q --no-rebase --no-edit >/dev/null 2>&1
  out=$(bash tools/render_all.sh 1)
  echo "$(date +%H:%M) $out" | tail -n 3
  echo "$out" | grep -q "К записи: 0" && sleep 60
done
