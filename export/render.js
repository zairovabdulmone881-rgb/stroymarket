#!/usr/bin/env node
/**
 * Экспорт HTML-анимации в MP4 (покадровый рендер, не зависит от скорости компьютера).
 *
 *   node export/render.js <анимация.html> <секунды> <выход.mp4> [аудио.wav] [fps=30] [потоки=4]
 *   пример: node export/render.js heist-animation.html 12 videos/heist.mp4 audio/heist.wav
 *
 * Требуется: Node.js 18+, `npm i playwright` (+ `npx playwright install chromium`), ffmpeg в PATH.
 * Страница должна отдавать window.seek(секунда) и иметь элемент #stage размером 1080×1920.
 */
const { chromium } = require('playwright');
const fs = require('fs'), os = require('os'), path = require('path');
const { execFileSync } = require('child_process');

const [html, dur, out, audio, fpsArg, thrArg] = process.argv.slice(2);
if (!html || !dur || !out) { console.error('usage: node export/render.js <html> <seconds> <out.mp4> [audio.wav] [fps] [threads]'); process.exit(1); }
const FPS = +(fpsArg || 30), THREADS = +(thrArg || 4), N = Math.round(+dur * FPS);
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'frames-'));

(async () => {
  const browser = await chromium.launch();
  const worker = async (w) => {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1970 }, deviceScaleFactor: 1 });
    await page.goto('file://' + path.resolve(html));
    await page.addStyleTag({ content: '#ui{display:none!important}' });
    for (let i = w; i < N; i += THREADS) {
      await page.evaluate(t => window.seek(t), i / FPS);
      await page.locator('#stage').screenshot({ path: `${dir}/f${String(i).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 93 });
    }
  };
  await Promise.all(Array.from({ length: THREADS }, (_, w) => worker(w)));
  await browser.close();

  fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
  const args = ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', `${dir}/f%05d.jpg`];
  if (audio) args.push('-i', audio);
  args.push('-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18');
  if (audio) args.push('-c:a', 'aac', '-b:a', '192k', '-shortest');
  args.push('-movflags', '+faststart', out);
  execFileSync('ffmpeg', args, { stdio: 'inherit' });
  fs.rmSync(dir, { recursive: true, force: true });
  console.log('готово:', out);
})();
