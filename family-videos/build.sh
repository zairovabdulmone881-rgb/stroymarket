#!/bin/bash
# ./build.sh <id>  — рендер 900 кадров + сборка mp4 (720x1280, 30 fps, ровно 30 с) со звуком шаблона
set -e
cd "$(dirname "$0")"
export NODE_PATH=$(npm root -g)
id=$1
rm -rf frames/$id && mkdir -p frames/$id out
node src/render.js $id frames/$id
ffmpeg -v error -y -framerate 30 -i frames/$id/f_%04d.jpg -i src/audio_template.m4a \
  -c:v libx264 -crf 17 -pix_fmt yuv420p -preset medium -c:a aac -b:a 128k -t 30 -movflags +faststart out/$id.mp4
rm -rf frames/$id
echo "OK $id"
