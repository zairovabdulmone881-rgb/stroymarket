// Запись выпуска в mp4: node tools/render.js <дизайн> [выпуск] [выход.mp4] [fps]
// Кадры снимаются по одному (детерминированно), затем сводятся ffmpeg.
// Если в папке выпуска есть voice.mp3 — подкладывается как звук.
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const path = require("path"), fs = require("fs");
const [design = "3-kino", ep = "001-abu-bakr-as-siddiq", out = `out/${ep}--${design}.mp4`, fpsArg = "30"] = process.argv.slice(2);
const fps = +fpsArg;            // частота выходного видео
const cap = +(process.env.CAPTURE_FPS || 10); // частота съёмки кадров; промежуточные кадры дорисовывает ffmpeg
const root = path.resolve(__dirname, "..");
(async () => {
  fs.mkdirSync(path.dirname(path.resolve(root, out)), { recursive: true });
  const browser = await chromium.launch(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {});
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(`file://${root}/player.html?d=${design}&ep=${ep}&render=1`);
  await page.evaluate(() => document.fonts.ready);
  const total = await page.evaluate(() => window.TOTAL);
  const n = Math.round(total * cap);
  const voice = path.join(root, "episodes", ep, "voice.mp3"); // собирается tools/voice.py
  const audio = fs.existsSync(voice) ? ["-i", voice] : ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"];
  const ff = spawn(process.env.FFMPEG || "ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(cap), "-c:v", "mjpeg", "-i", "-",
    ...audio, "-map", "0:v", "-map", "1:a", "-shortest", "-vf", `fps=${fps}`, "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", path.resolve(root, out)], { stdio: ["pipe", "inherit", "inherit"] });
  for (let f = 0; f < n; f++) {
    await page.evaluate((t) => window.render(t), f / cap);
    const buf = await page.screenshot({ type: "jpeg", quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
    if (f % 300 === 0) console.log(`${ep}: ${f}/${n}`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on("close", r));
  await browser.close();
  console.log("готово:", out);
})();
