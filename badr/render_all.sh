cd /home/user/stroymarket/badr
for st in vector paper iso; do
  rm -f ${st}_seg_*.mp4
  for k in 0 1 2 3; do python3 run_style.py $st render $k 4 > ${st}_$k.log 2>&1 & done
  wait
  printf "file ${st}_seg_0.mp4\nfile ${st}_seg_1.mp4\nfile ${st}_seg_2.mp4\nfile ${st}_seg_3.mp4\n" > ${st}_list.txt
  ffmpeg -y -loglevel error -f concat -safe 0 -i ${st}_list.txt -c copy ${st}_video_only.mp4
  ffmpeg -y -loglevel error -i ${st}_video_only.mp4 -i voice.wav -c:v copy -c:a aac -b:a 192k -shortest badr_${st}.mp4
  echo $st >> /tmp/styles_done
done
