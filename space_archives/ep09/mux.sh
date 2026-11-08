ffmpeg -y -loglevel error -i video_only.mp4 -i voice.wav -c:v copy -c:a aac -b:a 192k -shortest "$1"
