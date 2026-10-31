// check_lang.mjs: kiểm trang báo cáo song ngữ của /rp task bằng Playwright (cài global: npm i -g playwright).
//   PW_CHANNEL=chrome node check_lang.mjs rp-task-….html [thư-mục-ảnh]
// Kiểm: (1) mở EN, bấm VI đổi cả trang, bấm lại về EN; (2) KHÔNG request nào ra ngoài (chặn hết, đếm = 0), (3) localStorage ném lỗi thì trang vẫn chạy,
//   (4) không có Translator API: nút dịch ẩn; có API (giả): tên việc KHÔNG đổi khi mở trang, chỉ đổi sau khi bấm, bấm lần nữa trả về gốc,
//   (5) 390 và 1280, cả EN lẫn VI: không cuộn ngang, không chữ tràn. Ảnh: <ra>/{en,vi}-{390,1280}.png và khung GIF <ra>/f*.png. Mã thoát 1 nếu hỏng.
import { createRequire } from 'module'; import { execSync } from 'child_process'; import { resolve } from 'path'; import { mkdirSync } from 'fs';
const require = createRequire((process.env.PW_ROOT || execSync('npm root -g', { encoding: 'utf8' }).trim()) + '/');
const { chromium } = require('playwright');
const f = resolve(process.argv[2] || ''), out = resolve(process.argv[3] || '.'); mkdirSync(out, { recursive: true });
const b = await chromium.launch(process.env.PW_CHANNEL ? { channel: process.env.PW_CHANNEL } : {}); let bad = 0, ext = 0, fonts = 0;
const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) bad++; };
async function open(w, init) {
  const ctx = await b.newContext({ viewport: { width: w, height: 844 } }); const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(String(e)));
  await ctx.route('**/*', r => { const u = r.request().url(); if (u.startsWith('file:')) return r.continue();
    if (/^https:\/\/fonts\.(googleapis|gstatic)\.com\//.test(u)) fonts++; else { ext++; console.log('  request ngoài: ' + u); } return r.abort(); });   // chặn HẾT; web font của khung book-layout (GET, không mang chữ báo cáo) đếm riêng
  if (init) await p.addInitScript(init);
  await p.goto('file://' + f); await p.waitForTimeout(600); return { ctx, p, errs };
}
const vis = (p, sel) => p.evaluate(s => [...document.querySelectorAll(s)].some(e => e.offsetParent !== null), sel);
// Luật khoảng trống (owner 31/10 m1a192b837fe75fa: «chừa quá nhiều khoảng trống»): trong mỗi trang (trừ bìa) khe giữa hai khối kề nhau ≤ 80 px và chỗ trống dưới khối cuối ≤ 120 px.
const GAP = 80, TAIL = 120;
const blank = p => p.evaluate(([g, t]) => [...document.querySelectorAll('article.page:not(.cover)')].flatMap(pg => {
  const kids = [...pg.children].filter(e => e.offsetParent && !e.matches('.run,.foot')), r = pg.getBoundingClientRect(), out = [];
  for (let i = 1; i < kids.length; i++) { const d = kids[i].getBoundingClientRect().top - kids[i - 1].getBoundingClientRect().bottom; if (d > g) out.push(`khe ${Math.round(d)}px trong trang «${(pg.querySelector('h2') || {}).textContent}»`); }
  const foot = pg.querySelector('.foot'), end = (foot ? foot.getBoundingClientRect().top : r.bottom) - (kids.length ? kids[kids.length - 1].getBoundingClientRect().bottom : r.top);
  if (end > t + 60) out.push(`trống ${Math.round(end)}px dưới khối cuối trang «${(pg.querySelector('h2') || {}).textContent}»`); return out; }), [GAP, TAIL]);
const lay = p => p.evaluate(() => ({ sw: document.documentElement.scrollWidth - innerWidth,
  over: [...document.querySelectorAll('h1,h2,h3,p,li,.lead,button')].filter(e => e.offsetParent && e.scrollWidth > e.clientWidth + 1).length }));
for (const w of [390, 1280]) {
  const { ctx, p, errs } = await open(w);
  ok(await p.evaluate(() => document.documentElement.dataset.lang) === 'en' && await vis(p, '.en') && !await vis(p, '.vi'), `${w}: mở ra tiếng Anh, không thấy chữ Việt của trang`);
  let m = await lay(p); ok(m.sw <= 0 && m.over === 0, `${w} EN: không cuộn ngang, không chữ tràn ${JSON.stringify(m)}`);
  { const bl = await blank(p); ok(!bl.length, `${w} EN: không khoảng trống thừa ${bl.join('; ')}`); }
  await p.screenshot({ path: `${out}/en-${w}.png`, fullPage: true });
  await p.click('#rp-lang'); await p.waitForTimeout(150);
  ok(await p.evaluate(() => document.documentElement.dataset.lang) === 'vi' && await vis(p, '.vi') && !await vis(p, '.en'), `${w}: bấm nút đổi cả trang sang tiếng Việt`);
  m = await lay(p); ok(m.sw <= 0 && m.over === 0, `${w} VI: không cuộn ngang, không chữ tràn ${JSON.stringify(m)}`);
  { const bl = await blank(p); ok(!bl.length, `${w} VI: không khoảng trống thừa ${bl.join('; ')}`); }
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
ok(ext === 0, `không request nào ra ngoài file:// ngoài web font của khung book-layout (lạ: ${ext}; web font bị chặn mà trang vẫn chạy: ${fonts} request)`);
await b.close(); process.exit(bad ? 1 : 0);
