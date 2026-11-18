// Рисованные сцены серии. Только силуэты, карты и символы —
// лица и фигуры людей не изображаются.
// Цвета берутся из CSS-переменных оформления (--sky-top, --sky-bot, --sun,
// --far, --mid, --near, --ink, --accent, --star, --map-bg, --map-line).
// Анимации с классами .drift/.glow/.wave/.twinkle/.flicker/.glint — бесконечные
// CSS-анимации, движок выставляет им время. data-draw="начало,конец" — линия
// прорисовывается по локальному времени кадра.
(function () {
  const W = 1600, H = 900;

  function particles(n, seed, cls, color, rMax, yMin, yMax) {
    let s = seed, out = "";
    const rnd = () => ((s = (s * 9301 + 49297) % 233280) / 233280);
    for (let i = 0; i < n; i++) {
      const x = rnd() * W, y = yMin + rnd() * (yMax - yMin), r = 0.8 + rnd() * rMax;
      const d = (rnd() * -12).toFixed(2), dur = (8 + rnd() * 10).toFixed(2);
      out += `<circle class="${cls}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r.toFixed(1)}" fill="${color}" style="animation-delay:${d}s;animation-duration:${dur}s;opacity:${(0.25 + rnd() * 0.5).toFixed(2)}"/>`;
    }
    return out;
  }

  function stars(n, seed) {
    let s = seed, out = "";
    const rnd = () => ((s = (s * 9301 + 49297) % 233280) / 233280);
    for (let i = 0; i < n; i++) {
      const x = rnd() * W, y = rnd() * 560, r = 0.6 + rnd() * 1.8;
      out += `<circle class="twinkle" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r.toFixed(1)}" fill="var(--star)" style="animation-delay:${(rnd() * -4).toFixed(2)}s;animation-duration:${(2.5 + rnd() * 3).toFixed(2)}s"/>`;
    }
    return out;
  }

  const sky = (id) => `
    <defs>
      <linearGradient id="sky-${id}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="var(--sky-top)"/><stop offset="1" stop-color="var(--sky-bot)"/>
      </linearGradient>
      <radialGradient id="sun-${id}" cx="0.5" cy="0.5" r="0.5">
        <stop offset="0" stop-color="var(--sun)" stop-opacity="0.95"/>
        <stop offset="0.25" stop-color="var(--sun)" stop-opacity="0.45"/>
        <stop offset="1" stop-color="var(--sun)" stop-opacity="0"/>
      </radialGradient>
    </defs>
    <rect width="${W}" height="${H}" fill="url(#sky-${id})"/>`;

  const SCENES = {
    // Титул: восход над барханами и меч
    sword: () => `
      ${sky("sword")}
      <circle class="glow" cx="800" cy="560" r="420" fill="url(#sun-sword)"/>
      <circle cx="800" cy="560" r="92" fill="var(--sun)" opacity="0.85"/>
      <g class="drift slow">
        <path d="M-200 600 Q 150 520 420 590 T 1000 570 T 1600 600 T 2000 590 V900 H-200Z" fill="var(--far)"/>
      </g>
      <path d="M0 690 Q 300 610 620 680 T 1180 660 T 1600 700 V900 H0Z" fill="var(--mid)"/>
      <g transform="translate(800 690) rotate(-8)">
        <path d="M-18 0 L18 0 L10 -40 L-10 -40Z" fill="var(--ink)"/>
        <rect x="-70" y="-52" width="140" height="14" rx="7" fill="var(--ink)"/>
        <path d="M-9 -52 C -14 -200 10 -330 70 -440 C 40 -320 22 -200 9 -52Z" fill="var(--ink)"/>
        <path class="glint" d="M2 -70 C 2 -200 22 -320 62 -428" stroke="var(--accent)" stroke-width="3" fill="none" stroke-linecap="round"/>
      </g>
      <path d="M0 770 Q 400 700 820 760 T 1600 750 V900 H0Z" fill="var(--near)"/>
      ${particles(40, 7, "drift-p", "var(--accent)", 1.8, 420, 860)}`,

    // Карта: путь из Мекки в Медину
    road: () => `
      <defs>
        <pattern id="grid-road" width="80" height="80" patternUnits="userSpaceOnUse">
          <path d="M80 0H0V80" fill="none" stroke="var(--map-line)" stroke-width="1" opacity="0.35"/>
        </pattern>
      </defs>
      <rect width="${W}" height="${H}" fill="var(--map-bg)"/>
      <rect width="${W}" height="${H}" fill="url(#grid-road)"/>
      <path d="M0 120 C 180 160 260 300 230 420 S 120 700 210 900" stroke="var(--map-line)" stroke-width="3" fill="none" opacity="0.6"/>
      <text x="90" y="560" class="map-label small" transform="rotate(-80 90 560)">КРАСНОЕ МОРЕ</text>
      <g opacity="0.5" fill="none" stroke="var(--map-line)" stroke-width="2">
        <path d="M600 200 q 30 -40 60 0 q 30 -40 60 0"/><path d="M1180 520 q 30 -40 60 0 q 30 -40 60 0"/>
        <path d="M980 300 q 30 -40 60 0"/><path d="M500 640 q 30 -40 60 0 q 30 -40 60 0"/>
      </g>
      <path data-draw="0.4,4.6" d="M1000 560 C 930 470 760 480 730 400 S 800 270 740 220 S 620 180 560 170"
            stroke="var(--accent)" stroke-width="6" fill="none" stroke-linecap="round" stroke-dasharray="2 0"/>
      <g class="glow"><circle cx="1000" cy="560" r="34" fill="var(--accent)" opacity="0.25"/></g>
      <circle cx="1000" cy="560" r="14" fill="var(--accent)"/>
      <circle cx="560" cy="170" r="14" fill="var(--accent)"/>
      <g class="glow"><circle cx="560" cy="170" r="34" fill="var(--accent)" opacity="0.25"/></g>
      <text x="1055" y="572" class="map-label">МЕККА</text>
      <text x="615" y="182" class="map-label">МЕДИНА</text>
      <text x="1240" y="120" class="map-label small">8 г. х.</text>`,

    // Му'та: знамя над холмами, пыль
    banner: () => `
      ${sky("banner")}
      <circle class="glow" cx="1200" cy="380" r="360" fill="url(#sun-banner)"/>
      <path d="M0 560 L 180 470 L 330 540 L 520 430 L 720 530 L 900 460 L 1100 540 L 1320 450 L 1600 540 V900 H0Z" fill="var(--far)"/>
      <g stroke="var(--mid)" stroke-width="4">
        ${Array.from({ length: 34 }, (_, i) => `<line x1="${60 + i * 46}" y1="${640 - (i % 3) * 12}" x2="${70 + i * 46}" y2="${520 - (i % 4) * 14}"/>`).join("")}
      </g>
      <path d="M0 650 Q 400 600 800 640 T 1600 630 V900 H0Z" fill="var(--mid)"/>
      <rect x="742" y="250" width="12" height="560" rx="5" fill="var(--ink)"/>
      <circle cx="748" cy="244" r="14" fill="var(--accent)"/>
      <g class="wave"><path d="M754 270 C 880 240 980 300 1110 262 L 1110 452 C 980 490 880 430 754 460Z" fill="var(--ink)"/>
        <path d="M754 270 C 880 240 980 300 1110 262" stroke="var(--accent)" stroke-width="3" fill="none" opacity="0.7"/></g>
      <path d="M0 760 Q 500 700 900 750 T 1600 740 V900 H0Z" fill="var(--near)"/>
      ${particles(70, 13, "drift-p", "var(--sun)", 2.4, 300, 880)}`,

    // Достоинства: кольчуги и снаряжение
    armour: () => `
      <defs>
        <pattern id="mail" width="18" height="12" patternUnits="userSpaceOnUse">
          <path d="M0 12 a9 9 0 0 1 18 0" fill="none" stroke="var(--accent)" stroke-width="1.6" opacity="0.55"/>
        </pattern>
        <radialGradient id="lamp" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0" stop-color="var(--sun)" stop-opacity="0.6"/><stop offset="1" stop-color="var(--sun)" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <rect width="${W}" height="${H}" fill="var(--sky-top)"/>
      <path d="M0 0 L800 -60 L1600 0 V900 H0Z" fill="var(--sky-bot)" opacity="0.6"/>
      <circle class="flicker" cx="800" cy="300" r="620" fill="url(#lamp)"/>
      <rect x="300" y="180" width="1000" height="18" rx="9" fill="var(--ink)"/>
      <g transform="translate(560 198)">
        <path d="M-120 0 L120 0 L150 60 L110 70 L120 360 L-120 360 L-110 70 L-150 60Z" fill="var(--far)"/>
        <path d="M-120 0 L120 0 L150 60 L110 70 L120 360 L-120 360 L-110 70 L-150 60Z" fill="url(#mail)"/>
      </g>
      <g transform="translate(1040 198)">
        <path d="M-120 0 L120 0 L150 60 L110 70 L120 360 L-120 360 L-110 70 L-150 60Z" fill="var(--far)"/>
        <path d="M-120 0 L120 0 L150 60 L110 70 L120 360 L-120 360 L-110 70 L-150 60Z" fill="url(#mail)"/>
      </g>
      <g stroke="var(--ink)" stroke-width="10" stroke-linecap="round">
        <line x1="240" y1="820" x2="380" y2="150"/><line x1="1360" y1="820" x2="1220" y2="150"/>
      </g>
      <path d="M380 150 l-10 -50 l26 44Z" fill="var(--accent)"/><path d="M1220 150 l10 -50 l-26 44Z" fill="var(--accent)"/>
      <rect x="0" y="760" width="${W}" height="140" fill="var(--near)"/>
      <g transform="translate(800 690)">
        <circle r="110" fill="var(--mid)"/><circle r="110" fill="none" stroke="var(--accent)" stroke-width="5"/>
        <circle r="24" fill="var(--accent)"/>
      </g>
      <g transform="translate(470 720)"><circle r="70" fill="var(--mid)"/><circle r="70" fill="none" stroke="var(--accent)" stroke-width="4" opacity="0.7"/><circle r="15" fill="var(--accent)" opacity="0.8"/></g>
      <g transform="translate(1130 720)"><circle r="70" fill="var(--mid)"/><circle r="70" fill="none" stroke="var(--accent)" stroke-width="4" opacity="0.7"/><circle r="15" fill="var(--accent)" opacity="0.8"/></g>
      ${particles(30, 21, "drift-p", "var(--sun)", 1.4, 120, 760)}`,

    // Кончина: ночь над Хомсом
    night: () => `
      <defs>
        <linearGradient id="sky-night" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="var(--night-top)"/><stop offset="1" stop-color="var(--night-bot)"/>
        </linearGradient>
      </defs>
      <rect width="${W}" height="${H}" fill="url(#sky-night)"/>
      ${stars(120, 5)}
      <g transform="translate(1180 220)" class="glow">
        <circle r="70" fill="var(--star)"/><circle cx="26" cy="-14" r="64" fill="var(--night-top)"/>
      </g>
      <path d="M0 640 Q 400 590 800 620 T 1600 610 V900 H0Z" fill="var(--far)" opacity="0.8"/>
      <g fill="var(--ink)">
        <rect x="120" y="600" width="160" height="300"/><rect x="290" y="640" width="120" height="260"/>
        <rect x="430" y="580" width="200" height="320"/><path d="M470 580 a60 60 0 0 1 120 0Z"/>
        <rect x="650" y="620" width="140" height="280"/><rect x="810" y="560" width="220" height="340"/>
        <path d="M840 560 a80 80 0 0 1 160 0Z"/><rect x="1050" y="630" width="130" height="270"/>
        <rect x="1200" y="600" width="180" height="300"/><rect x="1400" y="650" width="200" height="250"/>
      </g>
      <g fill="var(--accent)" class="flicker">
        <rect x="170" y="660" width="14" height="22" rx="7"/><rect x="520" y="650" width="14" height="22" rx="7"/>
        <rect x="900" y="640" width="14" height="22" rx="7"/><rect x="960" y="640" width="14" height="22" rx="7"/>
        <rect x="1270" y="670" width="14" height="22" rx="7"/>
      </g>
      <rect y="840" width="${W}" height="60" fill="var(--near)"/>`
  };

  window.renderScene = function (name) {
    return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">${SCENES[name]()}</svg>`;
  };
})();
