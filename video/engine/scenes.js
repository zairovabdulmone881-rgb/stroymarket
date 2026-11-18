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
    road: (fr) => `
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
      <text x="1055" y="572" class="map-label">${(fr.labels||[])[0]||"МЕККА"}</text>
      <text x="615" y="182" class="map-label">${(fr.labels||[])[1]||"МЕДИНА"}</text>
      <text x="1240" y="120" class="map-label small">${fr.mapNote||""}</text>`,

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


    // Пещера в горах, ночь
    cave: () => `
      <defs><linearGradient id="sky-cave" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--night-top)"/><stop offset="1" stop-color="var(--night-bot)"/></linearGradient>
      <radialGradient id="cave-in" cx="0.5" cy="0.6" r="0.6"><stop offset="0" stop-color="var(--sun)" stop-opacity="0.35"/><stop offset="1" stop-color="var(--sun)" stop-opacity="0"/></radialGradient></defs>
      <rect width="${W}" height="${H}" fill="url(#sky-cave)"/>
      ${stars(110, 9)}
      <path d="M-50 900 L 120 420 L 330 300 L 520 360 L 760 180 L 1040 330 L 1260 260 L 1460 420 L 1650 900Z" fill="var(--far)"/>
      <path d="M 260 900 L 420 520 L 620 430 L 800 360 L 1000 450 L 1180 520 L 1340 900Z" fill="var(--mid)"/>
      <path d="M 680 900 Q 670 660 800 600 Q 930 660 920 900Z" fill="#000"/>
      <ellipse class="flicker" cx="800" cy="780" rx="160" ry="120" fill="url(#cave-in)"/>
      <path d="M0 860 Q 400 820 800 850 T 1600 840 V900 H0Z" fill="var(--near)"/>`,

    // Гора Ухуд на закате
    mountain: () => `
      ${sky("mountain")}
      <circle class="glow" cx="1240" cy="600" r="420" fill="url(#sun-mountain)"/>
      <circle cx="1240" cy="600" r="80" fill="var(--sun)" opacity="0.8"/>
      <path d="M-100 700 L 200 470 L 380 520 L 640 300 L 820 380 L 1000 260 L 1260 430 L 1460 380 L 1700 700Z" fill="var(--far)"/>
      <path d="M-100 760 L 260 600 L 520 660 L 760 560 L 1100 680 L 1400 600 L 1700 760 V900 H-100Z" fill="var(--mid)"/>
      <path d="M0 820 Q 400 780 800 810 T 1600 800 V900 H0Z" fill="var(--near)"/>
      ${particles(40, 31, "drift-p", "var(--sun)", 1.6, 300, 860)}`,

    // Мечеть Пророка ﷺ: пальмовые стволы и навес
    mosque: () => `
      <defs><radialGradient id="mq-l" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="var(--sun)" stop-opacity="0.55"/><stop offset="1" stop-color="var(--sun)" stop-opacity="0"/></radialGradient></defs>
      <rect width="${W}" height="${H}" fill="var(--sky-top)"/>
      <rect y="0" width="${W}" height="${H}" fill="var(--sky-bot)" opacity="0.35"/>
      <circle class="flicker" cx="800" cy="420" r="600" fill="url(#mq-l)"/>
      <path d="M0 150 L1600 150 L1600 210 L0 210Z" fill="var(--ink)"/>
      <g fill="none" stroke="var(--ink)" stroke-width="6" opacity="0.8">
        ${Array.from({ length: 30 }, (_, i) => `<line x1="${i * 56}" y1="150" x2="${i * 56 + 40}" y2="210"/>`).join("")}</g>
      ${[140, 420, 700, 900, 1180, 1460].map((x) => `<rect x="${x - 22}" y="200" width="44" height="620" rx="10" fill="var(--ink)"/>
        <g stroke="var(--far)" stroke-width="3" opacity="0.6">${Array.from({ length: 14 }, (_, k) => `<line x1="${x - 20}" y1="${230 + k * 42}" x2="${x + 20}" y2="${244 + k * 42}"/>`).join("")}</g>`).join("")}
      <g class="flicker"><line x1="800" y1="210" x2="800" y2="330" stroke="var(--ink)" stroke-width="3"/><circle cx="800" cy="350" r="22" fill="var(--sun)"/></g>
      <rect y="810" width="${W}" height="90" fill="var(--near)"/>
      ${particles(26, 41, "drift-p", "var(--sun)", 1.3, 260, 800)}`,

    // Караван в пустыне
    caravan: () => `
      ${sky("caravan")}
      <circle class="glow" cx="400" cy="560" r="380" fill="url(#sun-caravan)"/>
      <circle cx="400" cy="560" r="86" fill="var(--sun)" opacity="0.85"/>
      <g class="drift slow"><path d="M-200 620 Q 200 560 600 610 T 1400 600 T 2000 610 V900 H-200Z" fill="var(--far)"/></g>
      <path d="M0 700 Q 500 650 900 690 T 1600 680 V900 H0Z" fill="var(--mid)"/>
      <g fill="var(--ink)" transform="translate(0 0)">
        ${[620, 860, 1100].map((x, k) => `<g transform="translate(${x} ${676 - k * 4}) scale(${1 - k * 0.12})">
          <path d="M-90 0 L-80 -60 Q -70 -110 -30 -112 Q 0 -150 30 -112 Q 60 -112 70 -80 L 96 -96 Q 120 -120 130 -96 L 136 -70 L 120 -66 L 92 -40 L 80 0 L 66 0 L 60 -40 L -50 -40 L -60 0 L -74 0 L -70 -40Z"/></g>`).join("")}
      </g>
      <path d="M0 790 Q 400 740 820 780 T 1600 770 V900 H0Z" fill="var(--near)"/>
      ${particles(40, 51, "drift-p", "var(--accent)", 1.6, 420, 860)}`,

    // Пальмы Медины и колодец
    palms: () => `
      ${sky("palms")}
      <circle class="glow" cx="1100" cy="420" r="380" fill="url(#sun-palms)"/>
      <path d="M0 640 Q 400 600 800 630 T 1600 620 V900 H0Z" fill="var(--far)"/>
      ${[[220, 1], [430, 0.8], [1250, 0.95], [1450, 0.75]].map(([x, k]) => `<g transform="translate(${x} 700) scale(${k})" fill="var(--ink)">
        <path d="M-10 0 Q -18 -220 6 -440 L 18 -440 Q 4 -220 12 0Z"/>
        <g class="wave">${[-150, -110, -60, 10, 60, 110, 150].map((a) => `<path d="M12 -440 Q ${12 + a} ${-500 + Math.abs(a) / 3} ${12 + a * 1.6} ${-400 + Math.abs(a) * 0.6} Q ${12 + a * 0.9} ${-470 + Math.abs(a) / 3} 12 -440Z"/>`).join("")}</g></g>`).join("")}
      <g transform="translate(800 720)">
        <ellipse cx="0" cy="0" rx="150" ry="34" fill="var(--ink)"/>
        <rect x="-150" y="-70" width="300" height="70" fill="var(--mid)"/><ellipse cx="0" cy="-70" rx="150" ry="34" fill="var(--far)"/>
        <ellipse cx="0" cy="-70" rx="110" ry="22" fill="var(--ink)"/>
        <path d="M-130 -70 L-130 -220 L130 -220 L130 -70" fill="none" stroke="var(--ink)" stroke-width="12"/>
        <line x1="0" y1="-220" x2="0" y2="-120" stroke="var(--accent)" stroke-width="3"/><rect x="-22" y="-124" width="44" height="40" rx="6" fill="var(--accent)"/>
      </g>
      <path d="M0 800 Q 500 770 900 790 T 1600 785 V900 H0Z" fill="var(--near)"/>`,

    // Свиток и светильник — знание, Коран, записи
    scroll: () => `
      <defs><radialGradient id="sc-l" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="var(--sun)" stop-opacity="0.6"/><stop offset="1" stop-color="var(--sun)" stop-opacity="0"/></radialGradient></defs>
      <rect width="${W}" height="${H}" fill="var(--sky-top)"/>
      <circle class="flicker" cx="1150" cy="380" r="520" fill="url(#sc-l)"/>
      <rect y="640" width="${W}" height="260" fill="var(--near)"/>
      <g transform="translate(700 600) rotate(-4)">
        <rect x="-420" y="-150" width="840" height="300" rx="10" fill="var(--far)"/>
        <rect x="-460" y="-170" width="60" height="340" rx="30" fill="var(--mid)"/><rect x="400" y="-170" width="60" height="340" rx="30" fill="var(--mid)"/>
        <g stroke="var(--accent)" stroke-width="5" stroke-linecap="round" opacity="0.75">
          ${Array.from({ length: 6 }, (_, k) => `<line data-draw="${0.3 + k * 0.5},${0.9 + k * 0.5}" x1="${330}" y1="${-100 + k * 42}" x2="${-330 + (k % 2) * 60}" y2="${-100 + k * 42}"/>`).join("")}
        </g>
      </g>
      <g transform="translate(1150 560)">
        <path d="M-90 40 Q 0 90 90 40 L 120 10 L 60 10 Q 0 -20 -60 10 L -110 30Z" fill="var(--ink)"/>
        <path class="flicker" d="M100 6 Q 112 -40 128 -70 Q 146 -30 132 6Z" fill="var(--sun)"/>
      </g>
      ${particles(24, 61, "drift-p", "var(--sun)", 1.2, 200, 640)}`,

    // Крепость с воротами
    fort: () => `
      ${sky("fort")}
      <circle class="glow" cx="800" cy="300" r="380" fill="url(#sun-fort)"/>
      <path d="M0 700 Q 400 660 800 690 T 1600 680 V900 H0Z" fill="var(--far)"/>
      <g fill="var(--ink)">
        <rect x="360" y="340" width="880" height="400"/>
        ${Array.from({ length: 15 }, (_, i) => `<rect x="${360 + i * 60}" y="310" width="34" height="40"/>`).join("")}
        <rect x="300" y="260" width="160" height="480"/><rect x="1140" y="260" width="160" height="480"/>
        ${Array.from({ length: 4 }, (_, i) => `<rect x="${300 + i * 42}" y="230" width="26" height="40"/><rect x="${1140 + i * 42}" y="230" width="26" height="40"/>`).join("")}
      </g>
      <path d="M700 740 L700 560 Q 800 470 900 560 L 900 740Z" fill="var(--mid)"/>
      <path d="M700 740 L700 560 Q 800 470 900 560 L 900 740Z" fill="none" stroke="var(--accent)" stroke-width="4"/>
      <line x1="800" y1="510" x2="800" y2="740" stroke="var(--accent)" stroke-width="3" opacity="0.7"/>
      <path d="M0 790 Q 400 750 800 780 T 1600 770 V900 H0Z" fill="var(--near)"/>
      ${particles(40, 71, "drift-p", "var(--sun)", 2, 300, 860)}`,

    // Лагерь: шатры и костёр
    camp: () => `
      <defs><linearGradient id="sky-camp" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--night-top)"/><stop offset="1" stop-color="var(--night-bot)"/></linearGradient>
      <radialGradient id="fire" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="var(--sun)" stop-opacity="0.7"/><stop offset="1" stop-color="var(--sun)" stop-opacity="0"/></radialGradient></defs>
      <rect width="${W}" height="${H}" fill="url(#sky-camp)"/>
      ${stars(100, 17)}
      <path d="M0 640 Q 400 610 800 630 T 1600 620 V900 H0Z" fill="var(--far)"/>
      <g fill="var(--ink)">
        <path d="M120 760 L 330 500 L 540 760Z"/><path d="M500 740 L 640 560 L 780 740Z"/>
        <path d="M1020 750 L 1200 520 L 1380 750Z"/><path d="M1340 740 L 1460 590 L 1580 740Z"/>
      </g>
      <circle class="flicker" cx="900" cy="740" r="260" fill="url(#fire)"/>
      <g class="flicker"><path d="M870 760 Q 880 690 900 650 Q 924 700 932 760Z" fill="var(--sun)"/><path d="M886 760 Q 896 720 906 700 Q 918 730 918 760Z" fill="var(--accent)"/></g>
      <rect y="760" width="${W}" height="140" fill="var(--near)"/>
      ${particles(30, 81, "drift-p", "var(--sun)", 1.4, 500, 760)}`,

    // Море и парусник (переселение в Абиссинию)
    sea: () => `
      ${sky("sea")}
      <circle class="glow" cx="1150" cy="470" r="380" fill="url(#sun-sea)"/>
      <circle cx="1150" cy="470" r="80" fill="var(--sun)" opacity="0.85"/>
      <rect y="520" width="${W}" height="380" fill="var(--far)"/>
      <g class="drift" stroke="var(--accent)" stroke-width="3" fill="none" opacity="0.4">
        ${Array.from({ length: 8 }, (_, k) => `<path d="M-200 ${560 + k * 42} q 50 -14 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0 t 100 0"/>`).join("")}</g>
      <g transform="translate(620 600)" fill="var(--ink)">
        <path d="M-180 0 L 180 0 L 130 60 L -130 60Z"/><rect x="-6" y="-300" width="12" height="300"/>
        <g class="wave"><path d="M6 -290 Q 150 -170 6 -20Z"/></g><path d="M-6 -260 Q -120 -150 -6 -40Z"/>
      </g>
      <rect y="820" width="${W}" height="80" fill="var(--near)"/>`,

    // Кааба
    kaaba: () => `
      <defs><linearGradient id="sky-kb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--night-top)"/><stop offset="1" stop-color="var(--night-bot)"/></linearGradient></defs>
      <rect width="${W}" height="${H}" fill="url(#sky-kb)"/>
      ${stars(90, 23)}
      <path d="M-50 640 L 200 420 L 420 520 L 640 380 L 900 520 L 1180 400 L 1400 500 L 1650 640Z" fill="var(--far)"/>
      <g transform="translate(800 520)">
        <path d="M-200 0 L 120 -40 L 260 20 L 260 300 L 120 330 L -200 300Z" fill="var(--ink)"/>
        <path d="M120 -40 L 120 330" stroke="var(--far)" stroke-width="2"/>
        <path d="M-200 60 L 120 26 L 260 80 L 260 110 L 120 58 L -200 92Z" fill="var(--accent)" opacity="0.85"/>
        <rect x="160" y="170" width="44" height="80" fill="var(--accent)" opacity="0.6" transform="skewY(10)"/>
      </g>
      <ellipse cx="830" cy="860" rx="900" ry="80" fill="var(--near)"/>
      ${particles(30, 91, "drift-p", "var(--star)", 1.2, 100, 600)}`,

    // Монеты и кошель — щедрость, имущество
    coins: () => `
      <defs><radialGradient id="cn-l" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="var(--sun)" stop-opacity="0.5"/><stop offset="1" stop-color="var(--sun)" stop-opacity="0"/></radialGradient></defs>
      <rect width="${W}" height="${H}" fill="var(--sky-top)"/>
      <circle class="flicker" cx="800" cy="520" r="560" fill="url(#cn-l)"/>
      <rect y="700" width="${W}" height="200" fill="var(--near)"/>
      <path d="M640 700 Q 600 520 700 470 L 680 420 Q 800 390 920 420 L 900 470 Q 1000 520 960 700Z" fill="var(--mid)"/>
      <path d="M680 420 Q 800 450 920 420" stroke="var(--accent)" stroke-width="5" fill="none"/>
      ${[[520, 690], [580, 676], [1050, 694], [1110, 680], [1000, 700], [470, 700], [1170, 700]].map(([x, y], k) => `<ellipse cx="${x}" cy="${y}" rx="38" ry="12" fill="var(--accent)" opacity="${0.6 + (k % 3) * 0.12}"/>`).join("")}
      ${particles(40, 101, "drift-p", "var(--sun)", 1.5, 200, 700)}`,

    // Лучи света над горизонтом — финал
    light: () => `
      ${sky("light")}
      <g class="glow" opacity="0.5">${Array.from({ length: 13 }, (_, k) => `<path d="M800 760 L ${-400 + k * 200} -100 L ${-330 + k * 200} -100Z" fill="var(--sun)" opacity="0.12"/>`).join("")}</g>
      <circle class="glow" cx="800" cy="760" r="520" fill="url(#sun-light)"/>
      <path d="M0 760 Q 400 720 800 745 T 1600 740 V900 H0Z" fill="var(--mid)"/>
      <path d="M0 820 Q 400 800 800 815 T 1600 810 V900 H0Z" fill="var(--near)"/>
      ${particles(50, 111, "drift-p", "var(--star)", 1.4, 100, 760)}`,
    // Кончина: ночь над городом
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

  window.SCENE_NAMES = Object.keys(SCENES);
  window.renderScene = function (name, fr) {
    if (!SCENES[name]) throw new Error("Нет сцены: " + name);
    return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">${SCENES[name](fr || {})}</svg>`;
  };
})();
