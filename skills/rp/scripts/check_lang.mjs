// check_lang.mjs: kiểm trang báo cáo song ngữ của /rp task bằng Playwright (cài global: npm i -g playwright).
//   PW_CHANNEL=chrome node check_lang.mjs rp-task-….html [thư-mục-ảnh]
// Kiểm: (1) mở EN, bấm VI đổi cả trang, bấm lại về EN; (2) KHÔNG request nào ra ngoài (chặn hết, đếm = 0), (3) localStorage ném lỗi thì trang vẫn chạy,
//   (4) không có Translator API: nút dịch ẩn; có API (giả): tên việc KHÔNG đổi khi mở trang, chỉ đổi sau khi bấm, bấm lần nữa trả về gốc,
//   (5) 390 và 1280, cả EN lẫn VI: không cuộn ngang, không chữ tràn. Ảnh: <ra>/{en,vi}-{390,1280}.png và khung GIF <ra>/f*.png. Mã thoát 1 nếu hỏng.
import { createRequire } from 'module'; import { execSync } from 'child_process'; import { resolve } from 'path'; import { mkdirSync } from 'fs';
const require = createRequire((process.env.PW_ROOT || execSync('npm root -g', { encoding: 'utf8' }).trim()) + '/');
const { chromium } = require('playwright');
const f = resolve(process.argv[2] || ''), out = resolve(process.argv[3] || '.'); mkdirSync(out, { recursive: true });
const b = await chromium.launch(process.env.PW_CHANNEL ? { channel: process.env.PW_CHANNEL } : {}); let bad = 0, ext = 0;
const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) bad++; };
async function open(w, init) {
  const ctx = await b.newContext({ viewport: { width: w, height: 844 } }); const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await ctx.route('**/*', r => { const u = r.request().url(); if (u.startsWith('file:') || u.startsWith('data:')) return r.continue(); ext++; console.log('  request ngoài: ' + u); return r.abort(); });   // chặn HẾT; font Lexend Deca nhúng base64 nên không còn ngoại lệ
  if (init) await p.addInitScript(init);
  await p.goto('file://' + f); await p.waitForTimeout(600); return { ctx, p, errs };
}
const vis = (p, sel) => p.evaluate(s => [...document.querySelectorAll(s)].some(e => e.offsetParent !== null), sel);
// Luật khoảng trống đã đổi (owner 1/11 qua Klau m1a1931ae86c7507: «để space cũng được, không cần cố nhét»): BỎ luật trống cuối ≤ 120 px; tờ ít nội dung để trống phía dưới.
// Còn lại: (a) khổ > 820: MỌI tờ cao bằng nhau ±2 px (khổ chuẩn = bìa, quyển sổ thật); (b) khe giữa hai khối kề nhau trong tờ ≤ 80 px (trừ bìa, bìa là chuẩn).
const GAP = 80;
const blank = p => p.evaluate(([g]) => {
  const out = [], pgs = [...document.querySelectorAll('article.page')];
  if (innerWidth > 820 && pgs.length) { const hs = pgs.map(e => e.getBoundingClientRect().height), lo = Math.min(...hs), hi = Math.max(...hs); if (hi - lo > 2) out.push(`các tờ cao khác nhau: ${Math.round(lo)} đến ${Math.round(hi)} px (phải bằng nhau ±2)`); }
  for (const pg of pgs) { if (pg.classList.contains('cover')) continue;
    const kids = [...pg.children].filter(e => e.offsetParent && !e.matches('.run,.foot'));
    for (let i = 1; i < kids.length; i++) { const d = kids[i].getBoundingClientRect().top - kids[i - 1].getBoundingClientRect().bottom; if (d > g) out.push(`khe ${Math.round(d)}px trong trang «${(pg.querySelector('h2') || {}).textContent}»`); } }
  return out; }, [GAP]);
// Luật chữ (owner m1a192fa92c41dfb, Kanade DUYỆT): độ đậm ≤ 300 (cấm Lexend thường và bold); < 200 chỉ khi cỡ ≥ 48 px; chữ ≤ 200 dùng màu gần đen (WCAG không tính độ mảnh);
// tương phản ≥ 4.5:1 chữ < 24 px, ≥ 3:1 chữ lớn; họ font đầu tiên là Lexend Deca. Độ mảnh của nét: chưa đo bằng số, xem ảnh.
const typo = p => p.evaluate(() => {
  const lum = c => { const a = c.match(/[\d.]+/g).map(Number).slice(0, 3).map(v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }); return .2126 * a[0] + .7152 * a[1] + .0722 * a[2]; };
  const bgOf = e => { for (let n = e; n; n = n.parentElement) { const c = getComputedStyle(n).backgroundColor; if (!/rgba\(0, 0, 0, 0\)|transparent/.test(c)) return c; } return 'rgb(255, 255, 255)'; };
  const cr = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const bad = [], seen = new Set();
  for (const e of document.querySelectorAll('body *')) {
    if (!e.offsetParent && e.tagName !== 'BODY') continue;
    if (![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    const c = getComputedStyle(e), w = +c.fontWeight, fs = parseFloat(c.fontSize), k = `${e.tagName}.${e.className}|${w}|${Math.round(fs)}|${c.color}`;
    if (seen.has(k)) continue; seen.add(k);
    const tag = `${e.tagName.toLowerCase()}${e.className ? '.' + e.className : ''} «${e.textContent.trim().slice(0, 24)}»`;
    if (e.closest('b') && e.tagName !== 'B') { if (w !== 600) bad.push(`chữ trong nhãn đậm phải 600, đang ${w}: ${tag}`); }
    else if (e.tagName === 'B') { if (w !== 600) bad.push(`nhãn đậm phải 600, đang ${w}: ${tag}`); if (!/[:：]\s*$/.test(e.textContent.trim())) bad.push(`nhãn đậm phải kết thúc bằng «:»: ${tag}`); }   // NGOẠI LỆ DUY NHẤT (owner 1/11): nhãn đầu dòng trước «:» đậm 600, chữ sau «:» giữ Light
    else if (w > 300) bad.push(`độ đậm ${w} > 300: ${tag}`);
    if (w < 200 && fs < 48) bad.push(`độ đậm ${w} < 200 ở cỡ ${Math.round(fs)} px (< 48): ${tag}`);
    if (w <= 200 && cr(c.color, 'rgb(17, 17, 17)') > 1.3) bad.push(`chữ mảnh (${w}) không dùng màu gần đen (${c.color}): ${tag}`);
    const r = cr(c.color, bgOf(e)), need = fs >= 24 ? 3 : 4.5;
    if (r < need) bad.push(`tương phản ${r.toFixed(2)}:1 < ${need}:1 (cỡ ${Math.round(fs)} px): ${tag}`);
    if (!/^"?Lexend Deca/.test(c.fontFamily) && !e.closest('svg')) bad.push(`họ font không phải Lexend Deca (${c.fontFamily.slice(0, 30)}): ${tag}`);
  }
  return bad;
});
const labels = p => p.evaluate(() => { // mỗi dòng văn trong thẻ việc phải mở đầu bằng nhãn đậm; phần chữ sau nhãn ≤ 300
  const bad = []; let n = 0;
  for (const lead of document.querySelectorAll('p.lead')) {
    if (!/[🔴🟡🔵⚪🟢]/u.test(lead.textContent)) continue;
    for (let q = lead.nextElementSibling; q && q.tagName === 'P' && !q.classList.contains('lead'); q = q.nextElementSibling) {
      if (q.offsetParent === null && !q.querySelector('span:not([style*="none"])')) continue;
      n++; const b = q.querySelector('b'); if (!b || !q.textContent.trim().startsWith(b.textContent.trim().slice(0, 3)) || +getComputedStyle(b).fontWeight !== 600) bad.push(`dòng không mở đầu bằng nhãn đậm: «${q.textContent.trim().slice(0, 30)}»`);
    }
  }
  return { n, bad };
});
// Tên màu tô màu tương ứng (owner 1/11: «Red, Yellow tô màu tương ứng»): mọi tiêu đề trang và nhãn đậm mở đầu bằng tên màu phải chứa .c-<màu> có màu chữ đúng bảng. Tương phản do luật chữ đo.
const TXT = { red: 'rgb(179, 38, 30)', yellow: 'rgb(138, 97, 0)', blue: 'rgb(31, 95, 168)', gray: 'rgb(91, 97, 104)', green: 'rgb(46, 107, 31)' };
const NAMES = [['red', /^(Red|Đỏ)(?=[\s:：]|$)/], ['yellow', /^(Yellow|Vàng)(?=[\s:：]|$)/], ['blue', /^(Blue|Xanh dương)(?=[\s:：]|$)/], ['gray', /^(Gray|Xám)(?=[\s:：]|$)/], ['green', /^(Green|Xanh lá)(?=[\s:：]|$)/]];   // KHÔNG dùng \b: \b của JS không coi «ỏ», «á» là chữ nên «Đỏ:» «Xanh lá:» không bao giờ khớp (Kirei CẦN SỬA 1cda5bc)
const colors = p => p.evaluate(([T, N]) => { const bad = []; let n = 0;
  for (const e of document.querySelectorAll('h2, b')) {
    if (e.offsetParent === null) continue;
    const t = [...e.querySelectorAll('span')].filter(x => x.offsetParent !== null && !x.querySelector('span')).map(x => x.textContent).join('') || e.textContent.trim();
    const hit = N.find(([, re]) => new RegExp(re[0], re[1]).test(t.trim())); if (!hit) continue; n++;
    const c = e.querySelector('.c-' + hit[0]); if (!c) { bad.push(`«${t.trim().slice(0, 20)}» không tô màu ${hit[0]}`); continue; }
    if (getComputedStyle(c).color !== T[hit[0]]) bad.push(`«${t.trim().slice(0, 20)}» màu ${getComputedStyle(c).color}, cần ${T[hit[0]]}`);
  }
  return { n, bad }; }, [TXT, NAMES.map(([k, re]) => [k, [re.source, re.flags]])]);
const faces = p => p.evaluate(async () => { await document.fonts.ready; return [...document.fonts].filter(f => f.family.replace(/"/g, '') === 'Lexend Deca' && f.status === 'loaded').length; });
const lay = p => p.evaluate(() => ({ sw: document.documentElement.scrollWidth - innerWidth,
  over: [...document.querySelectorAll('h1,h2,h3,p,li,.lead,button')].filter(e => e.offsetParent && e.scrollWidth > e.clientWidth + 1).length }));
const enColors = {};
for (const w of [390, 1280]) {
  const { ctx, p, errs } = await open(w);
  ok(await p.evaluate(() => document.documentElement.dataset.lang) === 'en' && await vis(p, '.en') && !await vis(p, '.vi'), `${w}: mở ra tiếng Anh, không thấy chữ Việt của trang`);
  let m = await lay(p); ok(m.sw <= 0 && m.over === 0, `${w} EN: không cuộn ngang, không chữ tràn ${JSON.stringify(m)}`);
  { const bl = await blank(p); ok(!bl.length, `${w} EN: không khoảng trống thừa ${bl.join('; ')}`); const ty = await typo(p); ok(!ty.length, `${w} EN: luật chữ (độ đậm, tương phản, họ font) ${ty.slice(0, 4).join('; ')}`); const lb = await labels(p); ok(lb.n >= 3 && !lb.bad.length, `${w} EN: ${lb.n} dòng thẻ đều mở đầu bằng nhãn đậm ${lb.bad.slice(0, 3).join('; ')}`); const co = await colors(p); enColors[w] = co.n; ok(co.n >= 9 && !co.bad.length, `${w} EN: ${co.n} tên màu (tiêu đề, chú giải, tóm tắt) tô đúng màu ${co.bad.slice(0, 3).join('; ')}`); ok(await faces(p) >= 1, `${w} EN: font Lexend Deca nạp từ dữ liệu nhúng`); }
  await p.screenshot({ path: `${out}/en-${w}.png`, fullPage: true });
  await p.click('#rp-lang'); await p.waitForTimeout(150);
  ok(await p.evaluate(() => document.documentElement.dataset.lang) === 'vi' && await vis(p, '.vi') && !await vis(p, '.en'), `${w}: bấm nút đổi cả trang sang tiếng Việt`);
  m = await lay(p); ok(m.sw <= 0 && m.over === 0, `${w} VI: không cuộn ngang, không chữ tràn ${JSON.stringify(m)}`);
  { const bl = await blank(p); ok(!bl.length, `${w} VI: không khoảng trống thừa ${bl.join('; ')}`); const ty = await typo(p); ok(!ty.length, `${w} VI: luật chữ ${ty.slice(0, 4).join('; ')}`); const lb = await labels(p); ok(lb.n >= 3 && !lb.bad.length, `${w} VI: ${lb.n} dòng thẻ đều mở đầu bằng nhãn đậm ${lb.bad.slice(0, 3).join('; ')}`); const co = await colors(p); ok(co.n === enColors[w] && !co.bad.length, `${w} VI: ${co.n} tên màu tô đúng màu (phải bằng EN ${enColors[w]}) ${co.bad.slice(0, 3).join('; ')}`); ok(await faces(p) >= 2, `${w} VI: nạp cả bộ chữ Việt và Latin`); }
  await p.screenshot({ path: `${out}/vi-${w}.png`, fullPage: true });
  await p.click('#rp-lang'); ok(await p.evaluate(() => document.documentElement.dataset.lang) === 'en', `${w}: bấm lại về tiếng Anh`);
  ok(!errs.length, `${w}: không lỗi JS ${errs.join('|')}`); await ctx.close();
}
{ // nhớ lựa chọn; localStorage hỏng thì vẫn chạy
  const { ctx, p } = await open(390); await p.click('#rp-lang'); await p.reload(); await p.waitForTimeout(300);
  ok(await p.evaluate(() => document.documentElement.dataset.lang) === 'vi', 'nhớ lựa chọn VI sau khi tải lại'); await ctx.close();
  const t = await open(390, () => { const e = () => { throw new Error('storage bị chặn'); }; Storage.prototype.getItem = e; Storage.prototype.setItem = e; });
  ok(await t.p.evaluate(() => document.documentElement.dataset.lang) === 'en', 'localStorage ném lỗi: mặc định EN, trang vẫn chạy');
  await t.p.click('#rp-lang'); ok(await t.p.evaluate(() => document.documentElement.dataset.lang) === 'vi' && !t.errs.length, 'localStorage ném lỗi: nút vẫn đổi ngôn ngữ, không lỗi JS'); await t.ctx.close();
}
{ // không có Translator: nút dịch ẩn
  const { ctx, p } = await open(390, () => { try { delete self.Translator; } catch (e) {} Object.defineProperty(self, 'Translator', { get() { return undefined; }, configurable: true }); delete self.Translator; });
  ok(!await p.evaluate(() => 'Translator' in self) && !await vis(p, '#rp-tr'), 'không có Translator API: nút «Translate task names» ẩn'); await ctx.close();
}
{ // có Translator (giả): không tự dịch lúc tải, chỉ dịch khi bấm, bấm lần nữa trả về gốc
  const { ctx, p, errs } = await open(390, () => { self.__calls = 0; self.Translator = { create: async () => ({ translate: async s => { self.__calls++; return 'EN:' + s; } }) }; });
  const names = () => p.evaluate(() => [...document.querySelectorAll('.tn')].map(e => e.textContent));
  const before = await names(); ok(await vis(p, '#rp-tr') && before.length > 0 && !before.some(s => s.startsWith('EN:')) && await p.evaluate(() => self.__calls) === 0, `có Translator: nút hiện; ${before.length} tên việc chưa dịch, 0 lần gọi lúc tải`);
  const card = () => p.evaluate(() => document.querySelector('.tn').scrollIntoView({ block: 'center' }));
  await p.screenshot({ path: `${out}/f0.png` }); await card(); await p.screenshot({ path: `${out}/f1.png` });
  await p.click('#rp-tr'); await p.waitForTimeout(300); const after = await names(); await card();
  ok(after.every((s, i) => s === 'EN:' + before[i]), 'bấm nút: mọi tên việc được dịch (giả lập trên máy)'); await p.screenshot({ path: `${out}/f2.png` });
  await p.click('#rp-tr'); await p.waitForTimeout(150); ok((await names()).every((s, i) => s === before[i]), 'bấm lần nữa: trả về tên gốc');
  await p.click('#rp-lang'); await p.waitForTimeout(150); ok(!await vis(p, '#rp-tr'), 'ở bản Việt: nút dịch tên việc ẩn'); await card(); await p.screenshot({ path: `${out}/f3.png` });
  ok(!errs.length, 'không lỗi JS'); await ctx.close();
}
ok(ext === 0, `không request nào ra ngoài (kể cả font): đếm ${ext}`);
await b.close(); process.exit(bad ? 1 : 0);
