/* Предметы комнат: контурный «неоновый» стиль */
const OUT = '#C9C6FF';
function fillStroke(c, fill, stroke = OUT, lw = 2.2) { c.fillStyle = fill; c.fill(); c.strokeStyle = stroke; c.lineWidth = lw; c.lineJoin = 'round'; c.stroke(); }
function R(c, x, y, w, h, r, fill, stroke, lw) { rr(c, x, y, w, h, r); fillStroke(c, fill, stroke, lw); }

const Pr = {
  deskLaptop(g, x, gnd, o = {}) {
    const c = g.c, s = o.s || 1; c.save(); c.translate(x, gnd); c.scale(s, s);
    R(c, -105, -112, 210, 10, 3, '#3A3A78'); // столешница
    c.fillStyle = '#34346E'; c.fillRect(-92, -102, 8, 102); c.fillRect(84, -102, 8, 102);
    c.strokeStyle = OUT; c.lineWidth = 2; c.strokeRect(-92, -102, 8, 102); c.strokeRect(84, -102, 8, 102);
    // ноутбук
    R(c, -58, -218, 116, 94, 7, '#1A1840'); R(c, -52, -212, 104, 82, 4, '#A8C4FF', '#E7EEFF', 1.5);
    c.fillStyle = '#6C74FF'; c.fillRect(-52, -212, 104, 10);
    c.fillStyle = '#1D2A66'; [0, 1, 2, 3, 4, 5].forEach(i => c.fillRect(-44, -194 + i * 10, 62 + (i % 3) * 14, 3.2));
    R(c, -70, -124, 140, 12, 5, '#B7D2FF', '#E7EEFF', 1.5);
    if (o.glow !== false) glowCircle(c, 0, -170, 120, 'rgba(160,150,255,A)', .35);
    c.restore();
  },
  sofa(g, x, gnd, s = 1, o = {}) {
    const c = g.c; c.save(); c.translate(x, gnd); c.scale(s, s);
    const body = o.col || '#5B4FB0', back = o.back || '#4A3F96';
    R(c, -100, -118, 200, 76, 16, back);                     // спинка
    R(c, -146, -82, 48, 70, 16, body); R(c, 98, -82, 48, 70, 16, body); // подлокотники
    R(c, -108, -50, 216, 40, 12, body);                      // сиденье
    R(c, -108, -42, 216, 34, 8, o.seat || '#6A5CC6');
    if (o.pillow !== false) { R(c, -96, -78, 52, 30, 12, '#8E8CFF', '#D9D7FF', 1.6); }
    c.restore();
  },
  phone(g, x, y, s = 1, rot = 0, screen = 'yellow') {
    const c = g.c; c.save(); c.translate(x, y); c.rotate(rot * RAD); c.scale(s, s);
    R(c, -47, -80, 94, 160, 14, '#12102C', '#E6E3FF', 2.4);
    const P = { yellow: '#FFC93C', dark: '#2C3A5E', pink: '#FF7AA2', orange: '#FF9F4A', blue: '#7FB0FF', off: '#0E0C22', red: '#FF4A63' }[screen] || '#FFC93C';
    R(c, -40, -73, 80, 146, 9, P, P, 0);
    c.fillStyle = 'rgba(20,16,50,.55)'; c.fillRect(-30, -62, 52, 5); c.fillRect(-30, -52, 36, 5);
    if (screen !== 'off') {
      c.fillStyle = 'rgba(25,20,60,.85)'; c.strokeStyle = 'rgba(25,20,60,.85)';
      if (screen === 'yellow' || screen === 'blue') { c.beginPath(); c.arc(0, 4, 26, 0, TAU); c.fillStyle = 'rgba(0,0,0,.18)'; c.fill(); c.fillStyle = '#1B1840'; c.fillRect(-12, -6, 5, 7); c.fillRect(7, -6, 5, 7); c.lineWidth = 3; c.beginPath(); c.arc(0, 8, 13, .15 * Math.PI, .85 * Math.PI); c.stroke(); }
      else if (screen === 'orange' || screen === 'dark') { c.fillStyle = '#12102C'; c.beginPath(); c.arc(0, 8, 24, 0, TAU); c.fill(); c.beginPath(); c.moveTo(-22, -6); c.lineTo(-24, -26); c.lineTo(-8, -14); c.fill(); c.beginPath(); c.moveTo(22, -6); c.lineTo(24, -26); c.lineTo(8, -14); c.fill(); c.fillStyle = '#FFE9A0'; c.fillRect(-12, 2, 6, 6); c.fillRect(7, 2, 6, 6); }
      else if (screen === 'pink') { c.fillStyle = '#4C4C8F'; c.beginPath(); c.arc(0, 8, 24, 0, TAU); c.fill(); c.fillStyle = '#FF3B55'; c.beginPath(); c.arc(0, 8, 6, 0, TAU); c.fill(); c.beginPath(); c.arc(-24, -4, 8, 0, TAU); c.fill(); c.fillStyle = '#3D7DFF'; c.beginPath(); c.arc(24, -4, 8, 0, TAU); c.fill(); }
      else if (screen === 'red') { c.fillStyle = '#fff'; c.font = `800 60px ${FONT}`; c.textAlign = 'center'; c.fillText('!', 0, 26); }
    }
    c.fillStyle = screen === 'off' ? '#2A2850' : '#FF4A63'; c.beginPath(); c.arc(22, 56, 4.2, 0, TAU); c.fill();
    c.restore();
  },
  box(g, x, gnd, s = 1, open) { // коробка из-под пиццы
    const c = g.c; c.save(); c.translate(x, gnd); c.scale(s, s);
    c.beginPath(); c.moveTo(-42, -10); c.lineTo(-30, -44); c.lineTo(30, -44); c.lineTo(42, -10); c.closePath(); fillStroke(c, '#D9A66A', '#F0CDA0', 1.6);
    R(c, -52, -12, 104, 12, 2, '#C8924E', '#F0CDA0', 1.6);
    c.fillStyle = '#8C5E2C'; c.fillRect(-18, -34, 36, 3); c.fillRect(-12, -27, 24, 3); c.restore();
  },
  table(g, x, gnd, w = 330, h = 92, o = {}) {
    const c = g.c; c.save(); c.translate(x, gnd);
    const top = o.top || '#4A4690';
    c.fillStyle = '#2D2A66'; c.fillRect(-w / 2 + 12, -h, 9, h); c.fillRect(w / 2 - 21, -h, 9, h);
    c.strokeStyle = OUT; c.lineWidth = 1.8; c.strokeRect(-w / 2 + 12, -h, 9, h); c.strokeRect(w / 2 - 21, -h, 9, h);
    R(c, -w / 2, -h - 11, w, 13, 4, top);
    if (o.cloth) { c.beginPath(); c.moveTo(-w / 2 + 6, -h - 2); c.lineTo(-w / 2 + 6, -h + 34); for (let i = 0; i <= 12; i++) c.lineTo(-w / 2 + 6 + i * ((w - 12) / 12), -h + 34 - (i % 2) * 8); c.lineTo(w / 2 - 6, -h - 2); c.closePath(); fillStroke(c, o.cloth, '#F0E8FF', 1.6); }
    c.restore();
  },
  chair(g, x, gnd, s = 1, f = 1, col = '#5B4FB0') {
    const c = g.c; c.save(); c.translate(x, gnd); c.scale(s * f, s);
    c.fillStyle = col; c.strokeStyle = OUT; c.lineWidth = 2;
    c.fillRect(-18, -50, 5, 50); c.fillRect(13, -50, 5, 50); c.strokeRect(-18, -50, 5, 50); c.strokeRect(13, -50, 5, 50);
    R(c, -22, -56, 44, 9, 3, col); R(c, -24, -108, 8, 56, 3, col);
    c.restore();
  },
  candle(g, x, y, s = 1, t = 0) {
    const c = g.c; c.save(); c.translate(x, y); c.scale(s, s);
    glowCircle(c, 0, -26, 38, 'rgba(255,190,80,A)', .5);
    R(c, -4, -16, 8, 20, 2, '#F4F2FF', '#fff', 1);
    const fl = 1 + Math.sin(t * 13 + x) * .12;
    c.fillStyle = '#FFC93C'; c.beginPath(); c.ellipse(0, -24, 4.2, 9 * fl, 0, 0, TAU); c.fill();
    c.fillStyle = '#FF9F4A'; c.beginPath(); c.ellipse(0, -22, 2, 5 * fl, 0, 0, TAU); c.fill();
    c.restore();
  },
  cake(g, x, y, s = 1, o = {}) {
    const c = g.c; c.save(); c.translate(x, y); c.scale(s, s);
    R(c, -34, -26, 68, 26, 6, '#FF9FBC', '#FFD2E0', 1.8);
    R(c, -26, -46, 52, 22, 6, '#FFF0F5', '#fff', 1.8);
    c.fillStyle = '#FF3B55'; c.beginPath(); c.arc(0, -52, 5, 0, TAU); c.fill();
    c.restore();
  },
  plate(g, x, y, s = 1) { const c = g.c; c.save(); c.translate(x, y); c.scale(s, s); c.beginPath(); c.ellipse(0, 0, 22, 5, 0, 0, TAU); fillStroke(c, '#EDEBFF', '#fff', 1.2); c.beginPath(); c.ellipse(0, -1, 13, 2.6, 0, 0, TAU); fillStroke(c, '#C9C6FF', '#C9C6FF', 0); c.restore(); },
  cup(g, x, y, s = 1, col = '#FF7AA2') { const c = g.c; c.save(); c.translate(x, y); c.scale(s, s); R(c, -10, -18, 20, 18, 4, col, '#fff', 1.4); c.strokeStyle = '#fff'; c.lineWidth = 2.4; c.beginPath(); c.arc(11, -9, 6, -1.4, 1.4); c.stroke(); c.restore(); },
  soup(g, x, y, s = 1, t = 0) { const c = g.c; c.save(); c.translate(x, y); c.scale(s, s); c.beginPath(); c.moveTo(-18, -12); c.quadraticCurveTo(0, 14, 18, -12); c.closePath(); fillStroke(c, '#FFFFFF', '#fff', 1); c.fillStyle = '#FFB36B'; c.beginPath(); c.ellipse(0, -12, 18, 3.4, 0, 0, TAU); c.fill(); c.strokeStyle = 'rgba(255,255,255,.5)'; c.lineWidth = 2; for (let i = -1; i <= 1; i++) { c.beginPath(); c.moveTo(i * 8, -18); c.quadraticCurveTo(i * 8 + 5, -26 - Math.sin(t * 3 + i) * 3, i * 8, -34); c.stroke(); } c.restore(); },
  chandelier(g, x, y, t) { const c = g.c; c.save(); c.translate(x, y); c.strokeStyle = '#E8D9A8'; c.lineWidth = 2; c.beginPath(); c.moveTo(0, -60); c.lineTo(0, 0); c.stroke(); c.beginPath(); c.arc(0, 8, 46, Math.PI * .1, Math.PI * .9); c.stroke(); for (let i = -2; i <= 2; i++) { glowCircle(c, i * 21, 6 + Math.abs(i) * 5, 22, 'rgba(255,200,100,A)', .55); c.fillStyle = '#FFE9A0'; c.beginPath(); c.arc(i * 21, 6 + Math.abs(i) * 5, 4, 0, TAU); c.fill(); } c.restore(); },
  zzz(g, x, y, t, col = '#EDEBFF') { const c = g.c; for (let i = 0; i < 3; i++) { const p = ((t * .6 + i / 3) % 1); txt(c, 'Z', x + 18 * i + Math.sin(p * 6) * 4, y - p * 70, { size: 18 + i * 7, w: 800, col, a: Math.sin(p * Math.PI) }); } },
  hearts(g, x, y, t, n = 5, spread = 80) { const c = g.c; for (let i = 0; i < n; i++) { const p = ((t * .45 + i / n) % 1); const hx = x + Math.sin(i * 7.3) * spread, hy = y - p * 120; const r = 7 + (i % 3) * 3; c.save(); c.globalAlpha = Math.sin(p * Math.PI); c.fillStyle = '#FF6FA0'; c.translate(hx, hy); c.beginPath(); c.moveTo(0, r * .5); c.bezierCurveTo(-r * 1.4, -r * .5, -r * .6, -r * 1.3, 0, -r * .45); c.bezierCurveTo(r * .6, -r * 1.3, r * 1.4, -r * .5, 0, r * .5); c.fill(); c.restore(); } },
  sweat(g, x, y, t) { const c = g.c; const p = (t * 1.2) % 1; c.fillStyle = '#7FB6FF'; c.globalAlpha = 1 - p; c.beginPath(); c.ellipse(x, y + p * 18, 3, 5, 0, 0, TAU); c.fill(); c.globalAlpha = 1; },
  anger(g, x, y, t) { const c = g.c; c.save(); c.translate(x, y); c.scale(1 + .1 * Math.sin(t * 14), 1 + .1 * Math.sin(t * 14)); c.strokeStyle = '#FF4A63'; c.lineWidth = 3; c.lineCap = 'round'; for (const a of [0, 90]) { c.beginPath(); c.arc(a ? 6 : -6, a ? 6 : -6, 7, a ? Math.PI : 0, a ? 1.5 * Math.PI : .5 * Math.PI); c.stroke(); } c.restore(); },
  sparkles(g, cx, cy, t, n = 7, R0 = 80) {
    const c = g.c; for (let i = 0; i < n; i++) { const ph = i * 2.1, tt = (Math.sin(t * 2.3 + ph) + 1) / 2; const a = i * 2.4 + t * .3, r = R0 * (.5 + (i % 3) * .3); c.save(); c.globalAlpha = tt; star(c, cx + Math.cos(a) * r, cy + Math.sin(a) * r * .9, 5 + (i % 3) * 3, i % 2 ? '#FFD66B' : '#E8E4FF', t); c.restore(); }
  },
  bone(g, x, y, s = 1, rot = 0) { const c = g.c; c.save(); c.translate(x, y); c.rotate(rot * RAD); c.scale(s, s); c.fillStyle = '#F4EAD0'; c.strokeStyle = '#fff'; c.lineWidth = 1.2; R(c, -18, -4, 36, 8, 4, '#F4EAD0', '#fff', 1); for (const sx of [-1, 1]) for (const sy of [-1, 1]) { c.beginPath(); c.arc(sx * 18, sy * 5, 5.5, 0, TAU); fillStroke(c, '#F4EAD0', '#fff', 1); } c.restore(); },
  slipper(g, x, y, s = 1, torn) { const c = g.c; c.save(); c.translate(x, y); c.scale(s, s); c.beginPath(); c.moveTo(-26, 0); c.quadraticCurveTo(-30, -18, -8, -18); c.quadraticCurveTo(18, -18, 30, -4); c.lineTo(30, 0); c.closePath(); fillStroke(c, '#FF7AA2', '#FFC2D6', 1.6); if (torn) { c.fillStyle = '#12102C'; c.beginPath(); c.moveTo(-6, -18); c.lineTo(0, -8); c.lineTo(8, -16); c.closePath(); c.fill(); } c.restore(); },
  pillow(g, x, y, s = 1, rot = 0, col = '#8E8CFF') { const c = g.c; c.save(); c.translate(x, y); c.rotate(rot * RAD); c.scale(s, s); R(c, -26, -17, 52, 34, 12, col, '#D9D7FF', 1.6); c.restore(); },
  feathers(g, x, y, t, n = 9) { const c = g.c; for (let i = 0; i < n; i++) { const p = ((t * .35 + i / n) % 1); c.save(); c.globalAlpha = Math.sin(p * Math.PI) * .9; c.translate(x + Math.sin(i * 5.1 + p * 6) * 70, y - 60 + p * 120); c.rotate(p * 6 + i); c.fillStyle = '#F4F2FF'; c.beginPath(); c.ellipse(0, 0, 7, 2.4, 0, 0, TAU); c.fill(); c.restore(); } },
  bowl(g, x, y, s = 1) { const c = g.c; c.save(); c.translate(x, y); c.scale(s, s); c.beginPath(); c.moveTo(-18, -12); c.lineTo(-13, 0); c.lineTo(13, 0); c.lineTo(18, -12); c.closePath(); fillStroke(c, '#FF9F4A', '#FFD0A0', 1.6); c.fillStyle = '#7A4A2A'; c.beginPath(); c.ellipse(0, -12, 16, 3.5, 0, 0, TAU); c.fill(); c.restore(); },
  plant(g, x, gnd, s = 1) { const c = g.c; c.save(); c.translate(x, gnd); c.scale(s, s); c.beginPath(); c.moveTo(-18, -34); c.lineTo(-13, 0); c.lineTo(13, 0); c.lineTo(18, -34); c.closePath(); fillStroke(c, '#C86A4A', '#F0A98A', 1.6); c.fillStyle = '#3FD4B4'; c.strokeStyle = '#B8FFEA'; c.lineWidth = 1.4; for (const a of [-50, -20, 10, 40]) { c.save(); c.translate(0, -34); c.rotate(a * RAD); c.beginPath(); c.ellipse(0, -30, 9, 30, 0, 0, TAU); c.fill(); c.stroke(); c.restore(); } c.restore(); },
  lamp(g, x, gnd, s = 1, on = true) { const c = g.c; c.save(); c.translate(x, gnd); c.scale(s, s); c.fillStyle = '#6A62C8'; c.fillRect(-2, -130, 4, 130); R(c, -14, -6, 28, 6, 2, '#6A62C8'); c.beginPath(); c.moveTo(-26, -112); c.lineTo(26, -112); c.lineTo(16, -146); c.lineTo(-16, -146); c.closePath(); fillStroke(c, '#FFD66B', '#FFF0B0', 1.6); if (on) glowCircle(c, 0, -110, 110, 'rgba(255,214,107,A)', .28); c.restore(); },
  clock(g, x, y, r = 22, tt = 0) { const c = g.c; c.save(); c.translate(x, y); c.beginPath(); c.arc(0, 0, r, 0, TAU); fillStroke(c, '#1A1840', '#E7E4FF', 2.4); c.strokeStyle = '#fff'; c.lineWidth = 2.2; c.lineCap = 'round'; c.beginPath(); c.moveTo(0, 0); c.lineTo(Math.sin(tt * .6) * r * .5, -Math.cos(tt * .6) * r * .5); c.stroke(); c.beginPath(); c.moveTo(0, 0); c.lineTo(Math.sin(tt * 7) * r * .78, -Math.cos(tt * 7) * r * .78); c.strokeStyle = '#FF4A63'; c.lineWidth = 1.6; c.stroke(); c.restore(); },
  frame(g, x, y, w, h, col = '#FFC93C') { const c = g.c; R(c, x, y, w, h, 4, '#1A1840', '#E7E4FF', 2.2); c.fillStyle = col; c.globalAlpha = .75; c.fillRect(x + 6, y + 6, w - 12, h - 12); c.globalAlpha = 1; },
  piggy(g, x, gnd, s = 1, full = .5) { const c = g.c; c.save(); c.translate(x, gnd); c.scale(s, s); c.beginPath(); c.ellipse(0, -30, 34, 26, 0, 0, TAU); fillStroke(c, '#FF9FBC', '#FFD2E0', 2); c.fillStyle = '#FF9FBC'; c.strokeStyle = '#FFD2E0'; c.lineWidth = 1.6; c.beginPath(); c.moveTo(-26, -48); c.lineTo(-20, -62); c.lineTo(-12, -50); c.closePath(); c.fill(); c.stroke(); R(c, 28, -38, 14, 14, 5, '#FF7AA2', '#FFD2E0', 1.5); c.fillStyle = '#1A1840'; c.beginPath(); c.arc(16, -40, 2.4, 0, TAU); c.fill(); c.fillRect(-12, -52, 22, 3); c.fillStyle = '#FF9FBC'; c.fillRect(-22, -8, 8, 10); c.fillRect(14, -8, 8, 10); c.strokeRect(-22, -8, 8, 10); c.strokeRect(14, -8, 8, 10); c.restore(); },
  coin(g, x, y, r = 10, rot = 0) { const c = g.c; c.save(); c.translate(x, y); c.scale(Math.cos(rot) * .85 + .15, 1); c.beginPath(); c.arc(0, 0, r, 0, TAU); fillStroke(c, '#FFC93C', '#FFF0A0', 1.6); c.fillStyle = '#C8901C'; c.font = `800 ${r * 1.2}px ${FONT}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('₽', 0, 1); c.restore(); },
  router(g, x, gnd, s = 1, on = true, t = 0) { const c = g.c; c.save(); c.translate(x, gnd); c.scale(s, s); R(c, -34, -20, 68, 20, 5, '#2C2A5E'); c.strokeStyle = OUT; c.lineWidth = 2.2; c.beginPath(); c.moveTo(-22, -20); c.lineTo(-26, -52); c.moveTo(22, -20); c.lineTo(26, -52); c.stroke(); for (let i = 0; i < 3; i++) { c.fillStyle = on ? '#3FD4B4' : '#3A3A60'; c.beginPath(); c.arc(-14 + i * 14, -9, 2.8, 0, TAU); c.fill(); } if (on) { c.strokeStyle = '#3FD4B4'; c.lineWidth = 2.4; for (let i = 1; i <= 3; i++) { c.globalAlpha = .4 + .6 * ((Math.sin(t * 4 - i) + 1) / 2); c.beginPath(); c.arc(0, -52, 14 + i * 12, -2.2, -.94); c.stroke(); } c.globalAlpha = 1; } c.restore(); },
  wifiX(g, x, y, s = 1) { const c = g.c; c.save(); c.translate(x, y); c.scale(s, s); c.strokeStyle = '#B8B6E8'; c.lineWidth = 3; c.lineCap = 'round'; for (let i = 1; i <= 3; i++) { c.beginPath(); c.arc(0, 8, 8 + i * 10, -2.2, -.94); c.stroke(); } c.fillStyle = '#B8B6E8'; c.beginPath(); c.arc(0, 8, 3, 0, TAU); c.fill(); c.strokeStyle = '#FF4A63'; c.lineWidth = 4; c.beginPath(); c.moveTo(-28, -26); c.lineTo(28, 22); c.stroke(); c.restore(); },
  belt(g, x, y, s = 1, rot = 0) { const c = g.c; c.save(); c.translate(x, y); c.rotate(rot * RAD); c.scale(s, s); R(c, -4, -2, 8, 74, 3, '#8C5E2C', '#C99A5A', 1.4); R(c, -8, -8, 16, 16, 3, '#FFC93C', '#FFF0A0', 1.4); c.fillStyle = '#5A3A18'; for (let i = 0; i < 4; i++) { c.beginPath(); c.arc(0, 24 + i * 11, 1.8, 0, TAU); c.fill(); } c.restore(); },
  broom(g, x, gnd, s = 1, rot = 0) { const c = g.c; c.save(); c.translate(x, gnd); c.rotate(rot * RAD); c.scale(s, s); c.strokeStyle = '#C99A5A'; c.lineWidth = 5; c.lineCap = 'round'; c.beginPath(); c.moveTo(0, 0); c.lineTo(0, -120); c.stroke(); c.beginPath(); c.moveTo(-18, 0); c.lineTo(-10, -26); c.lineTo(10, -26); c.lineTo(18, 0); c.closePath(); fillStroke(c, '#E0B44A', '#FFE08A', 1.6); c.restore(); },
  dishes(g, x, y, s = 1) { const c = g.c; c.save(); c.translate(x, y); c.scale(s, s); for (let i = 0; i < 4; i++) { c.beginPath(); c.ellipse(0, -i * 7, 24, 5, 0, 0, TAU); fillStroke(c, i % 2 ? '#EDEBFF' : '#C9C6FF', '#fff', 1.2); } c.restore(); },
  bucket(g, x, gnd, s = 1) { const c = g.c; c.save(); c.translate(x, gnd); c.scale(s, s); c.beginPath(); c.moveTo(-20, -34); c.lineTo(-15, 0); c.lineTo(15, 0); c.lineTo(20, -34); c.closePath(); fillStroke(c, '#4C7DFF', '#B8D0FF', 1.8); c.strokeStyle = '#B8D0FF'; c.lineWidth = 2; c.beginPath(); c.arc(0, -34, 20, Math.PI, TAU); c.stroke(); c.restore(); },
  bubbles(g, x, y, t, n = 6) { const c = g.c; for (let i = 0; i < n; i++) { const p = ((t * .5 + i / n) % 1); c.strokeStyle = 'rgba(190,230,255,.9)'; c.lineWidth = 1.6; c.globalAlpha = Math.sin(p * Math.PI); c.beginPath(); c.arc(x + Math.sin(i * 3.3 + p * 4) * 24, y - p * 70, 4 + (i % 3) * 3, 0, TAU); c.stroke(); } c.globalAlpha = 1; },
  backpack(g, x, y, s = 1) { const c = g.c; c.save(); c.translate(x, y); c.scale(s, s); R(c, -22, -34, 44, 62, 14, '#FF7AA2', '#FFC2D6', 2); R(c, -15, -8, 30, 24, 6, '#E5558A', '#FFC2D6', 1.4); c.strokeStyle = '#FFC2D6'; c.lineWidth = 2; c.beginPath(); c.moveTo(-12, -14); c.lineTo(12, -14); c.stroke(); c.restore(); },
  doorSchool(g, x, gnd, s = 1, open = 0) { const c = g.c; c.save(); c.translate(x, gnd); c.scale(s, s); R(c, -120, -250, 240, 250, 6, '#3A3A8A'); c.fillStyle = '#FFE08A'; for (let i = 0; i < 3; i++) for (let j = 0; j < 2; j++) { c.fillRect(-100 + i * 70, -230 + j * 70, 44, 44); c.strokeStyle = '#fff'; c.lineWidth = 1.5; c.strokeRect(-100 + i * 70, -230 + j * 70, 44, 44); } R(c, -46, -86, 92, 86, 4, '#13112B', '#fff', 2); c.save(); c.translate(-46, 0); c.scale(1 - open * .85, 1); R(c, 0, -86, 46, 86, 2, '#6C74FF', '#fff', 1.6); c.restore(); c.save(); c.translate(46, 0); c.scale(1 - open * .85, 1); R(c, -46, -86, 46, 86, 2, '#6C74FF', '#fff', 1.6); c.restore(); txt(c, 'ШКОЛА', 0, -108, { size: 20, w: 800, ls: 3, col: '#fff' }); c.restore(); },
  briefcase(g, x, gnd, s = 1) { const c = g.c; c.save(); c.translate(x, gnd); c.scale(s, s); c.strokeStyle = '#C9C6FF'; c.lineWidth = 3; c.beginPath(); c.arc(0, -34, 11, Math.PI, TAU); c.stroke(); R(c, -26, -34, 52, 34, 6, '#8C5E2C', '#E0B070', 1.8); c.fillStyle = '#FFC93C'; c.fillRect(-4, -22, 8, 6); c.restore(); },
  gamepad(g, x, y, s = 1, rot = 0) { const c = g.c; c.save(); c.translate(x, y); c.rotate(rot * RAD); c.scale(s, s); c.beginPath(); c.moveTo(-26, -8); c.quadraticCurveTo(-36, 18, -22, 14); c.lineTo(-10, 4); c.lineTo(10, 4); c.lineTo(22, 14); c.quadraticCurveTo(36, 18, 26, -8); c.quadraticCurveTo(0, -16, -26, -8); fillStroke(c, '#4C7DFF', '#B8D0FF', 1.8); c.fillStyle = '#fff'; c.fillRect(-20, -6, 10, 3); c.fillRect(-17, -9, 3, 10); c.fillStyle = '#FFC93C'; c.beginPath(); c.arc(16, -5, 2.4, 0, TAU); c.arc(21, -2, 2.4, 0, TAU); c.fill(); c.restore(); },
  tv(g, x, y, w = 110, h = 70, col = '#A8C4FF') { const c = g.c; R(c, x, y, w, h, 6, '#12102C', '#E7E4FF', 2.4); R(c, x + 6, y + 6, w - 12, h - 12, 3, col, col, 0); },
  boombox(g, x, y, s = 1, t = 0) { const c = g.c; c.save(); c.translate(x, y); c.scale(s, s); R(c, -34, -20, 68, 40, 6, '#4C4C8F', '#C9C6FF', 2); for (const sx of [-18, 18]) { const k = 1 + Math.sin(t * 16) * .06; c.beginPath(); c.arc(sx, 2, 13 * k, 0, TAU); fillStroke(c, '#12102C', '#C9C6FF', 1.6); c.beginPath(); c.arc(sx, 2, 4, 0, TAU); c.fillStyle = '#C9C6FF'; c.fill(); } R(c, -10, -16, 20, 9, 2, '#FFC93C', '#FFF0A0', 1); c.restore(); },
  notes(g, x, y, t, n = 5) { const c = g.c; for (let i = 0; i < n; i++) { const p = ((t * .6 + i / n) % 1); c.save(); c.globalAlpha = Math.sin(p * Math.PI); c.fillStyle = i % 2 ? '#FF7AA2' : '#8E8EFF'; c.translate(x + Math.sin(i * 4 + p * 5) * 40, y - p * 80); c.beginPath(); c.ellipse(0, 0, 5.5, 4, -.4, 0, TAU); c.fill(); c.fillRect(4, -14, 2, 14); c.restore(); } },
  poster(g, x, y, w, h, col = '#FF4A63') { const c = g.c; c.save(); c.translate(x, y); c.fillStyle = col; c.fillRect(0, 0, w, h); c.strokeStyle = '#fff'; c.lineWidth = 2; c.strokeRect(0, 0, w, h); c.fillStyle = '#12102C'; c.beginPath(); c.arc(w / 2, h * .38, w * .22, 0, TAU); c.fill(); c.fillRect(w * .28, h * .56, w * .44, h * .3); c.restore(); },
  teaset(g, x, gnd, s = 1) { const c = g.c; c.save(); c.translate(x, gnd); c.scale(s, s); c.fillStyle = '#FFB3D1'; c.strokeStyle = '#fff'; c.lineWidth = 1.6; c.fillRect(-30, -52, 5, 52); c.fillRect(25, -52, 5, 52); R(c, -42, -62, 84, 12, 4, '#FF9FBC'); Pr.cup(g, x - 16 * s, gnd - 62 * s, s, '#FFE9A0'); Pr.cup(g, x + 14 * s, gnd - 62 * s, s, '#FFE9A0'); c.restore(); },
  teddy(g, x, y, s = 1) { const c = g.c; c.save(); c.translate(x, y); c.scale(s, s); c.fillStyle = '#C8864A'; c.strokeStyle = '#F0C090'; c.lineWidth = 1.6; for (const sx of [-1, 1]) { c.beginPath(); c.arc(sx * 11, -26, 6, 0, TAU); fillStroke(c, '#C8864A', '#F0C090', 1.4); } c.beginPath(); c.arc(0, -18, 14, 0, TAU); fillStroke(c, '#C8864A', '#F0C090', 1.6); c.beginPath(); c.ellipse(0, 10, 15, 18, 0, 0, TAU); fillStroke(c, '#C8864A', '#F0C090', 1.6); c.fillStyle = '#1A1840'; c.fillRect(-6, -21, 3, 3); c.fillRect(3, -21, 3, 3); c.restore(); },
  papers(g, x, gnd, s = 1, h = 40) { const c = g.c; c.save(); c.translate(x, gnd); c.scale(s, s); for (let i = 0; i < h / 5; i++) R(c, -22 + (i % 2) * 2, -i * 5 - 4, 44, 5, 1, i % 3 ? '#EDEBFF' : '#C9C6FF', '#fff', .8); c.restore(); },
  trophy(g, x, y, s = 1) { const c = g.c; c.save(); c.translate(x, y); c.scale(s, s); c.beginPath(); c.moveTo(-18, -34); c.lineTo(18, -34); c.quadraticCurveTo(16, -4, 0, -2); c.quadraticCurveTo(-16, -4, -18, -34); fillStroke(c, '#FFC93C', '#FFF0A0', 1.8); c.fillRect(-3, -2, 6, 12); R(c, -12, 8, 24, 6, 2, '#FFC93C', '#FFF0A0', 1.4); c.restore(); },
  heartIcon(g, x, y, r, col = '#FF6FA0') { const c = g.c; c.save(); c.translate(x, y); c.fillStyle = col; c.beginPath(); c.moveTo(0, r * .5); c.bezierCurveTo(-r * 1.4, -r * .5, -r * .6, -r * 1.3, 0, -r * .45); c.bezierCurveTo(r * .6, -r * 1.3, r * 1.4, -r * .5, 0, r * .5); c.fill(); c.restore(); },
  bag(g, x, gnd, s = 1, col = '#4C7DFF') { const c = g.c; c.save(); c.translate(x, gnd); c.scale(s, s); c.strokeStyle = '#C9C6FF'; c.lineWidth = 3; c.beginPath(); c.arc(0, -36, 10, Math.PI, TAU); c.stroke(); R(c, -20, -38, 40, 38, 4, col, '#C9D6FF', 1.8); c.restore(); },
  ruler(g, x, y, len, rot = 0) { const c = g.c; c.save(); c.translate(x, y); c.rotate(rot * RAD); R(c, 0, -5, len, 10, 1.5, '#FFE08A', '#fff', 1); c.fillStyle = '#7A5A10'; for (let i = 0; i < len; i += 8) c.fillRect(i, -5, 1.2, i % 16 ? 3.5 : 6); c.restore(); },
  sandwich(g, x, y, s = 1) { const c = g.c; c.save(); c.translate(x, y); c.scale(s, s); R(c, -16, -9, 32, 6, 2, '#E8C48A', '#fff', 1); R(c, -15, -4, 30, 4, 1, '#7CE08A', '#7CE08A', 0); R(c, -16, -1, 32, 6, 2, '#E8C48A', '#fff', 1); c.restore(); },
  book(g, x, y, s = 1, col = '#4C7DFF') { const c = g.c; c.save(); c.translate(x, y); c.scale(s, s); R(c, -18, -24, 36, 24, 3, col, '#fff', 1.4); c.fillStyle = '#fff'; c.fillRect(-10, -15, 20, 2.4); c.fillRect(-10, -10, 14, 2.4); c.restore(); },
  glow(g, x, y, r, a = .3, col = 'rgba(255,214,107,A)') { glowCircle(g.c, x, y, r, col, a); },
};
