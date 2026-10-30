// check.mjs: đo trang book.py ở 1280 và 390 bằng Playwright (cài global: npm i -g playwright). In số đo, chụp ảnh cạnh tệp, mã 1 nếu hỏng.
//   node check.mjs trang.html
// Hỏng khi: cuộn ngang, chữ tràn khung, tiêu đề line-height < 1.15 (cắt dấu tiếng Việt), mép trái khối chữ lệch trong một trang, lỗi JS, font chưa tải,
//   sơ đồ vòng lệch (cyc): tâm nút cách tâm vòng khác nhau > 1 px, góc giữa hai nút kề lệch 360/n quá 1°, khoảng nhãn–nút khác nhau > 1 px,
//   đầu/cuối mũi tên không nằm trên vòng (± 1 px) hoặc không nằm giữa hai nút nó nối, nhãn đè lên mũi tên / nút / nhãn khác (hit).
import { createRequire } from 'module'; import { execSync } from 'child_process'; import { resolve } from 'path';
const require = createRequire((process.env.PW_ROOT || execSync('npm root -g', { encoding: 'utf8' }).trim()) + '/');
const { chromium } = require('playwright');
const f = resolve(process.argv[2] || ''); const b = await chromium.launch(process.env.PW_CHANNEL ? { channel: process.env.PW_CHANNEL } : {}); let bad = 0;   // PW_CHANNEL=chrome: dùng Chrome đã cài khi Playwright không có Chromium cho máy (vd macOS 13)
for (const w of [1280, 390]) {
  const p = await b.newPage({ viewport: { width: w, height: 900 } }); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file://' + f); await p.waitForTimeout(1500);
  const m = await p.evaluate(() => {
    const over = [...document.querySelectorAll('h1,h2,h3,p,li,blockquote,.hand,.big,.cmp-r b,.cmp-r span')].filter(e => e.scrollWidth > e.clientWidth + 1).length;
    const clip = [...document.querySelectorAll('h1,h2,.big')].filter(e => { const c = getComputedStyle(e); return parseFloat(c.lineHeight) / parseFloat(c.fontSize) < 1.15; }).length;
    const uneven = [...document.querySelectorAll('.page:not(.bleed)')].filter(pg => { const L = pg.getBoundingClientRect().left;
      return new Set([...pg.querySelectorAll(':scope > h1, :scope > h2, :scope > .lead, :scope > p, :scope > .kick, :scope > .rule')].map(e => Math.round(e.getBoundingClientRect().left - L))).size > 1; }).length;
    const cyc = [...document.querySelectorAll('.cycle')].map(c => {
      const ring = c.querySelector('svg.ring'); if (!ring || getComputedStyle(ring).display === 'none') return null;
      const o = ring.querySelector('circle').getBoundingClientRect(), cx = o.left + o.width / 2, cy = o.top + o.height / 2;
      const deg = (x, y) => (Math.atan2(y - cy, x - cx) * 180 / Math.PI + 450) % 360;   // 0° = đỉnh, theo chiều kim đồng hồ
      const ns = [...c.querySelectorAll('.node')].map(n => { const i = n.querySelector('i').getBoundingClientRect(), l = n.querySelector('div').getBoundingClientRect();
        const x = i.left + i.width / 2, y = i.top + i.height / 2;
        return { r: Math.hypot(x - cx, y - cy), a: deg(x, y), gap: Math.max(l.left - i.right, i.left - l.right, l.top - i.bottom, i.top - l.bottom) }; });
      const n = ns.length, span = v => Math.max(...v) - Math.min(...v), R = ns.reduce((s, q) => s + q.r, 0) / n;
      const da = Math.max(...ns.map((q, k) => Math.abs((ns[(k + 1) % n].a - q.a + 360) % 360 - 360 / n)));
      const m = ring.getScreenCTM(); let dar = 0, order = 0;
      [...ring.querySelectorAll('path[marker-end]')].forEach((pth, k) => { const L = pth.getTotalLength();
        const ends = [0, L].map(t => { const q = pth.getPointAtLength(t).matrixTransform(m); dar = Math.max(dar, Math.abs(Math.hypot(q.x - cx, q.y - cy) - R)); return deg(q.x, q.y); });
        const a0 = ns[k % n].a, a1 = ns[(k + 1) % n].a, w = (a1 - a0 + 360) % 360;
        if (!ends.every(e => { const d = (e - a0 + 360) % 360; return d > 0 && d < w; })) order++; });
      const box = e => e.getBoundingClientRect(), labs = [...c.querySelectorAll('.node > div')].map(box), dots = [...c.querySelectorAll('.node i')].map(box);
      const meet = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
      let hit = labs.filter((l, k) => labs.some((o, j) => j !== k && meet(l, o)) || dots.some(d => meet(l, d))).length;
      [...ring.querySelectorAll('path[marker-end]')].forEach(pth => { const L = pth.getTotalLength();
        for (let t = 0; t <= L; t += L / 60) { const q = pth.getPointAtLength(t).matrixTransform(m); if (labs.some(l => q.x > l.left - 4 && q.x < l.right + 4 && q.y > l.top - 4 && q.y < l.bottom + 4)) { hit++; break; } } });
      return { n, hit, dr: +span(ns.map(q => q.r)).toFixed(1), da: +da.toFixed(1), dg: +span(ns.map(q => q.gap)).toFixed(1), dar: +dar.toFixed(1), order };
    }).filter(Boolean);
    const cycBad = cyc.filter(q => q.dr > 1 || q.da > 1 || q.dg > 1 || q.dar > 1 || q.order || q.hit).length;
    return { sw: document.documentElement.scrollWidth - innerWidth, over, clip, uneven, cyc, cycBad, fonts: document.fonts.check('800 40px "Be Vietnam Pro"') };
  });
  const ok = !m.sw && !m.over && !m.clip && !m.uneven && !m.cycBad && !errs.length;
  bad += ok ? 0 : 1;
  console.log(`${ok ? 'ok ' : 'HỎNG'} ${w}px ${JSON.stringify(m)}${errs.length ? ' lỗi JS: ' + errs.join('; ') : ''}${m.fonts ? '' : ' (font chưa tải: mạng chặn Google Fonts?)'}`);
  await p.screenshot({ path: f.replace(/\.html$/, `-${w}.png`), fullPage: true }); await p.close();
}
await b.close(); process.exit(bad ? 1 : 0);
