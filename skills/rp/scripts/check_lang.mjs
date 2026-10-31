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
    if (!lead.querySelector('.dot')) continue;
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
// Mã máy đóng chip (owner 1/11): mọi mã khớp mẫu ngoài chip là FAIL. KIỂU CHIP = trang mẫu của owner https://uiux.giatbh.io.vn/components/chip.html (Hình 1, .cx.fill): viên thuốc bo tròn, nền pastel THEO NHÓM,
// viền 1 px đậm hơn nền, chữ tối #1a1d21. Nhóm theo LOẠI MÃ do bản dựng khai ở data-what (không đoán từ chữ: nhánh toàn hex như «deadbee» vẫn là nhánh):
//   hồng phấn Pink #f7c1d9 = sha; mòng két Teal #b2ece2 = room, open (hang_open_work), branch; đào Peach #fae3c8 = reopen (mã mở lại). KHÔNG tím (owner chê «lạc quẻ»), không xám (owner), không đỏ/xanh lá (Kanade).
// Chip xuống dòng phải ôm sát chữ từng dòng như highlight (display:inline + box-decoration-break:clone), KHÔNG thành khối chữ nhật thừa chỗ (owner m1a19338db452775).
const CODE = /(\bs[0-9a-f]{11,12}\b|\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b|\bm[0-9a-f]{15}\b|\broom:[a-z0-9][a-z0-9-]*|\b[a-z0-9][a-z0-9_.-]*\/[a-z0-9][a-z0-9_./-]*)/;
const chips = p => p.evaluate(src => { const re = new RegExp(src); const bad = []; let n = 0;
  const rgb = x => (x.match(/[\d.]+/g) || []).slice(0, 3).map(Number), Lm = a => { const v = a.map(c => { c /= 255; return c <= .03928 ? c / 12.92 : Math.pow((c + .055) / 1.055, 2.4); }); return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]; }, cr = (a, b) => (Math.max(Lm(a), Lm(b)) + .05) / (Math.min(Lm(a), Lm(b)) + .05);
  const alpha = x => { const m = x.match(/[\d.]+/g) || []; return m.length > 3 ? +m[3] : 1; };
  const KIND = { pink: [247, 193, 217], teal: [178, 236, 226], peach: [250, 227, 200] }, GROUP = { sha: 'pink', room: 'teal', open: 'teal', branch: 'teal', reopen: 'peach' };
  for (const c of document.querySelectorAll('.chip')) { if (c.offsetParent === null) continue; n++;
    const st = getComputedStyle(c), txt = c.textContent.trim(), tag = `«${txt.slice(0, 20)}»`;
    const what = c.dataset.what, want = GROUP[what];
    if (!want) { bad.push(`chip ${tag} thiếu data-what hợp lệ (${what})`); continue; }
    if (!c.classList.contains('chip-' + want)) bad.push(`chip ${tag} (${what}) phải thuộc nhóm ${want}, đang lớp «${c.className}»`);
    const bgc = rgb(st.backgroundColor);
    if (bgc.join() !== KIND[want].join()) bad.push(`chip ${tag} phải nền ${want} rgb(${KIND[want].join(', ')}) như trang mẫu, đang ${st.backgroundColor}`);
    // không tông đỏ / xanh lá (Kanade): đỏ = cần xử lý, xanh lá = xong; chỉ xét khi nền có sắc (max−min ≥ 12)
    const mx = Math.max(...bgc), mn = Math.min(...bgc);
    if (mx - mn >= 12) { const [r, g, b] = bgc.map(v => v / 255), d = (mx - mn) / 255; let h = mx / 255 === r ? ((g - b) / d) % 6 : (mx / 255 === g ? (b - r) / d + 2 : (r - g) / d + 4); h = (h * 60 + 360) % 360;
      if (h >= 335 || h <= 12 || (h >= 75 && h <= 150)) bad.push(`chip ${tag} có tông ${h >= 75 && h <= 150 ? 'xanh lá' : 'đỏ'} (hue ${Math.round(h)}°): trùng màu tình trạng`);
      if (h >= 225 && h <= 320) bad.push(`chip ${tag} có tông TÍM (hue ${Math.round(h)}°): owner chê «lạc quẻ» (m1a1932949ed7b2d)`); }
    if (!/^"?Lexend Deca/.test(st.fontFamily) || +st.fontWeight > 300) bad.push(`chip ${tag} phải Lexend Deca ≤ 300, đang ${st.fontFamily.slice(0, 24)} ${st.fontWeight}`);
    if (rgb(st.color).join() !== '26,29,33') bad.push(`chữ chip ${tag} phải #1a1d21 như trang mẫu, đang ${st.color}`);
    const bd = rgb(st.borderTopColor); if (st.borderTopWidth !== '1px' || !bd.every((v, i) => v < bgc[i])) bad.push(`chip ${tag} phải có viền 1 px đậm hơn nền (viền ${st.borderTopColor}, nền ${st.backgroundColor})`);
    if (parseFloat(st.borderTopLeftRadius) < 14) bad.push(`chip ${tag} phải bo tròn kiểu viên thuốc (bo ${st.borderTopLeftRadius})`);
    // giấy THẬT = nền đầu tiên có alpha > 0 đi ngược tổ tiên từ cha của chip (.page trong suốt; giấy là .spread, trong khối .stat là nền .stat): lần trước lấy nền .page nên so với đen, luật không bao giờ FAIL (Kirei f51402b)
    let pe = c.parentElement, pbg = null; while (pe) { const b = getComputedStyle(pe).backgroundColor; if (alpha(b) > 0) { pbg = b; break; } pe = pe.parentElement; }
    if (!pbg) bad.push('không tìm thấy nền giấy phía sau chip');
    else if (cr(bgc, rgb(pbg)) < 1.06) bad.push(`chip ${tag} không nổi hơn giấy (${cr(bgc, rgb(pbg)).toFixed(3)}:1 < 1,06; giấy ${pbg})`);
    if (cr(rgb(st.color), bgc) < 7) bad.push(`chữ chip ${tag} tương phản ${cr(rgb(st.color), bgc).toFixed(1)}:1 < 7:1`);
    // ÔM SÁT CHỮ khi xuống dòng: inline + clone; mỗi mảnh dòng chỉ rộng hơn chữ đúng đệm + viền, không khối chữ nhật thừa chỗ
    if (st.display !== 'inline') bad.push(`chip ${tag} phải display:inline để ôm sát chữ từng dòng (đang ${st.display})`);
    if (!/clone/.test(st.boxDecorationBreak || st.webkitBoxDecorationBreak || '')) bad.push(`chip ${tag} phải box-decoration-break:clone`);
    const box = [...c.getClientRects()], rg = document.createRange(); rg.selectNodeContents(c); const tx = [...rg.getClientRects()].filter(r => r.width > 0);
    const slack = parseFloat(st.paddingLeft) + parseFloat(st.paddingRight) + 2 * parseFloat(st.borderTopWidth) + 3;
    for (const r of box) { const t = tx.filter(x => Math.abs(x.top - r.top) < r.height).sort((a, b) => a.left - b.left); if (!t.length) continue;
      const w = Math.max(...t.map(x => x.right)) - Math.min(...t.map(x => x.left)); if (r.width - w > slack) bad.push(`chip ${tag} bọc thừa chỗ: khung ${Math.round(r.width)}px, chữ ${Math.round(w)}px`); }
    const pr = c.closest('p,li,h2,div'); if (pr && box.some(r => r.right > pr.getBoundingClientRect().right + 1)) bad.push(`chip ${tag} tràn khung`); }
  const skip = e => e.closest('.chip,.foot,.run,.tn,.lead,b,h1,h2,#rp-bar,script,style,.kick,.vol,svg');
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let t; (t = w.nextNode());) { const e = t.parentElement; if (!e || e.offsetParent === null || skip(e)) continue; const m = t.textContent.match(re); if (m) bad.push(`mã ngoài chip: «${m[0].slice(0, 30)}»`); }
  return { n, bad }; }, CODE.source);
// Chấm trạng thái (owner m1a193435b762da4: emoji 🔴🟡 bóng loáng, lệch → «dot pastel màu đặc»): KHÔNG còn emoji chấm màu ở bất kỳ chữ nào; mỗi .dot là hình tròn CSS màu ĐẶC pastel, phẳng (không bóng, không viền, không gradient),
// đúng bảng màu, tương phản ≥ 1,5:1 với nền thật phía sau, và THẲNG HÀNG với chữ đi kèm (tâm chấm lệch tâm hộp chữ ≤ 3 px).
const DOTS = { red: [233, 140, 131], yellow: [239, 201, 92], blue: [134, 179, 230], gray: [183, 187, 193], green: [141, 206, 150] };
const dots = p => p.evaluate(D => { const bad = []; let n = 0;
  const rgb = x => (x.match(/[\d.]+/g) || []).slice(0, 3).map(Number), Lm = a => { const v = a.map(c => { c /= 255; return c <= .03928 ? c / 12.92 : Math.pow((c + .055) / 1.055, 2.4); }); return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]; }, cr = (a, b) => (Math.max(Lm(a), Lm(b)) + .05) / (Math.min(Lm(a), Lm(b)) + .05);
  const emoji = /[\u{1F534}\u{1F535}\u{1F7E0}-\u{1F7EB}\u{26AA}\u{26AB}\u{25CF}]/u, w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let t; (t = w.nextNode());) { const e = t.parentElement; if (e && e.offsetParent !== null && !e.closest('script,style') && emoji.test(t.textContent)) bad.push(`còn ký tự chấm màu (emoji): «${t.textContent.trim().slice(0, 24)}»`); }
  for (const d of document.querySelectorAll('.dot')) { if (d.offsetParent === null) continue; n++;
    const st = getComputedStyle(d), k = [...d.classList].find(c => c.startsWith('dot-'))?.slice(4), r = d.getBoundingClientRect();
    if (!D[k]) { bad.push(`chấm không thuộc năm màu (${d.className})`); continue; }
    if (rgb(st.backgroundColor).join() !== D[k].join()) bad.push(`chấm ${k} phải nền pastel rgb(${D[k].join(', ')}), đang ${st.backgroundColor}`);
    if (st.backgroundImage !== 'none' || (st.boxShadow && st.boxShadow !== 'none') || parseFloat(st.borderTopWidth) > 0) bad.push(`chấm ${k} phải phẳng: không gradient, không bóng, không viền`);
    if (parseFloat(st.borderTopLeftRadius) < r.width / 2 - .5 || Math.abs(r.width - r.height) > .5) bad.push(`chấm ${k} phải là hình tròn (${Math.round(r.width)}×${Math.round(r.height)}, bo ${st.borderTopLeftRadius})`);
    let pe = d.parentElement, pbg = null; while (pe) { const b = getComputedStyle(pe).backgroundColor; if (!/rgba\(0, 0, 0, 0\)|transparent/.test(b)) { pbg = b; break; } pe = pe.parentElement; }
    if (pbg && cr(D[k], rgb(pbg)) < 1.5) bad.push(`chấm ${k} tương phản ${cr(D[k], rgb(pbg)).toFixed(2)}:1 < 1,5:1 với nền`);
    // THẲNG HÀNG: hộp chữ đầu tiên bên PHẢI chấm trong cùng dòng (nextSibling của chấm chỉ là khoảng trắng nên lần trước luật không bao giờ chạy: Kirei, thử lệch 6 px vẫn xanh)
    const par = d.parentElement, rg = document.createRange(); rg.selectNodeContents(par);
    const tr = [...rg.getClientRects()].filter(x => x.width > 2 && x.left >= r.right - 1 && x.top < r.bottom && x.bottom > r.top).sort((a, b) => a.left - b.left)[0];
    if (!tr) bad.push(`chấm ${k} không có chữ bên phải cùng dòng để so hàng`);
    else { const fs = parseFloat(getComputedStyle(par).fontSize), glyphMid = tr.bottom - (tr.height - fs) / 2 - fs * .5 + fs * .02, dotMid = r.top + r.height / 2;
      if (Math.abs(dotMid - glyphMid) > 3) bad.push(`chấm ${k} lệch hàng với chữ ${(dotMid - glyphMid).toFixed(1)} px (> 3)`); } }
  return { n, bad }; }, DOTS);
const faces = p => p.evaluate(async () => { await document.fonts.ready; return [...document.fonts].filter(f => f.family.replace(/"/g, '') === 'Lexend Deca' && f.status === 'loaded').length; });
const lay = p => p.evaluate(() => ({ sw: document.documentElement.scrollWidth - innerWidth,
  over: [...document.querySelectorAll('h1,h2,h3,p,li,.lead,button')].filter(e => e.offsetParent && e.scrollWidth > e.clientWidth + 1).length }));
const enColors = {};
for (const w of [390, 1280]) {
  const { ctx, p, errs } = await open(w);
  ok(await p.evaluate(() => document.documentElement.dataset.lang) === 'en' && await vis(p, '.en') && !await vis(p, '.vi'), `${w}: mở ra tiếng Anh, không thấy chữ Việt của trang`);
  let m = await lay(p); ok(m.sw <= 0 && m.over === 0, `${w} EN: không cuộn ngang, không chữ tràn ${JSON.stringify(m)}`);
  { const bl = await blank(p); ok(!bl.length, `${w} EN: không khoảng trống thừa ${bl.join('; ')}`); const ty = await typo(p); ok(!ty.length, `${w} EN: luật chữ (độ đậm, tương phản, họ font) ${ty.slice(0, 4).join('; ')}`); const lb = await labels(p); ok(lb.n >= 3 && !lb.bad.length, `${w} EN: ${lb.n} dòng thẻ đều mở đầu bằng nhãn đậm ${lb.bad.slice(0, 3).join('; ')}`); const ch = await chips(p); ok(ch.n >= 8 && !ch.bad.length, `${w} EN: ${ch.n} chip mã máy, mọi mã nằm trong chip ${ch.bad.slice(0, 3).join('; ')}`); const dt = await dots(p); ok(dt.n >= 8 && !dt.bad.length, `${w} EN: ${dt.n} chấm tròn pastel đặc, không emoji ${dt.bad.slice(0, 3).join('; ')}`); const co = await colors(p); enColors[w] = co.n; ok(co.n >= 9 && !co.bad.length, `${w} EN: ${co.n} tên màu (tiêu đề, chú giải, tóm tắt) tô đúng màu ${co.bad.slice(0, 3).join('; ')}`); ok(await faces(p) >= 1, `${w} EN: font Lexend Deca nạp từ dữ liệu nhúng`); }
  await p.screenshot({ path: `${out}/en-${w}.png`, fullPage: true });
  await p.click('#rp-lang'); await p.waitForTimeout(150);
  ok(await p.evaluate(() => document.documentElement.dataset.lang) === 'vi' && await vis(p, '.vi') && !await vis(p, '.en'), `${w}: bấm nút đổi cả trang sang tiếng Việt`);
  m = await lay(p); ok(m.sw <= 0 && m.over === 0, `${w} VI: không cuộn ngang, không chữ tràn ${JSON.stringify(m)}`);
  { const bl = await blank(p); ok(!bl.length, `${w} VI: không khoảng trống thừa ${bl.join('; ')}`); const ty = await typo(p); ok(!ty.length, `${w} VI: luật chữ ${ty.slice(0, 4).join('; ')}`); const lb = await labels(p); ok(lb.n >= 3 && !lb.bad.length, `${w} VI: ${lb.n} dòng thẻ đều mở đầu bằng nhãn đậm ${lb.bad.slice(0, 3).join('; ')}`); const ch = await chips(p); ok(ch.n >= 8 && !ch.bad.length, `${w} VI: ${ch.n} chip mã máy, mọi mã nằm trong chip ${ch.bad.slice(0, 3).join('; ')}`); const dt = await dots(p); ok(dt.n >= 8 && !dt.bad.length, `${w} VI: ${dt.n} chấm tròn pastel đặc, không emoji ${dt.bad.slice(0, 3).join('; ')}`); const co = await colors(p); ok(co.n === enColors[w] && !co.bad.length, `${w} VI: ${co.n} tên màu tô đúng màu (phải bằng EN ${enColors[w]}) ${co.bad.slice(0, 3).join('; ')}`); ok(await faces(p) >= 2, `${w} VI: nạp cả bộ chữ Việt và Latin`); }
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
