// check.mjs: đo trang book.py ở 1280 và 390 bằng Playwright (cài global: npm i -g playwright). In số đo, chụp ảnh cạnh tệp, mã 1 nếu hỏng.
//   node check.mjs trang.html
// Hỏng khi: cuộn ngang, chữ tràn khung, tiêu đề line-height < 1.15 (cắt dấu tiếng Việt), mép trái khối chữ lệch trong một trang, lỗi JS, font chưa tải.
import { createRequire } from 'module'; import { execSync } from 'child_process'; import { resolve } from 'path';
const require = createRequire((process.env.PW_ROOT || execSync('npm root -g', { encoding: 'utf8' }).trim()) + '/');
const { chromium } = require('playwright');
const f = resolve(process.argv[2] || ''); const b = await chromium.launch(); let bad = 0;
for (const w of [1280, 390]) {
  const p = await b.newPage({ viewport: { width: w, height: 900 } }); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await p.goto('file://' + f); await p.waitForTimeout(1500);
  const m = await p.evaluate(() => {
    const over = [...document.querySelectorAll('h1,h2,h3,p,li,blockquote,.hand,.big')].filter(e => e.scrollWidth > e.clientWidth + 1).length;
    const clip = [...document.querySelectorAll('h1,h2,.big')].filter(e => { const c = getComputedStyle(e); return parseFloat(c.lineHeight) / parseFloat(c.fontSize) < 1.15; }).length;
    const uneven = [...document.querySelectorAll('.page:not(.bleed)')].filter(pg => { const L = pg.getBoundingClientRect().left;
      return new Set([...pg.querySelectorAll(':scope > h1, :scope > h2, :scope > .lead, :scope > p, :scope > .kick, :scope > .rule')].map(e => Math.round(e.getBoundingClientRect().left - L))).size > 1; }).length;
    return { sw: document.documentElement.scrollWidth - innerWidth, over, clip, uneven, fonts: document.fonts.check('800 40px "Be Vietnam Pro"') };
  });
  const ok = !m.sw && !m.over && !m.clip && !m.uneven && !errs.length;
  bad += ok ? 0 : 1;
  console.log(`${ok ? 'ok ' : 'HỎNG'} ${w}px ${JSON.stringify(m)}${errs.length ? ' lỗi JS: ' + errs.join('; ') : ''}${m.fonts ? '' : ' (font chưa tải: mạng chặn Google Fonts?)'}`);
  await p.screenshot({ path: f.replace(/\.html$/, `-${w}.png`), fullPage: true }); await p.close();
}
await b.close(); process.exit(bad ? 1 : 0);
