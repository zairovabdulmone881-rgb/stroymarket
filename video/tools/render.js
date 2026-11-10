// Снимает кадры выпуска в JPEG 1920×1080 (вызывается из make_video.py).
//   node render.js <папка выпуска> <папка для кадров> <номер потока> <всего потоков> [fps]
// Время не «проигрывается», а выставляется вручную для каждого кадра, поэтому ролик выходит ровным.
const {chromium} = require('playwright');
const fs = require('fs');
(async () => {
  const [ep, out, w, n, fpsArg] = process.argv.slice(2);
  const fps = +(fpsArg || 30);
  const b = await chromium.launch();
  const p = await b.newPage({viewport: {width: 1920, height: 1080}, deviceScaleFactor: 1});
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + ep + '/index.html');
  await p.addStyleTag({content: `body{padding:0!important}.page{max-width:none!important;gap:0!important}
    .page>*:not(#wrap){display:none!important}
    #wrap{position:fixed!important;inset:0;border:0!important;border-radius:0!important;aspect-ratio:auto!important;width:1920px;height:1080px}
    .main{transition:none!important}`});
  await p.evaluate(() => { fit(); return document.fonts.ready; });
  await p.waitForTimeout(1500);
  const D = await p.evaluate(() => DUR);
  const starts = []; let T = 0; D.forEach(d => { starts.push(T); T += d; });
  fs.mkdirSync(out, {recursive: true});
  for (let i = 0; i < D.length; i++) {
    if (i % (+n) !== +w) continue;
    await p.evaluate(i => {
      const f = FRAMES[i]; main.innerHTML = html(f);
      $('sec').textContent = f.sec;
      $('num').innerHTML = String(i + 1).padStart(2, '0') + ' <i>/ ' + FRAMES.length + '</i>';
      return document.fonts.ready;
    }, i);
    const nf = Math.round(D[i] * fps), g0 = Math.round(starts[i] * fps);
    for (let k = 0; k < nf; k++) {
      const t = k / fps;
      await p.evaluate(([t, d, g, T]) => {
        document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; });
        main.style.opacity = Math.max(0, Math.min(1, t / .5, (d - t) / .5));
        $('prog').style.width = (g / T * 100) + '%';
      }, [t, D[i], starts[i] + t, T]);
      await p.screenshot({path: `${out}/${String(g0 + k).padStart(6, '0')}.jpg`, type: 'jpeg', quality: 95,
        clip: {x: 0, y: 0, width: 1920, height: 1080}});
    }
  }
  await b.close();
  if (errs.length) { console.error(errs.join('\n')); process.exit(1); }
})();
