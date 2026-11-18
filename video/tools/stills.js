// Контрольные кадры: node tools/stills.js <дизайн> <папка> t1 t2 ...
const { chromium } = require("playwright");
const path = require("path");
const [design, dir, ...ts] = process.argv.slice(2);
const root = path.resolve(__dirname, "..");
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on("pageerror", (e) => console.log("ERR", e.message));
  await p.goto(`file://${root}/player.html?d=${design}&render=1`);
  await p.evaluate(() => document.fonts.ready);
  for (const t of ts) { await p.evaluate((t) => window.render(t), +t); await p.screenshot({ path: `${dir}/${design}-${t}.png` }); }
  await b.close();
})();
