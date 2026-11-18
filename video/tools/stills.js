// Контрольные кадры: node tools/stills.js <дизайн> <выпуск> <папка> [t1 t2 ...]
// Без времён — по одному снимку из середины каждого кадра (когда текст уже проявился).
const { chromium } = require("playwright");
const path = require("path");
const [design, ep, dir, ...ts] = process.argv.slice(2);
const root = path.resolve(__dirname, "..");
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on("pageerror", (e) => console.log("ERR", e.message));
  await p.goto(`file://${root}/player.html?d=${design}&ep=${ep}&render=1`);
  await p.evaluate(() => document.fonts.ready);
  const times = ts.length ? ts.map(Number) : await p.evaluate(() => window.EPISODE.frames.map((f) => f.start + Math.min(f.duration - 0.6, 3.5)));
  let k = 0;
  for (const t of times) { await p.evaluate((t) => window.render(t), t); await p.screenshot({ path: `${dir}/${ep}-${String(++k).padStart(2, "0")}.png` }); }
  await b.close();
})();
