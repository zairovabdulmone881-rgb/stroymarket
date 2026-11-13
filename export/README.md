# Экспорт анимации в MP4

1. Установить: Node.js 18+, ffmpeg, затем `npm i playwright && npx playwright install chromium`
2. (Звук, по желанию) `python3 -m pip install numpy && python3 audio/make_audio_heist.py` → `audio/heist.wav`
3. Рендер:
   ```
   node export/render.js heist-animation.html 12 videos/heist-sound.mp4 audio/heist.wav
   ```
   Без звука — не указывайте последний аргумент. Результат: 1080×1920, 30 fps, H.264 + AAC.

Серия «Снаружи / Внутри»: `node export/render.js "masks-animation.html?v=1" 20 videos/perfect-family.mp4 audio/perfect-family.wav` (v=2 — «Успешный человек»).

Предпросмотр: просто откройте `heist-animation.html` в браузере.
Тайминги всех сцен — в объекте `T` в начале скрипта страницы.
