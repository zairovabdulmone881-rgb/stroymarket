/* Движок ролика «Два сценария, один таймер» — 720x1280, 30 c, 30 fps */
const W = 720, H = 1280, DUR = 30;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
const RAD = Math.PI / 180, TAU = Math.PI * 2;
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const ease = t => (t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
const eo = t => 1 - Math.pow(1 - t, 3);
const back = t => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); };
const FONT = 'Inter, "Helvetica Neue", Arial, sans-serif';

/* ---------- ключевые кадры ---------- */
function kf(t, keys) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    if (t <= keys[i][0]) {
      const [t0, v0] = keys[i - 1], [t1, v1] = keys[i];
      return lerp(v0, v1, ease((t - t0) / (t1 - t0)));
    }
  }
  return keys[keys.length - 1][1];
}
function kfl(t, keys) { // линейная
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    if (t <= keys[i][0]) {
      const [t0, v0] = keys[i - 1], [t1, v1] = keys[i];
      return lerp(v0, v1, (t - t0) / (t1 - t0));
    }
  }
  return keys[keys.length - 1][1];
}
const tw = (t, a, b) => ease(clamp((t - a) / (b - a)));          // 0→1 между a и b
const inWin = (t, a, b) => t >= a && t < b;

/* ---------- примитивы ---------- */
function rr(c, x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  c.beginPath();
  c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
  c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
}
function glowCircle(c, x, y, r, col, a = 1) {
  const g = c.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, col.replace('A', a)); g.addColorStop(1, col.replace('A', 0));
  c.fillStyle = g; c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill();
}
function star(c, x, y, r, col, rot = 0) {
  c.save(); c.translate(x, y); c.rotate(rot); c.fillStyle = col; c.beginPath();
  for (let i = 0; i < 8; i++) { const rad = i % 2 ? r * .22 : r; const a = i * Math.PI / 4; c.lineTo(Math.cos(a) * rad, Math.sin(a) * rad); }
  c.closePath(); c.fill(); c.restore();
}
function txt(c, s, x, y, o = {}) {
  c.save();
  c.font = `${o.w || 700} ${o.size || 20}px ${FONT}`;
  c.textAlign = o.align || 'center'; c.textBaseline = o.base || 'middle';
  if (o.ls) c.letterSpacing = o.ls + 'px'; else c.letterSpacing = '0px';
  if (o.shadow) { c.shadowColor = o.shadow; c.shadowBlur = o.sb || 12; }
  c.fillStyle = o.col || '#F2F0FF'; c.globalAlpha *= (o.a == null ? 1 : o.a);
  let size = o.size || 20;
  if (o.maxW) { // сжать по ширине
    let m = c.measureText(s).width;
    if (m > o.maxW) { size = size * o.maxW / m; c.font = `${o.w || 700} ${size}px ${FONT}`; }
  }
  c.fillText(s, x, y); c.restore();
}

/* ---------- скелет-силуэт ---------- */
const LEN = { torso: 62, up: 38, fore: 40, thigh: 50, shin: 52 };
const POSE = {
  stand:   { hy: 102, hx: 0, tor: 0, hd: 0, aF: [6, 8], aB: [-6, 8], lF: [3, -2], lB: [-3, -2], rot: 0, face: 'smile' },
  proud:   { hy: 102, hx: 0, tor: -3, hd: -4, aF: [14, 10], aB: [-14, 10], lF: [5, -2], lB: [-5, -2], rot: 0, face: 'smile' },
  reach:   { hy: 102, hx: 0, tor: 8, hd: 4, aF: [88, 0], aB: [-6, 10], lF: [8, -4], lB: [-10, -6], rot: 0, face: 'smile' },
  reach2:  { hy: 102, hx: 0, tor: 12, hd: 6, aF: [95, 4], aB: [40, 40], lF: [10, -6], lB: [-12, -8], rot: 0, face: 'worry' },
  lean:    { hy: 100, hx: 0, tor: 16, hd: 8, aF: [60, 30], aB: [30, 40], lF: [8, -4], lB: [-8, -4], rot: 0, face: 'worry' },
  kneel:   { hy: 56, hx: 0, tor: 6, hd: 8, aF: [70, 80], aB: [60, 90], lF: [60, -90], lB: [-6, -86], rot: 0, face: 'cry' },
  beg:     { hy: 56, hx: 0, tor: 8, hd: 6, aF: [78, 100], aB: [70, 108], lF: [62, -88], lB: [-6, -84], rot: 0, face: 'cry' },
  sit:     { hy: 52, hx: 0, tor: 0, hd: 0, aF: [20, 40], aB: [-4, 30], lF: [88, -88], lB: [80, -84], rot: 0, face: 'smile' },
  sitslump:{ hy: 50, hx: 0, tor: 22, hd: 22, aF: [24, 30], aB: [10, 30], lF: [88, -88], lB: [84, -84], rot: 0, face: 'sad' },
  sitread: { hy: 52, hx: 0, tor: 6, hd: 14, aF: [34, 80], aB: [20, 80], lF: [88, -88], lB: [80, -84], rot: 0, face: 'smile' },
  lie:     { hy: 22, hx: 0, tor: 0, hd: 6, aF: [30, 60], aB: [-20, 40], lF: [4, -2], lB: [10, -14], rot: -90, face: 'smirk' },
  lieph:   { hy: 22, hx: 0, tor: 0, hd: 6, aF: [160, 40], aB: [30, 50], lF: [4, -2], lB: [10, -14], rot: -90, face: 'smirk' },
  sleep:   { hy: 22, hx: 0, tor: 0, hd: 2, aF: [10, 20], aB: [-10, 20], lF: [3, -2], lB: [8, -8], rot: -90, face: 'sleep' },
  cheer:   { hy: 102, hx: 0, tor: -4, hd: -6, aF: [150, 10], aB: [-150, 10], lF: [8, -4], lB: [-8, -4], rot: 0, face: 'smile' },
  shrug:   { hy: 102, hx: 0, tor: 0, hd: 6, aF: [40, 100], aB: [-40, 100], lF: [3, -2], lB: [-3, -2], rot: 0, face: 'worry' },
  point:   { hy: 102, hx: 0, tor: 6, hd: 0, aF: [95, -10], aB: [-8, 10], lF: [4, -2], lB: [-4, -2], rot: 0, face: 'angry' },
  hands_up:{ hy: 102, hx: 0, tor: 0, hd: 0, aF: [170, 10], aB: [-170, 10], lF: [3, -2], lB: [-3, -2], rot: 0, face: 'shock' },
  facepalm:{ hy: 102, hx: 0, tor: 8, hd: 14, aF: [50, 118], aB: [-8, 8], lF: [3, -2], lB: [-3, -2], rot: 0, face: 'worry' },
  hold:    { hy: 102, hx: 0, tor: 0, hd: 0, aF: [34, 80], aB: [20, 80], lF: [3, -2], lB: [-3, -2], rot: 0, face: 'smile' },
  walkA:   { hy: 100, hx: 0, tor: 4, hd: 0, aF: [30, 10], aB: [-30, 10], lF: [28, -4], lB: [-24, -26], rot: 0, face: 'smile' },
  walkB:   { hy: 100, hx: 0, tor: 4, hd: 0, aF: [-30, 10], aB: [30, 10], lF: [-24, -26], lB: [28, -4], rot: 0, face: 'smile' },
  wave:    { hy: 102, hx: 0, tor: 0, hd: 0, aF: [150, 30], aB: [-6, 10], lF: [3, -2], lB: [-3, -2], rot: 0, face: 'smile' },
  hug:     { hy: 102, hx: 0, tor: 6, hd: 4, aF: [60, 50], aB: [40, 60], lF: [3, -2], lB: [-3, -2], rot: 0, face: 'smile' },
};
function mixPose(a, b, k) {
  const o = {};
  for (const key in a) {
    if (Array.isArray(a[key])) o[key] = a[key].map((v, i) => lerp(v, b[key][i], k));
    else if (typeof a[key] === 'number') o[key] = lerp(a[key], b[key], k);
    else o[key] = k < .5 ? a[key] : b[key];
  }
  return o;
}
function poseAt(t, keys) {
  const get = p => (typeof p === 'string' ? POSE[p] : { ...POSE.stand, ...p });
  if (t <= keys[0][0]) return get(keys[0][1]);
  for (let i = 1; i < keys.length; i++) {
    if (t <= keys[i][0]) {
      const [t0, p0] = keys[i - 1], [t1, p1] = keys[i];
      return mixPose(get(p0), get(p1), ease(clamp((t - t0) / (t1 - t0))));
    }
  }
  return get(keys[keys.length - 1][1]);
}
const dirv = (a, f) => [Math.sin(a * RAD) * f, Math.cos(a * RAD)];
const LINE = '#EDEBFF';

function person(g, o) {
  const c = g.c, s = o.s || 1.2, f = o.facing || 1, P = o.pose || POSE.stand, t = g.t;
  const br = 1 + .012 * Math.sin(t * 5 + (o.ph || 0));
  const pulse = o.noPulse ? 0 : g.pulse;
  const hip = [o.x + (P.hx || 0) * s, o.y - P.hy * s];
  const rot = (P.rot || 0) * RAD * f * (f < 0 ? 1 : 1);
  const rp = (p) => { // повернуть вокруг бедра
    const dx = p[0] - hip[0], dy = p[1] - hip[1];
    return [hip[0] + dx * Math.cos(rot) - dy * Math.sin(rot), hip[1] + dx * Math.sin(rot) + dy * Math.cos(rot)];
  };
  const add = (p, v, L) => [p[0] + v[0] * L * s, p[1] + v[1] * L * s];
  const upv = a => [Math.sin(a * RAD) * f, -Math.cos(a * RAD)];
  const tu = upv(P.tor), neck = add(hip, tu, LEN.torso * br);
  const sh = add(hip, tu, LEN.torso * .88 * br);
  const hu = upv(P.tor + P.hd), headR = (o.headR || 17) * s;
  const head = [neck[0] + hu[0] * (headR + 3 * s), neck[1] + hu[1] * (headR + 3 * s)];
  const limb = (a, b, L1, L2, from) => {
    const k = add(from, dirv(a, f), L1), e = add(k, dirv(a + b, f), L2);
    return [k, e];
  };
  const [kF, aFt] = limb(P.lF[0], P.lF[1], LEN.thigh, LEN.shin, hip);
  const [kB, aBt] = limb(P.lB[0], P.lB[1], LEN.thigh, LEN.shin, hip);
  const [eF, hF] = limb(P.aF[0], P.aF[1], LEN.up, LEN.fore, sh);
  const [eB, hB] = limb(P.aB[0], P.aB[1], LEN.up, LEN.fore, sh);
  const footF = [aFt[0] + 12 * s * f, aFt[1]], footB = [aBt[0] + 12 * s * f, aBt[1]];
  // применить поворот и сквош
  const T = {};
  const pts = { hip, neck, sh, head, kF, aFt, kB, aBt, eF, hF, eB, hB, footF, footB };
  for (const k in pts) T[k] = rot ? rp(pts[k]) : pts[k];
  const col = o.col || '#06050F', line = o.line || LINE, wl = (o.lw || 1) * s;
  c.save();
  // «резиновость»: сжатие/растяжение от точки опоры
  c.translate(o.x, o.y); c.scale(1 - pulse * .5, 1 + pulse); c.translate(-o.x, -o.y);
  const seg = (a, b, w) => {
    c.lineCap = 'round'; c.lineJoin = 'round';
    c.strokeStyle = line; c.lineWidth = w + 2.8; c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.stroke();
    c.strokeStyle = col; c.lineWidth = w; c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.stroke();
  };
  const segFill = (a, b, w) => { c.strokeStyle = col; c.lineWidth = w; c.lineCap = 'round'; c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.stroke(); };
  const lw = 5.6 * wl / s;
  // задние конечности
  seg(T.hip, T.kB, lw); seg(T.kB, T.aBt, lw); seg(T.aBt, T.footB, lw * .9);
  seg(T.sh, T.eB, lw * .9); seg(T.eB, T.hB, lw * .9);
  // торс
  seg(T.hip, T.neck, 8.2 * s);
  // передние
  seg(T.hip, T.kF, lw); seg(T.kF, T.aFt, lw); seg(T.aFt, T.footF, lw * .9);
  seg(T.sh, T.eF, lw * .9); seg(T.eF, T.hF, lw * .9);
  // кисти
  for (const h of [T.hF, T.hB]) { c.fillStyle = col; c.strokeStyle = line; c.lineWidth = 1.6; c.beginPath(); c.arc(h[0], h[1], 3.6 * s, 0, TAU); c.fill(); c.stroke(); }
  // голова
  const hx = T.head[0], hy = T.head[1], hr = headR;
  const tilt = (P.tor + P.hd) * RAD * f + rot;
  // причёска (сзади головы)
  c.save(); c.translate(hx, hy); c.rotate(tilt);
  const hair = o.hair || 'spiky';
  c.fillStyle = col; c.strokeStyle = line; c.lineWidth = 2.2;
  if (hair === 'spiky') {
    const n = 7;
    c.beginPath();
    for (let i = 0; i < n; i++) {
      const a0 = (-160 + i * (140 / (n - 1))) * RAD, a1 = (-160 + (i + .5) * (140 / (n - 1))) * RAD;
      const R1 = hr * (1.55 + (i % 2) * .3);
      c.lineTo(Math.cos(a0) * hr * .96, Math.sin(a0) * hr * .96);
      c.lineTo(Math.cos((a0 + a1) / 2) * R1, Math.sin((a0 + a1) / 2) * R1);
    }
    c.closePath(); c.fill(); c.stroke();
  } else if (hair === 'buns') {
    for (const sgn of [-1, 1]) { c.beginPath(); c.arc(sgn * hr * .8, -hr * 1.0, hr * .46, 0, TAU); c.fill(); c.stroke(); }
  } else if (hair === 'bun') {
    c.beginPath(); c.arc(-hr * .15, -hr * 1.18, hr * .5, 0, TAU); c.fill(); c.stroke();
  } else if (hair === 'pony') {
    c.beginPath(); c.moveTo(-hr * .6, -hr * .5); c.quadraticCurveTo(-hr * 2.0, -hr * .2, -hr * 1.5, hr * 1.4);
    c.quadraticCurveTo(-hr * 1.0, hr * .4, -hr * .9, hr * .1); c.closePath(); c.fill(); c.stroke();
  } else if (hair === 'short') {
    c.beginPath(); for (let i = 0; i < 6; i++) { const a = (-165 + i * 30) * RAD; c.lineTo(Math.cos(a) * hr, Math.sin(a) * hr); c.lineTo(Math.cos(a + 15 * RAD) * hr * 1.28, Math.sin(a + 15 * RAD) * hr * 1.28); }
    c.closePath(); c.fill(); c.stroke();
  } else if (hair === 'long') {
    c.beginPath(); c.moveTo(-hr * .9, -hr * .4); c.quadraticCurveTo(-hr * 1.8, hr * 1.3, -hr * .6, hr * 2.2);
    c.lineTo(hr * .4, hr * 1.2); c.closePath(); c.fill(); c.stroke();
  }
  c.beginPath(); c.arc(0, 0, hr, 0, TAU); c.fillStyle = col; c.fill(); c.strokeStyle = line; c.lineWidth = 2.4; c.stroke();
  // лицо
  const look = (o.look == null ? f * .35 : o.look) * hr * .35;
  face(c, P.face || 'smile', look, hr, t, o.ph || 0);
  // аксессуары на голове
  if (o.acc === 'crown') { c.fillStyle = '#FFC93C'; c.strokeStyle = '#FFE9A0'; c.lineWidth = 1.4; c.beginPath(); c.moveTo(-hr * .6, -hr * .95); c.lineTo(-hr * .75, -hr * 1.7); c.lineTo(-hr * .3, -hr * 1.3); c.lineTo(0, -hr * 1.85); c.lineTo(hr * .3, -hr * 1.3); c.lineTo(hr * .75, -hr * 1.7); c.lineTo(hr * .6, -hr * .95); c.closePath(); c.fill(); c.stroke(); }
  if (o.acc === 'cap') { c.fillStyle = '#FF7AA2'; c.beginPath(); c.arc(0, -hr * .15, hr * 1.02, Math.PI, TAU); c.fill(); c.fillRect(-hr * .1, -hr * .35, hr * 1.5, hr * .22); }
  if (o.acc === 'headphones') { c.strokeStyle = '#8E8EFF'; c.lineWidth = 3.4; c.beginPath(); c.arc(0, -hr * .1, hr * 1.08, Math.PI * 1.02, Math.PI * 1.98); c.stroke(); c.fillStyle = '#4C7DFF'; for (const sg of [-1, 1]) { rr(c, sg * hr * 1.0 - 4, -hr * .35, 8, hr * .7, 3); c.fill(); } }
  if (o.acc === 'bow') { c.fillStyle = '#FF7AA2'; c.beginPath(); c.moveTo(0, -hr * 1.05); c.lineTo(-hr * .5, -hr * 1.45); c.lineTo(-hr * .5, -hr * .75); c.closePath(); c.fill(); c.beginPath(); c.moveTo(0, -hr * 1.05); c.lineTo(hr * .5, -hr * 1.45); c.lineTo(hr * .5, -hr * .75); c.closePath(); c.fill(); }
  c.restore();
  // аксессуары на теле
  if (o.acc === 'tie') { c.fillStyle = '#FF7AA2'; const nx = T.neck[0], ny = T.neck[1]; c.beginPath(); c.moveTo(nx, ny + 4); c.lineTo(nx - 5 * s, ny + 20 * s); c.lineTo(nx, ny + 38 * s); c.lineTo(nx + 5 * s, ny + 20 * s); c.closePath(); c.fill(); }
  c.restore();
  return { head: [hx, hy], hr, hF: T.hF, hB: T.hB, hip: T.hip, neck: T.neck, footF: T.footF, footB: T.footB, kF: T.kF, kB: T.kB, sh: T.sh };
}

function face(c, kind, look, hr, t, ph) {
  c.save(); c.translate(look, 0);
  c.strokeStyle = '#F4F2FF'; c.fillStyle = '#F4F2FF'; c.lineWidth = 1.9; c.lineCap = 'round';
  const ex = hr * .38, ey = -hr * .12;
  const blink = (Math.sin(t * 1.7 + ph) > .985);
  const arcEye = (x, up) => { c.beginPath(); c.arc(x, ey + (up ? hr * .12 : 0), hr * .17, up ? Math.PI * 1.1 : Math.PI * 0.1, up ? Math.PI * 1.9 : Math.PI * 0.9); c.stroke(); };
  const dotEye = (x, r = hr * .1) => { c.beginPath(); c.arc(x, ey, r, 0, TAU); c.fill(); };
  const lineEye = (x) => { c.beginPath(); c.moveTo(x - hr * .17, ey); c.lineTo(x + hr * .17, ey); c.stroke(); };
  if (kind === 'smile') { arcEye(-ex, true); arcEye(ex, true); c.beginPath(); c.arc(0, hr * .18, hr * .3, Math.PI * .15, Math.PI * .85); c.stroke(); }
  else if (kind === 'smirk') { lineEye(-ex); lineEye(ex); c.beginPath(); c.moveTo(-hr * .2, hr * .4); c.quadraticCurveTo(hr * .1, hr * .52, hr * .35, hr * .3); c.stroke(); }
  else if (kind === 'worry') { blink ? lineEye(-ex) : dotEye(-ex); blink ? lineEye(ex) : dotEye(ex); c.beginPath(); c.moveTo(-ex - hr * .15, ey - hr * .28); c.lineTo(-ex + hr * .12, ey - hr * .38); c.moveTo(ex + hr * .15, ey - hr * .28); c.lineTo(ex - hr * .12, ey - hr * .38); c.stroke(); c.beginPath(); c.moveTo(-hr * .24, hr * .42); c.quadraticCurveTo(0, hr * .28, hr * .24, hr * .42); c.stroke(); }
  else if (kind === 'sad' || kind === 'cry') { arcEye(-ex, false); arcEye(ex, false); c.beginPath(); c.moveTo(-hr * .26, hr * .46); c.quadraticCurveTo(0, hr * .26, hr * .26, hr * .46); c.stroke();
    if (kind === 'cry') { c.fillStyle = '#7FB6FF'; const d = (t * 1.6 + ph) % 1; for (const sgn of [-1, 1]) { c.beginPath(); c.ellipse(sgn * ex, ey + hr * (.25 + d * .8), hr * .08, hr * .14, 0, 0, TAU); c.fill(); } } }
  else if (kind === 'angry') { dotEye(-ex, hr * .09); dotEye(ex, hr * .09); c.beginPath(); c.moveTo(-ex - hr * .2, ey - hr * .38); c.lineTo(-ex + hr * .16, ey - hr * .2); c.moveTo(ex + hr * .2, ey - hr * .38); c.lineTo(ex - hr * .16, ey - hr * .2); c.stroke(); c.beginPath(); c.moveTo(-hr * .26, hr * .46); c.lineTo(hr * .26, hr * .46); c.stroke(); }
  else if (kind === 'shock') { c.beginPath(); c.arc(-ex, ey, hr * .15, 0, TAU); c.arc(ex, ey, hr * .15, 0, TAU); c.stroke(); c.beginPath(); c.ellipse(0, hr * .45, hr * .12, hr * .18, 0, 0, TAU); c.stroke(); }
  else if (kind === 'sleep') { lineEye(-ex); lineEye(ex); c.beginPath(); c.arc(0, hr * .42, hr * .1, 0, TAU); c.stroke(); }
  else if (kind === 'happy') { arcEye(-ex, true); arcEye(ex, true); c.beginPath(); c.arc(0, hr * .1, hr * .38, Math.PI * .1, Math.PI * .9); c.fill(); }
  c.restore();
}

/* ---------- собака ---------- */
function dog(g, o) {
  const c = g.c, s = o.s || 1, f = o.facing || 1, t = g.t, p = o.pose || 'stand';
  const col = '#06050F', line = LINE;
  c.save(); c.translate(o.x, o.y); c.scale(f * s, s);
  const wag = Math.sin(t * (o.wag || 14)) * 24;
  let by = -38, tilt = 0, head = [36, -62];
  if (p === 'sit' || p === 'beg') { by = -34; tilt = -.75; head = [26, -78]; }
  if (p === 'lie') { by = -16; head = [38, -26]; }
  if (p === 'chew') { by = -36; tilt = .25; head = [42, -22]; }
  if (p === 'run') { by = -40 + Math.sin(t * 16) * 4; head = [40, -58]; }
  const L = (a, b, w = 6) => { c.lineCap = 'round'; c.strokeStyle = line; c.lineWidth = w + 2.8; c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.stroke(); c.strokeStyle = col; c.lineWidth = w; c.stroke(); };
  // хвост
  const ta = (-70 + wag) * RAD, tb = [-26, by - 4], tt = [tb[0] + Math.cos(ta) * 26, tb[1] + Math.sin(ta) * 26];
  L(tb, tt, 4.6);
  const ph = t * 16;
  if (p === 'run') { for (const [x, d] of [[-20, 0], [-8, 2], [10, 3], [22, 1]]) L([x, by + 8], [x * 1.3 + Math.sin(ph + d) * 15, 0], 5.4); }
  else if (p === 'sit' || p === 'beg') { L([-14, by + 10], [-24, -3], 6); L([-14, by + 10], [4, -3], 6); L([16, by + 4], [20, 0], 5.4); L([8, by + 6], [10, 0], 5.4); }
  else if (p === 'lie') { L([-20, -8], [-34, -1], 5.4); L([20, -8], [36, -1], 5.4); }
  else { for (const x of [-20, -8, 12, 24]) L([x, by + 8], [x, 0], 5.4); }
  // тело
  c.save(); c.translate(0, by); c.rotate(tilt);
  c.fillStyle = col; c.strokeStyle = line; c.lineWidth = 2.4; c.beginPath(); c.ellipse(0, 0, 32, 16, 0, 0, TAU); c.fill(); c.stroke(); c.restore();
  // шея
  const nk = [Math.cos(tilt) * 22 + 0, by + Math.sin(tilt) * 22 - 4];
  L([nk[0], nk[1]], [head[0] - 6, head[1] + 6], 9);
  // голова
  c.save(); c.translate(head[0], head[1]);
  c.fillStyle = col; c.strokeStyle = line; c.lineWidth = 2.4;
  c.beginPath(); c.arc(0, 0, 14, 0, TAU); c.fill(); c.stroke();
  c.beginPath(); c.ellipse(13, 5, 11, 7, 0, 0, TAU); c.fillStyle = col; c.fill(); c.stroke();
  c.beginPath(); c.arc(0, 0, 12.4, 0, TAU); c.fillStyle = col; c.fill();
  c.fillStyle = '#F4F2FF'; c.beginPath(); c.arc(21, 2, 2.6, 0, TAU); c.fill();
  c.beginPath(); c.arc(5, -3, 2, 0, TAU); c.fill();
  c.fillStyle = col; c.beginPath(); c.moveTo(-6, -10); c.lineTo(-15, 5 + Math.sin(t * 8) * 1.5); c.lineTo(-1, 9); c.closePath(); c.fill(); c.stroke();
  if (o.acc === 'bow') { c.fillStyle = '#FF7AA2'; c.beginPath(); c.moveTo(-6, -14); c.lineTo(-16, -22); c.lineTo(-16, -8); c.closePath(); c.fill(); c.beginPath(); c.moveTo(-6, -14); c.lineTo(4, -22); c.lineTo(4, -8); c.closePath(); c.fill(); }
  c.restore();
  c.restore();
  return { head: [o.x + head[0] * s * f, o.y + head[1] * s] };
}

/* ---------- фон комнат ---------- */
const PAL = {
  A: { w1: '#2D3062', w2: '#252852', fl: '#191A36', glow: 'rgba(160,150,255,A)', edge: '#9A98FF' },
  B: { w1: '#4D3D82', w2: '#43366F', fl: '#2A2147', glow: 'rgba(170,140,255,A)', edge: '#9C86FF' },
};
function rng(seed) { let s = seed; return () => (s = (s * 1664525 + 1013904223) % 4294967296) / 4294967296; }
const SKY = (() => { const r = rng(7); const b = []; let x = -10; while (x < 690) { const w = 26 + r() * 40, h = 90 + r() * 150; b.push({ x, w, h, win: Array.from({ length: 26 }, () => r()) }); x += w + 4 + r() * 8; } return b; })();

function room(g, kind, bg) {
  const c = g.c, pal = PAL[kind], w = g.w, h = g.h, gy = g.ground;
  const gr = c.createLinearGradient(0, 0, 0, gy); gr.addColorStop(0, pal.w1); gr.addColorStop(1, pal.w2);
  c.fillStyle = gr; c.fillRect(0, 0, w, h);
  if (bg === 'skyline' || (!bg && kind === 'A')) {
    for (const b of SKY) {
      const by = gy - b.h;
      c.fillStyle = 'rgba(30,26,70,.78)'; c.fillRect(b.x, by, b.w, b.h);
      const cols = Math.max(2, Math.floor(b.w / 12)), rows = Math.floor(b.h / 16);
      for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
        const v = b.win[(i * 5 + j * 3) % 26];
        if (v > .62) { c.fillStyle = v > .9 ? 'rgba(255,201,60,.95)' : 'rgba(255,170,90,.75)'; c.fillRect(b.x + 4 + i * 12, by + 6 + j * 16, 5, 6); }
      }
    }
    glowCircle(c, w * .78, 90, 210, 'rgba(160,150,255,A)', .38);
  } else if (bg === 'wall' || (!bg && kind === 'B')) {
    c.strokeStyle = 'rgba(190,170,255,.07)'; c.lineWidth = 1;
    for (let x = 0; x < w; x += 42) { c.beginPath(); c.moveTo(x, 0); c.lineTo(x, gy); c.stroke(); }
    for (let y = 0; y < gy; y += 42) { c.beginPath(); c.moveTo(0, y); c.lineTo(w, y); c.stroke(); }
  }
  c.fillStyle = pal.fl; c.fillRect(0, gy, w, h - gy);
  c.strokeStyle = pal.edge; c.lineWidth = 2; c.globalAlpha = .75; c.beginPath(); c.moveTo(0, gy); c.lineTo(w, gy); c.stroke(); c.globalAlpha = 1;
  c.fillStyle = 'rgba(0,0,0,.18)'; c.fillRect(0, gy + 2, w, h - gy);
}
function windowFrame(g, x = 60, y = 62, w = 130, h = 90) { // окошко-картина в нижней комнате
  const c = g.c;
  c.fillStyle = '#13112B'; rr(c, x, y, w, h, 5); c.fill();
  const r = rng(11);
  for (let i = 0; i < 14; i++) for (let j = 0; j < 4; j++) { const v = r(); c.fillStyle = v > .5 ? 'rgba(255,190,80,.85)' : 'rgba(120,110,200,.5)'; c.fillRect(x + 10 + i * 8.5, y + 52 + j * 9 + (j > 1 ? 4 : 0), 4, 4); }
  c.strokeStyle = '#D8D4FF'; c.lineWidth = 2.6; rr(c, x, y, w, h, 5); c.stroke();
}

/* ---------- UI: заголовок панели, подпись, тост, чек-лист ---------- */
function drawCaption(g, lines, x, y, t0, size = 28, dy = 34) {
  const c = g.c, age = g.t - t0;
  const k = back(clamp(age / .28)); const sc = .85 + .15 * k;
  c.save(); c.translate(x, y); c.scale(sc, sc);
  lines.forEach((L, i) => {
    if (L == null) return;
    txt(c, L, 0, i * dy, { size, w: 800, col: i ? '#B8B5FF' : '#FFFFFF', maxW: 628, shadow: 'rgba(0,0,0,.55)', sb: 6, a: clamp(age / .12) });
  });
  c.restore();
}
function toast(g, x, y, text, alert, a) {
  const c = g.c; c.save(); c.globalAlpha = clamp(a) * (g.dim ? 1 : 1); c.translate((1 - eo(clamp(a * 1.5))) * 40, 0);
  c.font = `700 14px ${FONT}`; const w = Math.min(330, c.measureText(text).width + 56);
  c.fillStyle = 'rgba(18,16,48,.96)'; c.strokeStyle = alert ? '#FF4A63' : '#7C7CFF'; c.lineWidth = 1.8; rr(c, x - w, y, w, 34, 17); c.fill(); c.stroke();
  c.fillStyle = alert ? '#FF4A63' : '#6C74FF'; c.beginPath(); c.arc(x - w + 19, y + 17, 8, 0, TAU); c.fill();
  txt(c, alert ? '!' : 'i', x - w + 19, y + 17.5, { size: 12, w: 800, col: '#fff' });
  txt(c, text, x - w + 34, y + 17.5, { size: 14, w: 700, align: 'left', col: '#fff' });
  c.restore();
}
function checklist(g, scn, t) {
  if (t < 4.6) return;
  const c = g.c, a = back(clamp((t - 4.6) / .4)), late = g.red;
  c.save(); c.translate(14, 54); c.globalAlpha = clamp((t - 4.6) / .2); c.scale(.7 + .3 * a, .7 + .3 * a);
  c.fillStyle = 'rgba(18,14,44,.93)'; c.strokeStyle = late > .5 ? '#FF4A63' : '#F4A9C4'; c.lineWidth = 2; rr(c, 0, 0, 192, 126, 12); c.fill(); c.stroke();
  txt(c, scn.card[0], 12, 16, { size: 11.5, w: 800, ls: 2, align: 'left', col: late > .5 ? '#FF6F85' : '#F4A9C4', maxW: 168 });
  scn.card.slice(1).forEach((it, i) => {
    const y = 40 + i * 21.5;
    c.strokeStyle = '#8E8EFF'; c.lineWidth = 1.8; rr(c, 12, y - 7.5, 14, 14, 3.5);
    if (i === 0) { c.fillStyle = '#6C74FF'; c.fill(); c.stroke(); c.strokeStyle = '#fff'; c.lineWidth = 2; c.beginPath(); c.moveTo(15, y); c.lineTo(18.5, y + 3.5); c.lineTo(24, y - 4); c.stroke(); }
    else c.stroke();
    txt(c, it, 36, y, { size: 14.5, w: 700, align: 'left', col: i === 0 ? '#9A9AC8' : '#fff', maxW: 148 });
    if (i === 0) { c.strokeStyle = '#9A9AC8'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(34, y); c.lineTo(36 + Math.min(c.measureText(it).width, 140), y); c.stroke(); }
  });
  c.restore();
}

/* ---------- таймер ---------- */
const TIMER = [[0, 300], [.45, 294], [1.45, 281], [2.45, 268], [3.45, 256], [4.45, 243], [5.45, 230], [6.45, 218], [7.45, 205], [8.45, 193], [9.45, 180], [10.45, 167], [11.45, 155], [12.45, 142], [13.45, 129], [14.45, 117], [14.95, 80], [15.45, 54], [16.45, 42], [17.45, 29], [18.45, 16], [19.45, 8], [20.45, 5], [21.45, 2], [22.0, 0]];
const timerSec = t => Math.max(0, kfl(t, TIMER));
function drawTimer(g, label, t) {
  const c = g.c, sec = timerSec(t), rem = sec / 300;
  const ss = Math.round(sec), txtT = String(Math.floor(ss / 60)).padStart(2, '0') + ':' + String(ss % 60).padStart(2, '0');
  const red = clamp((19 - t) * -1 / .3) * (t < 22.4 ? 1 : 1);
  const fade = 1 - tw(t, 22.4, 23.0);
  if (fade <= 0) return;
  c.save(); c.globalAlpha = fade;
  // тусклая линия
  c.strokeStyle = 'rgba(150,150,210,.28)'; c.lineWidth = 2; c.beginPath(); c.moveTo(40, 618); c.lineTo(680, 618); c.stroke();
  const L = 198, lx = 238 - L * rem, rx = 482 + L * rem;
  const lc0 = red > .5 ? '#FF3B55' : '#F4A9C4', rc0 = red > .5 ? '#FF3B55' : '#8E8EFF';
  const gl = c.createLinearGradient(lx, 0, 238, 0); gl.addColorStop(0, lc0); gl.addColorStop(1, red > .5 ? '#FF3B55' : '#C8A0E0');
  c.shadowColor = lc0; c.shadowBlur = 8; c.strokeStyle = gl; c.lineWidth = 3; c.lineCap = 'round'; c.beginPath(); c.moveTo(lx, 618); c.lineTo(238, 618); c.stroke();
  const gr = c.createLinearGradient(482, 0, rx, 0); gr.addColorStop(0, red > .5 ? '#FF3B55' : '#B4A4F0'); gr.addColorStop(1, rc0);
  c.shadowColor = rc0; c.strokeStyle = gr; c.beginPath(); c.moveTo(482, 618); c.lineTo(rx, 618); c.stroke();
  c.fillStyle = '#fff'; c.shadowBlur = 12; c.shadowColor = lc0; c.beginPath(); c.arc(lx, 618, 5, 0, TAU); c.fillStyle = lc0; c.fill();
  c.shadowColor = rc0; c.beginPath(); c.arc(rx, 618, 5, 0, TAU); c.fillStyle = rc0; c.fill();
  c.shadowBlur = 0;
  txt(c, label, 360, 579, { size: 14, w: 800, ls: 6.5, col: red > .5 ? '#FF8294' : '#A6A8D8' });
  const pop = 1 + .04 * Math.max(0, 1 - ((t * 1) % 1) * 5) * (t > 14 ? 1 : 0);
  c.save(); c.translate(360, 617); c.scale(pop, pop);
  txt(c, txtT, 0, 0, { size: 56, w: 800, col: red > .5 ? '#FF3B55' : '#D9D7FF', shadow: red > .5 ? 'rgba(255,40,70,.9)' : 'rgba(190,180,255,.6)', sb: 18 });
  c.restore(); c.restore();
}

/* ---------- панель ---------- */
function panel(g, kind, title, y0, drawScene, capsFn, t, scn) {
  const c = ctx, x0 = 24, w = 672, h = kind === 'A' ? 466 : 465;
  const red = clamp((t - 18.9) / .4), dim = tw(t, 22.4, 23.0);
  c.save(); c.translate(x0, y0);
  rr(c, 0, 0, w, h, 20); c.save(); c.clip();
  const gg = { c, t, w, h, ground: 372, pulse: 0, red, kind, dim };
  // резиновость на смене реплики
  const caps = kind === 'A' ? scn.TA : scn.TB; let last = 0; for (const tt of caps) if (t >= tt) last = tt;
  const age = t - last; gg.pulse = last > 0 ? Math.exp(-age * 7) * Math.sin(age * 26) * .045 : 0;
  room(gg, kind, scn[kind].bg);
  drawScene(gg, t);
  if (kind === 'A') checklist(gg, scn, t);
  capsFn(gg, t);
  if (red > 0) { c.fillStyle = `rgba(255,50,80,${.07 * red})`; c.fillRect(0, 0, w, h); }
  c.fillStyle = `rgba(8,6,22,${.62 * dim})`; c.fillRect(0, 0, w, h);
  c.restore();
  // рамка
  const pal = PAL[kind];
  c.strokeStyle = red > .5 ? '#FF4A63' : pal.edge; c.globalAlpha = (red > .5 ? .95 : .7) * (1 - dim * .55); c.lineWidth = 2.2;
  c.shadowColor = red > .5 ? '#FF4A63' : pal.edge; c.shadowBlur = 12; rr(c, 0, 0, w, h, 20); c.stroke(); c.shadowBlur = 0;
  c.globalAlpha = kind === 'B' ? 1 - tw(t, 22.6, 23.4) : 1 - dim * .5;
  txt(c, title, w / 2, 26, { size: 22, w: 800, ls: 4, col: '#F2F0FF', maxW: 560 });
  c.restore();
}

function pickIdx(t, T) { let i = 0; for (let k = 0; k < T.length; k++) if (t >= T[k]) i = k; return i; }

function frame(t, scn) {
  const c = ctx;
  c.clearRect(0, 0, W, H); c.fillStyle = '#0A0916'; c.fillRect(0, 0, W, H);
  const capA = (g, tt) => {
    if (tt >= 22.4) return; const i = pickIdx(tt, scn.TA);
    g.c.save(); g.c.globalAlpha = 1; drawCaption(g, scn.capsA[i], 336, 411, scn.TA[i], 28, 35); g.c.restore();
  };
  const capB = (g, tt) => {
    if (tt >= 22.4) return; const i = pickIdx(tt, scn.TB);
    drawCaption(g, [scn.capsB[i]], 336, 435, scn.TB[i], 27, 0);
    // уведомления
    scn.toasts.forEach(([a, b, text, alert]) => { if (tt >= a - .01 && tt < b) { const k = Math.min(clamp((tt - a) / .25), clamp((b - tt) / .2)); toast(g, 650, 46, text, alert, k); } });
  };
  panel(null, 'A', scn.A.title, 84, (g, tt) => scn.A.draw(g, tt), capA, t, scn);
  drawTimer({ c }, scn.timer, t);
  panel(null, 'B', scn.B.title, 650, (g, tt) => scn.B.draw(g, tt), capB, t, scn);
  // водяной знак
  c.save();
  txt(c, '@MASKA', 360, 1160, { size: 17, w: 800, ls: 6, col: '#8E90C8', a: .9 });
  txt(c, scn.sub, 360, 1184, { size: 12, w: 600, ls: 1.5, col: '#6F72A8', a: .9 });
  c.restore();
  // финальная карточка
  if (t >= 23.0) {
    const a = back(clamp((t - 23.0) / .45)), al = clamp((t - 23.0) / .2);
    c.save(); c.globalAlpha = al; c.translate(360, 599); c.scale(.7 + .3 * a, .7 + .3 * a);
    c.shadowColor = 'rgba(180,170,255,.85)'; c.shadowBlur = 36; c.fillStyle = '#F4F2FF'; rr(c, -319, -54, 638, 108, 26); c.fill(); c.shadowBlur = 0;
    txt(c, scn.cardText, 0, 3, { size: 44, w: 800, col: '#15122E', maxW: 580 });
    c.restore();
  }
  if (t >= 23.9) {
    const n = Math.max(1, Math.round(lerp(1, scn.ctr[1], eo(clamp((t - 24.2) / 2.4)))));
    c.save(); c.globalAlpha = clamp((t - 23.9) / .3);
    txt(c, scn.ctr[0] + (scn.ctr[1] <= 1 ? scn.ctr[1] : n) + (scn.ctr[2] || ''), 360, 672, { size: 23, w: 800, col: '#FFFFFF', shadow: 'rgba(0,0,0,.6)', sb: 8 });
    c.restore();
  }
  if (t >= 26.8) {
    const a = clamp((t - 26.8) / 1.0);
    c.save(); c.globalAlpha = a;
    txt(c, scn.cta, 360, 1216, { size: 18, w: 800, col: '#F2F0FF', maxW: 640 });
    // «Знакомо? Ставь 🎯 в комментарии»
    c.font = `800 18px ${FONT}`;
    const s1 = 'Знакомо? Ставь ', s2 = ' в комментарии', w1 = c.measureText(s1).width, w2 = c.measureText(s2).width, tot = w1 + 24 + w2, x0 = 360 - tot / 2;
    txt(c, s1, x0, 1246, { size: 18, w: 800, align: 'left' });
    const tx = x0 + w1 + 12, ty = 1246;
    c.fillStyle = '#FF3B55'; c.beginPath(); c.arc(tx, ty, 11, 0, TAU); c.fill(); c.fillStyle = '#fff'; c.beginPath(); c.arc(tx, ty, 7.5, 0, TAU); c.fill();
    c.fillStyle = '#FF3B55'; c.beginPath(); c.arc(tx, ty, 4.8, 0, TAU); c.fill(); c.fillStyle = '#fff'; c.beginPath(); c.arc(tx, ty, 2, 0, TAU); c.fill();
    txt(c, s2, x0 + w1 + 24, 1246, { size: 18, w: 800, align: 'left' });
    c.restore();
  }
}
window.__frame = frame;
