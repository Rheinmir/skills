// The gallery: a grid of live previews, filters and search, and a detail page per component (#/c/<id>).
(() => {
  const { items, layouts = [], skins, meta } = JSON.parse(document.getElementById("g-data").textContent);
  const PRODUCT = meta.product, PAGE = `${meta.product} UIUX Map`;
  const $ = (s, el = document) => el.querySelector(s);
  const byId = new Map(items.map((i) => [i.id, i]));
  const store = { get: (k) => { try { return localStorage.getItem(k); } catch { return null; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch {} } };
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  // Inline markdown the reports use: `code`, **bold**, and continuation lines as a list.
  const inline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\[([^\]]+)\]\([^)]*\)/g, "$1");
  const md = (s) => {
    const [first, ...rest] = String(s ?? "").split("\n");
    return inline(first) + (rest.length ? `<ul>${rest.map((l) => `<li>${inline(l)}</li>`).join("")}</ul>` : "");
  };
  const STATUS = { full: "Có đủ", partial: "Có một phần", none: "Chưa có" };
  const tagOf = (i) => (i.kind === "catalogue" ? i.group : i.group.replace(/\s*\(.*\)/, ""));

  // ── theme and skin ──
  const root = document.documentElement;
  const setTheme = (t) => { root.dataset.gTheme = t; store.set("g-theme", t); $("#theme-label").textContent = t === "dark" ? "Nền sáng" : "Nền tối"; };
  setTheme(store.get("g-theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  $("#theme").onclick = () => setTheme(root.dataset.gTheme === "dark" ? "light" : "dark");
  const skinSel = $("#skin");
  if (!skins.length) skinSel.closest("label").hidden = true;
  skinSel.innerHTML = skins.map((s) => `<option value="${s.id}">${esc(s.name)}</option>`).join("");
  const setSkin = (id) => { if (!id) return; root.setAttribute(meta.skinAttr || "data-skin", id); skinSel.value = id; store.set("g-skin", id); requestAnimationFrame(fitAll); };
  skinSel.onchange = () => setSkin(skinSel.value);

  // ── previews fit their stage ──
  // A demo sits in a fixed frame its content may fill only a corner of. Frame the content itself: the union of what is
  // drawn (leaves, filled or bordered boxes, media), clipped to the frame, then scale it (never above 1:1) and centre it.
  const MEDIA = /^(svg|img|canvas|video|input|textarea|select|button|hr)$/i;
  const transparent = (c) => !c || c === "transparent" || /rgba?\([^)]*,\s*0\)$/.test(c) || /\/\s*0\)$/.test(c);
  function drawn(box) {
    const origin = box.getBoundingClientRect();
    const frame = box.querySelector(".demo-root > *");
    const clip = (frame ?? box).getBoundingClientRect();
    let l = Infinity, t = Infinity, r = -Infinity, b = -Infinity;
    for (const el of box.querySelectorAll(".demo-root *")) {
      if (el === frame || (el.ownerSVGElement && el.ownerSVGElement !== el)) continue;
      const rect = el.getBoundingClientRect();
      if (rect.width < 1 || rect.height < 1) continue;
      const cs = getComputedStyle(el);
      if (cs.visibility === "hidden" || cs.opacity === "0") continue;
      const visual = !el.firstElementChild || MEDIA.test(el.tagName) || !transparent(cs.backgroundColor)
        || parseFloat(cs.borderTopWidth) > 0 || parseFloat(cs.borderLeftWidth) > 0 || cs.boxShadow !== "none";
      if (!visual) continue;
      l = Math.min(l, Math.max(rect.left, clip.left)); t = Math.min(t, Math.max(rect.top, clip.top));
      r = Math.max(r, Math.min(rect.right, clip.right)); b = Math.max(b, Math.min(rect.bottom, clip.bottom));
    }
    if (!(r > l && b > t)) return { x: 0, y: 0, w: box.offsetWidth, h: box.offsetHeight };
    return { x: l - origin.left, y: t - origin.top, w: r - l, h: b - t };
  }
  function fit(stage) {
    const box = stage.querySelector(".g-fit");
    if (!box) return;
    box.style.transform = "none";
    const big = stage.hasAttribute("data-big");
    // room around the content: 18px on a card, less on a narrow layout slot so a thin column is not all margin
    const pad = big ? 32 : Math.max(3, Math.min(18, Math.min(stage.clientWidth, stage.clientHeight) * 0.08));
    const c = drawn(box);
    const sw = stage.clientWidth;
    const k = Math.min(1, (sw - 2 * pad) / c.w, big ? Infinity : (stage.clientHeight - 2 * pad) / c.h);
    const sh = big ? Math.max(300, c.h * k + 2 * pad) : stage.clientHeight;
    if (big) stage.style.height = `${sh}px`;
    box.style.transform = `translate(${(sw - c.w * k) / 2 - c.x * k}px, ${(sh - c.h * k) / 2 - c.y * k}px) scale(${k})`;
  }
  const fitAll = () => document.querySelectorAll(".g-prev").forEach(fit);
  const io = new ResizeObserver((entries) => entries.forEach((e) => fit(e.target)));

  // ── list ──
  const grid = $("#grid");
  const state = { scope: "all", group: "", status: "", q: "" };
  grid.innerHTML = items.map((i) => `
    <article class="g-card" data-id="${i.id}" tabindex="0" role="link" aria-label="${esc(i.name)}">
      <div class="g-prev"><div class="g-fit" inert>${i.html}</div></div>
      <div class="g-meta">
        <div class="g-name"><span class="g-dot" data-s="${i.status}" title="${STATUS[i.status]}"></span><b>${esc(i.name)}</b><span class="g-tag">${esc(tagOf(i))}</span></div>
        ${i.omb || i.slug ? `<div class="g-api">${esc(stripMd(i.omb) || i.slug)}</div>` : ""}
        <div class="g-line">${esc(stripMd(i.line))}</div>
      </div>
    </article>`).join("") + `<p class="g-empty" hidden>Không có thành phần nào khớp.</p>`;
  function stripMd(s) { return String(s ?? "").replace(/\*\*|`/g, "").replace(/\[([^\]]+)\]\([^)]*\)/g, "$1").split("\n")[0]; }
  grid.querySelectorAll(".g-prev").forEach((p) => io.observe(p));
  grid.addEventListener("click", (e) => { const c = e.target.closest(".g-card"); if (c) location.hash = `#/c/${c.dataset.id}`; });
  grid.addEventListener("keydown", (e) => { const c = e.target.closest(".g-card"); if (c && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); location.hash = `#/c/${c.dataset.id}`; } });

  const groups = [...new Set(items.map((i) => i.group))];
  const chip = (attr, val, label, n) => `<button type="button" class="g-chip" data-${attr}="${esc(val)}" aria-pressed="false">${esc(label)}${n != null ? ` <i>${n}</i>` : ""}</button>`;
  $("#groups").innerHTML = chip("group", "", "Mọi nhóm") + groups.map((g) => chip("group", g, g, items.filter((i) => i.group === g).length)).join("");
  $("#statuses").innerHTML = chip("status", "", "Mọi trạng thái") + ["full", "partial", "none"].map((s) => chip("status", s, STATUS[s], items.filter((i) => i.status === s).length)).join("");
  $("#groups").onclick = (e) => { const b = e.target.closest("[data-group]"); if (b) { state.group = b.dataset.group; apply(); } };
  $("#statuses").onclick = (e) => { const b = e.target.closest("[data-status]"); if (b) { state.status = b.dataset.status; apply(); } };
  const q = $("#q");
  q.oninput = () => { state.q = q.value.trim().toLowerCase(); if (!location.hash.startsWith("#/c/")) apply(); else location.hash = scopeHash(); };
  const findField = () => { if (document.body.dataset.view !== "list") location.hash = scopeHash(); requestAnimationFrame(() => { q.scrollIntoView({ block: "center" }); q.focus(); q.select(); }); };
  $("#find").onclick = findField;
  addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); findField(); }
    if (e.key === "Escape" && location.hash.startsWith("#/c/")) location.hash = scopeHash();
  });
  const haystack = new Map(items.map((i) => [i.id, [i.name, i.omb, i.slug, i.line, i.group, i.id, ...(i.aliases || [])].join(" ").toLowerCase()]));
  function apply() {
    let shown = 0;
    for (const card of grid.querySelectorAll(".g-card")) {
      const i = byId.get(card.dataset.id);
      const ok = (state.scope === "all" || i.kind === state.scope) && (!state.group || i.group === state.group)
        && (!state.status || i.status === state.status) && (!state.q || state.q.split(/\s+/).every((w) => haystack.get(i.id).includes(w)));
      card.hidden = !ok; shown += ok;
    }
    grid.querySelector(".g-empty").hidden = shown > 0;
    $("#count").textContent = `${shown} / ${items.length} thành phần`;
    document.querySelectorAll("[data-group]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.group === state.group)));
    document.querySelectorAll("[data-status]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.status === state.status)));
    document.querySelectorAll(".g-scopes a").forEach((a) => { if (a.dataset.scope === state.scope) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
    requestAnimationFrame(fitAll);
  }
  const scopeHash = () => (state.scope === "all" ? "#/" : `#/${state.scope}`);

  // ── detail ──
  const detail = $("#detail"), list = $("#list");
  const copy = async (btn, text) => {
    try { await navigator.clipboard.writeText(text); } catch {
      const t = document.createElement("textarea"); t.value = text; document.body.append(t); t.select(); document.execCommand("copy"); t.remove();
    }
    const label = btn.textContent; btn.textContent = "Đã chép"; btn.dataset.done = "";
    setTimeout(() => { btn.textContent = label; delete btn.dataset.done; }, 1400);
  };
  const markdownOf = (i) => [
    `### ${i.name}${i.slug ? ` — \`${i.slug}\`` : ""}`, "", stripMd(i.description || i.line), "",
    i.omb && `- Tên trong code: ${i.omb.split("\n")[0]}`, i.definitions && `- Định nghĩa: ${i.definitions.split("\n")[0]}`,
    i.variants && `- Biến thể: ${i.variants.split("\n")[0]}`, i.source && `- Demo dựng từ: \`${i.source}\``,
  ].filter((l) => l !== false && l !== "").join("\n");
  const promptOf = (i) => `Trong ${PRODUCT}, tôi cần thành phần "${i.name}"${i.slug ? ` (${i.slug})` : ""}. ${stripMd(i.description || i.line)}\n`
    + `Dùng lại thứ đã có, đừng viết mới: ${stripMd(i.omb) || "xem phần định nghĩa"}.\n`
    + (i.definitions ? `Định nghĩa nằm ở: ${stripMd(i.definitions)}.\n` : "")
    + `Giữ đúng token của skin (bg-*, text-ink*, rounded-*), ${meta.houseFont ? `chữ ${meta.houseFont}, ` : ""}và đối chiếu với demo ${i.source ? `dựng từ ${i.source}` : ""}.`;
  function showDetail(id) {
    const i = byId.get(id);
    if (!i) { location.hash = "#/"; return; }
    const visible = items.filter((x) => state.scope === "all" || x.kind === state.scope);
    const at = visible.findIndex((x) => x.id === id);
    const prev = visible[(at - 1 + visible.length) % visible.length], next = visible[(at + 1) % visible.length];
    const snippets = [...i.samples.map((s) => ({ title: s.path, lang: s.lang, code: s.code })), { title: `HTML demo · ${i.id}.html`, lang: "html", code: i.html }];
    detail.innerHTML = `
      <div class="g-crumbs">
        <span class="g-path"><a href="${scopeHash()}">Chỉ mục</a> / ${esc(i.kind === "catalogue" ? `Danh mục · ${i.group}` : `Ngoài danh mục · ${i.group}`)}</span>
        <button class="g-btn" data-copy="name" type="button">Chép tên</button>
        <button class="g-btn" data-copy="md" type="button">Chép dạng Markdown</button>
        <button class="g-btn" data-copy="prompt" type="button">Chép prompt</button>
      </div>
      <div class="g-detail">
        <div>
          <div class="g-prev" data-big><div class="g-fit">${i.html}</div></div>
          ${i.source ? `<p class="g-caption">Dựng từ <code>${esc(i.source)}</code></p>` : ""}
        </div>
        <div>
          <h1 class="g-title">${esc(i.name)}</h1>
          ${i.omb || i.slug ? `<div class="g-sub">/ ${esc(stripMd(i.omb) || "")}${i.slug ? `${i.omb ? " · " : ""}${esc(i.slug)}` : ""} /</div>` : ""}
          ${i.aliases?.length ? `<div class="g-alias">còn gọi là ${esc(i.aliases.join(", "))}</div>` : ""}
          <div class="g-status"><span class="g-dot" data-s="${i.status}"></span>${esc(i.statusText ? stripMd(i.statusText).replace(/^[✅🟡❌]️?\s*/u, "") : STATUS[i.status])}</div>
          <div class="g-prose">${inline(i.description || i.line)}</div>
          <div class="g-mapbox"><h2 class="g-h">Map vào thành phần này khi</h2>
            <div class="g-field">${esc(i.cue)}${i.aliases?.length ? `<br>Người ta còn gọi: ${esc(i.aliases.join(", "))}.` : ""}${i.omb ? `<br>Dùng lại: <code>${esc(stripMd(i.omb))}</code>` : ""}</div></div>
          ${i.variants ? `<h2 class="g-h">Biến thể</h2><div class="g-field">${md(i.variants)}</div>` : ""}
          ${i.definitions ? `<h2 class="g-h">Định nghĩa</h2><div class="g-field">${md(i.definitions)}</div>` : ""}
          ${i.usage ? `<h2 class="g-h">Nơi dùng</h2><div class="g-field">${md(i.usage)}</div>` : ""}
          ${i.notes ? `<h2 class="g-h">Ghi chú refactor</h2><div class="g-field">${md(i.notes)}</div>` : ""}
        </div>
      </div>
      <div class="g-codewrap">
        <h2 class="g-h">Trong code</h2>
        <div class="g-codetabs">${snippets.map((s, n) => `<button type="button" class="g-chip" data-tab="${n}" aria-pressed="${n === 0}">${esc(s.lang === "html" ? "HTML demo" : s.title.split("/").pop())}</button>`).join("")}</div>
        ${snippets.map((s, n) => `<div class="g-snip" data-pane="${n}" ${n ? "hidden" : ""}><header><span>${esc(s.title)}</span><button class="g-btn" type="button" data-copy-pane="${n}">Chép code</button></header><pre><code>${esc(s.code)}</code></pre></div>`).join("")}
      </div>
      <nav class="g-pager" aria-label="Thành phần kế bên">
        <a href="#/c/${prev.id}">← Trước<b>${esc(prev.name)}</b></a>
        <a href="#/c/${next.id}" style="text-align:end">Sau →<b>${esc(next.name)}</b></a>
      </nav>`;
    detail.onclick = (e) => {
      const b = e.target.closest("button"); if (!b) return;
      if (b.dataset.copy === "name") copy(b, i.name);
      if (b.dataset.copy === "md") copy(b, markdownOf(i));
      if (b.dataset.copy === "prompt") copy(b, promptOf(i));
      if (b.dataset.copyPane) copy(b, snippets[Number(b.dataset.copyPane)].code);
      if (b.dataset.tab) {
        detail.querySelectorAll("[data-tab]").forEach((t) => t.setAttribute("aria-pressed", String(t === b)));
        detail.querySelectorAll("[data-pane]").forEach((p) => { p.hidden = p.dataset.pane !== b.dataset.tab; });
      }
    };
    list.hidden = true; detail.hidden = false;
    document.title = `${i.name} · ${PAGE}`;
    scrollTo(0, 0);
    const big = detail.querySelector(".g-prev"); io.observe(big); requestAnimationFrame(() => fit(big));
  }

  // ── routes: #/, #/catalogue, #/outside, #/c/<id> ──
  const views = { list, ontology: $("#ontology"), layouts: $("#layouts"), detail };
  function show(view) {
    for (const [k, el] of Object.entries(views)) el.hidden = k !== view;
    document.body.dataset.view = view;
    document.querySelectorAll(".g-nav a").forEach((a) => { if (a.dataset.nav === (view === "detail" ? "list" : view)) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
  }
  function route() {
    const h = location.hash.replace(/^#/, "") || "/";
    const m = /^\/c\/(.+)$/.exec(h);
    if (m) { show("detail"); return showDetail(decodeURIComponent(m[1])); }
    const lm = /^\/layouts(?:\/(.+))?$/.exec(h);
    if (lm) { show("layouts"); renderLayouts(lm[1] && decodeURIComponent(lm[1])); scrollTo(0, 0); document.title = `Layout · ${PAGE}`; return; }
    if (h === "/ontology") { show("ontology"); renderOntology(); scrollTo(0, 0); document.title = `Ontology · ${PAGE}`; return; }
    if (h === "/catalogue" || h === "/outside" || h === "/") state.scope = h === "/catalogue" ? "catalogue" : h === "/outside" ? "outside" : "all";
    detail.innerHTML = ""; show("list");
    document.title = PAGE;
    apply();
  }

  // ── ontology: the same JSON an agent reads, shown for people ──
  const onto = JSON.parse(document.getElementById("ui-ontology").textContent);
  function renderOntology() {
    const el = views.ontology;
    if (el.dataset.ready) return;
    el.dataset.ready = "1";
    const props = Object.entries(onto.properties).map(([k, v]) => `<tr><th>${esc(k)}</th><td>${esc(v)}</td></tr>`).join("");
    const tree = onto.groups.map((g) => `<details><summary>${esc(g.name)} <i>${g.components.length}</i></summary><ul>${g.components.map((id) => {
      const c = onto.components.find((x) => x.id === id);
      return `<li><a href="#/c/${c.id}">${esc(c.name)}</a> <span class="g-dot" data-s="${c.status}"></span><div class="g-map">Map khi: ${esc(c.cue)}</div></li>`;
    }).join("")}</ul></details>`).join("");
    el.innerHTML = `<div class="g-doc">
      <p class="g-eyebrow">Ontology</p><h1 class="g-h1">Khi nào map vào thành phần nào</h1>
      <p>File này là tài liệu cho agent. Đưa nó cho agent cùng một thiết kế cần dựng: agent cắt thiết kế thành vùng, đối chiếu từng vùng với ${onto.components.length} thành phần dưới đây theo dấu hiệu nhận diện và tên gọi khác, rồi dùng lại thứ app đã có kèm code mẫu. Bản đọc được bằng máy nằm ngay trong file: <code>&lt;script id="ui-ontology" type="application/ld+json"&gt;</code>.</p>
      <div class="g-cta" style="margin-top:18px"><button class="g-btn" type="button" id="copy-onto">Chép ontology JSON</button><button class="g-btn" type="button" id="copy-rules">Chép quy tắc map</button></div>
      <h2 class="g-h">Mô hình</h2>
      <table class="g-table"><tr><th>Group</th><td>${esc(onto.classes.Group)}</td></tr><tr><th>Component</th><td>${esc(onto.classes.Component)}</td></tr></table>
      <h2 class="g-h">Thuộc tính của một thành phần</h2><table class="g-table">${props}</table>
      <h2 class="g-h">Quy tắc map</h2><ol class="g-rules">${onto.mappingRules.map((r) => `<li>${esc(r)}</li>`).join("")}</ol>
      <h2 class="g-h">${onto.groups.length} nhóm · ${onto.components.length} thành phần</h2><div class="g-tree">${tree}</div>
    </div>`;
    $("#copy-onto").onclick = (e) => copy(e.currentTarget, JSON.stringify(onto, null, 2));
    $("#copy-rules").onclick = (e) => copy(e.currentTarget, onto.mappingRules.map((r, n) => `${n + 1}. ${r}`).join("\n"));
  }

  // ── layouts: common page layouts drawn with this map's own components ──
  function renderLayouts(one) {
    const el = views.layouts;
    const want = one && layouts.some((l) => l.id === one) ? one : "";
    if (el.dataset.ready !== `:${want}`) {
      el.dataset.ready = `:${want}`;
      const slot = (area, s) => s.id && byId.has(s.id)
        ? `<div class="g-prev g-slot" style="grid-area:${area}"${s.key ? " data-key" : ""}><div class="g-fit" inert>${byId.get(s.id).html}</div></div>`
        : `<div class="g-wire" data-wire="${esc(s.wire ?? "block")}" style="grid-area:${area}"${s.key ? " data-key" : ""}><i></i><i></i><i></i></div>`;
      const card = (l) => {
        const base = Object.entries(l.slots).filter(([a]) => a !== l.overlay);
        const over = l.overlay && l.slots[l.overlay];
        const used = Object.values(l.slots).filter((s) => s.id && byId.has(s.id)).map((s) => s.id);
        return `<article class="g-lay"${want ? " data-big" : ` data-href="#/layouts/${l.id}" tabindex="0" role="link" aria-label="${esc(l.name)}"`}>
          <h3>${esc(l.name)}</h3>
          <div class="g-lay-frame">
            <div class="g-lay-bar"><i></i><i></i><i></i><span></span></div>
            <div class="g-lay-grid" style="grid-template-columns:${esc(l.columns)};grid-template-rows:${esc(l.rows)};grid-template-areas:${l.areas.map((r) => `'${esc(r)}'`).join(" ")}">
              ${base.map(([a, s]) => slot(a, s)).join("")}
              ${over ? `<div class="g-lay-over">${over.id && byId.has(over.id) ? `<div class="g-prev g-slot" data-key><div class="g-fit" inert>${byId.get(over.id).html}</div></div>` : `<div class="g-wire" data-key><i></i><i></i><i></i></div>`}</div>` : ""}
            </div>
          </div>
          <p class="g-lay-cue">${esc(l.cue)}</p>
          <p class="g-lay-uses">${used.length ? `Dùng: ${used.map((id) => `<a href="#/c/${id}">${esc(byId.get(id).name)}</a>`).join(", ")}.` : "Chưa có thành phần khớp: khung xám là chỗ cần dựng."}</p>
        </article>`;
      };
      el.innerHTML = want
        ? `<div class="g-doc g-doc-wide"><div class="g-crumbs"><span class="g-path"><a href="#/layouts">Layout</a> / ${esc(layouts.find((l) => l.id === want).name)}</span></div>
            <div class="g-lays g-lays-one">${card(layouts.find((l) => l.id === want))}</div></div>`
        : `<div class="g-doc g-doc-wide">
        <p class="g-eyebrow">Layout</p><h1 class="g-h1">Bố cục trang, dựng bằng chính thành phần này</h1>
        <p>Mỗi bố cục lấy thành phần khớp nhất trong map cho từng ô; ô viền cam là ô đặc trưng của bố cục. Khung xám là chỗ map chưa có thành phần phù hợp. Bấm một bố cục để xem lớn. Ghép này cũng nằm trong ontology (<code>layouts</code>) để agent dựng đúng bố cục.</p>
        <div class="g-lays">${layouts.map(card).join("")}</div></div>`;
      el.onclick = (e) => { if (e.target.closest("a")) return; const c = e.target.closest(".g-lay[data-href]"); if (c) location.hash = c.dataset.href; };
      el.onkeydown = (e) => { const c = e.target.closest(".g-lay[data-href]"); if (c && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); location.hash = c.dataset.href; } };
      el.querySelectorAll(".g-prev").forEach((p) => io.observe(p));
    }
    requestAnimationFrame(() => el.querySelectorAll(".g-prev").forEach(fit));
  }

  addEventListener("hashchange", route);
  addEventListener("resize", () => requestAnimationFrame(fitAll));
  // Hero frames: each screen stacks real demos, each scaled to the screen's width; the caption names them.
  function fillScreens() {
    for (const screen of document.querySelectorAll(".g-screen[data-ids]")) {
      const ids = screen.dataset.ids.split(",").filter((id) => byId.has(id));
      if (!screen.dataset.ready) {
        screen.dataset.ready = "1";
        screen.innerHTML = ids.map((id) => `<div class="g-fill"><div class="g-fit" inert>${byId.get(id).html}</div></div>`).join("");
        const cap = screen.closest(".g-frame").querySelector("figcaption");
        cap.innerHTML = `${esc(cap.dataset.cap)}: ${ids.map((id) => `<a href="#/c/${id}">${esc(byId.get(id).name)}</a>`).join(", ")}.`;
      }
      const w = screen.clientWidth;
      for (const fill of screen.querySelectorAll(".g-fill")) {
        const box = fill.firstElementChild, frame = box.querySelector(".demo-root > *") ?? box;
        box.style.transform = "none";
        const k = w / frame.offsetWidth;
        box.style.transform = `scale(${k})`;
        fill.style.height = `${frame.offsetHeight * k}px`;
      }
      if (!screen.closest(".g-phone")) screen.style.height = `${[...screen.children].reduce((h, f) => h + f.offsetHeight, 0)}px`;
    }
  }
  fillScreens();
  addEventListener("resize", () => requestAnimationFrame(fillScreens));
  document.fonts?.ready.then(fillScreens);
  setSkin((skins.some((s) => s.id === store.get("g-skin")) && store.get("g-skin")) || meta.defaultSkin || skins[0]?.id);
  route();
  document.fonts?.ready.then(fitAll);
})();
