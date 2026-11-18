#!/bin/bash
# Записать mp4 для всех выпусков, у которых есть полная озвучка (timing.js), кроме уже записанных.
# bash tools/render_all.sh [число потоков]
cd "$(dirname "$0")/.." || exit 1
J=${1:-4}
ready=()
for d in episodes/*/; do
  e=$(basename "$d")
  [ -f "$d/timing.js" ] || continue
  n=$(grep -c '{ type:' "$d/episode.js"); v=$(ls "$d/voice"/*.mp3 2>/dev/null | wc -l)
  [ "$n" = "$v" ] || continue
  [ -s "out/$e.mp4" ] && [ "out/$e.mp4" -nt "$d/timing.js" ] && [ "out/$e.mp4" -nt "$d/episode.js" ] && continue
  ready+=("$e")
done
echo "К записи: ${#ready[@]} — ${ready[*]}"
mkdir -p out logs
printf '%s\n' "${ready[@]}" | xargs -P "$J" -I{} sh -c 'python3 tools/voice.py --mix "episodes/{}" && node tools/render.js 3-kino "{}" "out/{}.mp4.tmp.mp4" > "logs/{}.log" 2>&1 && mv "out/{}.mp4.tmp.mp4" "out/{}.mp4" && echo "готово: {}" || echo "ОШИБКА: {}"'
