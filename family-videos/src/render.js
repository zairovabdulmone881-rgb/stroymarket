// node render.js <id> <outDir> [times,comma] [--sheet]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [id, outDir, times] = process.argv.slice(2);
  fs.mkdirSync(outDir, { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 720, height: 1280 } });
  p.on('pageerror', e => { console.error('PAGEERR', e.message); });
  p.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()); });
  await p.goto('file://' + path.resolve(__dirname, 'index.html'));
  await p.waitForFunction('window.__ready');
  await p.evaluate(() => document.fonts.load('800 20px Inter'));
  const list = times ? times.split(',').map(Number) : null;
  const n = 900;
  const frames = list ? list.map(t => Math.round(t * 30)) : Array.from({ length: n }, (_, i) => i);
  for (const i of frames) {
    const data = await p.evaluate(([id, i]) => { window.__frame(i / 30, SCN[id]); return document.getElementById('c').toDataURL('image/jpeg', 0.95); }, [id, i]);
    fs.writeFileSync(path.join(outDir, list ? `t${(i / 30).toFixed(1)}.jpg` : `f_${String(i + 1).padStart(4, '0')}.jpg`), Buffer.from(data.split(',')[1], 'base64'));
  }
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
