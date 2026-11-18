// Движок кадров. Строит страницу выпуска по EPISODE и рисует любой момент времени
// функцией render(t). Используется и для просмотра в браузере, и для записи mp4.
(function () {
  const ep = window.EPISODE;
  const params = new URLSearchParams(location.search);
  const RENDER = params.has("render");
  const FADE = 0.6;          // смена сцены
  const TEXT_IN = 0.7;       // появление строки текста
  const TEXT_OUT = 0.45;     // исчезновение текста в конце кадра
  const N = ep.frames.length;
  const pad = (n, l = 2) => String(n).padStart(l, "0");

  let acc = 0;
  ep.frames.forEach((f) => { f.start = acc; acc += f.duration; });
  const TOTAL = acc;

  const esc = (s) => String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;");

  function card(f, i) {
    const a = (cls, at, html) => html ? `<div class="a ${cls}" data-at="${at}">${html}</div>` : "";
    let body = "";
    if (f.type === "title") {
      body = a("kicker", 0.3, `Выпуск № ${pad(ep.num, 3)}`) +
             a("ar", 0.5, esc(f.ar)) +
             a("rule", 0.8, "") +
             a("ru big", 0.9, esc(f.ru)) +
             a("sub", 1.2, esc(f.sub));
    } else if (f.type === "fact") {
      body = a("label", 0.3, "Факт") +
             a("ru fact", 0.6, esc(f.ru)) +
             a("rule", 0.9, "") +
             a("src", 1.1, esc(f.src)) +
             a("note", 1.3, esc(f.note));
    } else {
      body = a("ar", 0.3, esc(f.ar)) +
             a("rule", 0.7, "") +
             a("ru", 0.8, esc(f.ru)) +
             a("src", 1.1, esc(f.src)) +
             a("note", 1.3, esc(f.note));
    }
    return `<div class="card type-${f.type}" data-i="${i}">${body}</div>`;
  }

  const stage = document.createElement("div");
  stage.className = "stage";
  stage.innerHTML = `
    <div class="bg"></div>
    <div class="orn"></div>
    <div class="hdr">
      <span class="num">№ ${pad(ep.num, 3)}</span>
      <span class="secs">${ep.frames.map((f, i) => `<span class="sec" data-i="${i}">${esc(f.section)}</span>`).join("")}</span>
      <span class="cnt"><b>01</b> / ${pad(N)}</span>
      <div class="prog"><i></i></div>
    </div>
    <div class="scene-wrap">
      ${ep.frames.map((f, i) => `<div class="scene" data-i="${i}">${window.renderScene(f.scene)}</div>`).join("")}
      <div class="vignette"></div>
    </div>
    <div class="panel">${ep.frames.map(card).join("")}</div>
    <div class="ftr">
      <div class="name">${esc(ep.name)}</div>
      <div class="series">${esc(ep.kunya.split(" — ")[0])} · Сподвижники Пророка ﷺ · по достоверной Сунне</div>
    </div>
    <div class="black"></div>`;
  document.body.appendChild(stage);

  const $$ = (s) => Array.from(stage.querySelectorAll(s));
  const scenes = $$(".scene"), cards = $$(".card"), secs = $$(".sec");
  const cntB = stage.querySelector(".cnt b"), bar = stage.querySelector(".prog i");
  const black = stage.querySelector(".black");
  const ease = (x) => { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); };

  // Длины линий для прорисовки
  const draws = $$("[data-draw]").map((el) => {
    const len = el.getTotalLength();
    el.style.strokeDasharray = `${len} ${len}`;
    const [a, b] = el.dataset.draw.split(",").map(Number);
    return { el, len, a, b, i: +el.closest(".scene").dataset.i };
  });

  function render(t) {
    t = Math.max(0, Math.min(TOTAL - 1e-6, t));
    let i = ep.frames.findIndex((f) => t >= f.start && t < f.start + f.duration);
    if (i < 0) i = N - 1;
    const f = ep.frames[i], lt = t - f.start, D = f.duration;

    scenes.forEach((s, j) => {
      let o = 0;
      if (j === i) o = i === 0 ? 1 : ease(lt / FADE);
      else if (j === i - 1 && lt < FADE) o = 1;
      s.style.opacity = o;
      s.style.zIndex = j === i ? 2 : 1;
      const local = j === i ? lt : (j === i - 1 ? ep.frames[j].duration + lt : 0);
      const d = ep.frames[j].duration;
      s.style.transform = `scale(${1.03 + 0.05 * Math.min(1, local / d)})`;
    });

    cards.forEach((c, j) => {
      c.style.visibility = j === i ? "visible" : "hidden";
      if (j !== i) return;
      const out = i === N - 1 ? 1 : ease((D - lt) / TEXT_OUT);
      c.querySelectorAll(".a").forEach((el) => {
        const e = ease((lt - +el.dataset.at) / TEXT_IN);
        el.style.opacity = e * out;
        el.style.transform = el.classList.contains("rule") ? `scaleX(${e})` : `translateY(${(1 - e) * 18}px)`;
      });
    });

    secs.forEach((s, j) => {
      s.style.opacity = j === i ? (i === 0 ? 1 : ease(lt / 0.5)) : (j === i - 1 ? 1 - ease(lt / 0.3) : 0);
    });
    cntB.textContent = pad(i + 1);
    bar.style.width = ((i + lt / D) / N * 100).toFixed(3) + "%";

    draws.forEach((d) => {
      const p = d.i === i ? ease((lt - d.a) / (d.b - d.a)) : (d.i < i ? 1 : 0);
      d.el.style.strokeDashoffset = d.len * (1 - p);
    });

    black.style.opacity = Math.max(1 - ease(t / 0.6), ease((t - (TOTAL - 0.8)) / 0.8));

    document.getAnimations().forEach((an) => { an.pause(); an.currentTime = t * 1000; });
  }

  window.TOTAL = TOTAL;
  window.render = render;

  function fit() {
    const k = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = RENDER ? "none" : `translate(${(innerWidth - 1920 * k) / 2}px, ${(innerHeight - 1080 * k) / 2}px) scale(${k})`;
  }
  addEventListener("resize", fit); fit();

  if (!RENDER) {
    const t0 = performance.now();
    const loop = () => { render(((performance.now() - t0) / 1000) % TOTAL); requestAnimationFrame(loop); };
    document.fonts.ready.then(loop);
  } else {
    render(0);
  }
})();
