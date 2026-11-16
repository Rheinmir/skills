---
name: ui-inventory
description: Kiểm kê TOÀN BỘ thành phần UI của một frontend có kiểm chứng (mỗi path:line và code mẫu được máy đối chiếu với mã nguồn), đối chiếu danh mục chuẩn Name That UI (91 thành phần macOS + web, 14 phong cách, 18 cặp so sánh), đặt tên chuẩn cho mọi thành phần ngoài danh mục, dựng demo tĩnh từng component bằng chính class/token của app rồi xuất MỘT trang HTML có tab, Gallery và so sánh A/B cũ–mới (song song, thanh trượt, chỉ A, chỉ B) giữa skin cũ và skin/giao diện mới. Gọi khi user nói "kiểm kê UI", "quét toàn bộ component", "đối chiếu namethatui", "ui inventory", "liệt kê thành phần giao diện", "render component tượng trưng", "so sánh A/B giao diện cũ mới", "chuẩn bị refactor giao diện", hoặc /ui-inventory. KHÁC `design-prim` (dọn slop, sửa code UI) và `visual-qa` (chấm ảnh chụp màn hình) — skill này KHÔNG sửa UI của app, chỉ lập bản đồ + demo + so sánh.
metadata:
  design-standard: "solid-what-how/1"
  contract-version: "1.0.0"
  loop: utils
---

# Skill: ui-inventory

Lập bản đồ đầy đủ, kiểm chứng được, của mọi thành phần giao diện trong một app, làm nền cho một đợt refactor giao diện lớn. Kết quả là một bộ tài liệu Markdown trong repo cùng **một tệp HTML tự chứa**. Trong tệp đó, mỗi component được dựng lại bằng chính CSS của app và đặt cạnh nhau ở hai phiên bản: A (giao diện cũ) và B (giao diện mới).

Chạy thật lần đầu trên OpenMausBot (React 19 + Tailwind 4, 629 tệp `.tsx`): 91/91 mục danh mục, 112 thành phần riêng được đặt tên, 203 demo, 2756 tham chiếu và 262 code mẫu đều được kiểm, 0 lỗi.

**Bẫy đã trả giá, đọc trước khi chạy:**
1. **Không escape code inline thì trang chết.** Báo cáo chứa `` `<select>` ``, `` `<textarea>` ``. Nếu renderer Markdown trả chữ thô, trình duyệt mở thẻ thật, thẻ đó nuốt phần còn lại của trang, kể cả `<script>`, và mọi tab đều "không bấm được". `build-page.mjs` đã escape cả codespan lẫn HTML thô; đừng thay renderer.
2. **CSS của app chứa `html, body { overflow: hidden }`** (app dạng full-screen). Khuôn trang đã ghi đè lại; demo nào dùng `fixed` thì phải đổi sang `absolute`, vì khung demo có `transform` để giữ nó trong hộp.
3. **Tailwind đọc chữ thô của tệp.** `class="[&amp;_rect]:…"` trong HTML không sinh CSS. `compile-demos.mjs` giải mã class ra `classes.txt` cho Tailwind quét.
4. **Agent bịa class.** Luôn chạy `validate-demos.mjs`; mọi class không có CSS đều bị báo (trừ class móc mà app tự dùng, khai qua `--allow`).
5. **Agent bịa khẳng định.** Mỗi báo cáo phải qua `verify-refs.mjs`. Riêng khẳng định "không có X" (❌) phải tự grep lại vài mục; đã có trường hợp báo cáo sai ở chỗ này.
6. **Số dòng sẽ trôi.** Hãy ghim bản kiểm kê vào một commit và trỏ link trong HTML về commit đó (`--blob …/blob/<sha>`). Sau đó sửa mã (ví dụ thêm skin) thì `verify-refs` sẽ đỏ ở tệp đã đổi; khi đó kiểm lại trên worktree của commit đã ghim.

## WHAT

### Purpose và context
- **Purpose:** trả lời "app này đang dùng những thành phần giao diện nào, ở đâu, trông ra sao, và giao diện mới sẽ làm chúng khác đi thế nào". Câu trả lời phải đủ chi tiết để làm danh sách việc cho refactor.
- **Trigger (when to use):**
  - Sắp refactor hoặc redesign toàn bộ UI và cần biết trước có những gì.
  - Có danh mục thành phần chuẩn (mặc định Name That UI) và cần đối chiếu từng mục.
  - Có giao diện mới (skin, theme, bộ token, hoặc tệp HTML thiết kế) và cần xem A/B trên từng component.
  - User nói "kiểm kê UI", "quét toàn bộ component", "đối chiếu namethatui", "so sánh A/B", "/ui-inventory".
- **Non-goals:** KHÔNG sửa code UI của app (việc đó của `design-prim` / `hallmark`). KHÔNG chấm điểm ảnh chụp (`visual-qa`). KHÔNG dựng skin mới; skin B phải có sẵn trong CSS của app trước khi so sánh (xem B01).

### Mental model
`danh mục (fetch) → agent đối chiếu theo lô mục + agent bản đồ theo lô tệp + agent nền móng → verify-refs (máy) → aggregate + canon.json (tên chuẩn) → README tổng → agent demo theo lô → compile-demos (CSS thật) → validate-demos → build-page (tab · Gallery · A/B) → browser-check (bấm thật, ảnh) → commit/push`.

### Input và output contract
| | Field | Required? | Ý nghĩa |
|---|---|---|---|
| In | repo app (đã `install`) | có | nơi đọc mã và biên dịch CSS |
| In | stylesheet chính (`--css src/styles.css`) | có cho demo | Tailwind v4 qua `@tailwindcss/vite`; app khác thì đưa CSS đã build cho `build-page --css` |
| In | danh mục chuẩn | không | mặc định `https://uiux.giatbh.io.vn/namethatui/data.js` |
| In | skin cũ (A) và skin mới (B) | có cho A/B | giá trị `data-skin` đã có trong CSS của app, ví dụ `midnight,daylight` vs `ctd-dots` |
| Out | `docs/ui-inventory/parts/*.md` | có | mỗi mục: trạng thái ✅/🟡/❌, tên trong app, `path:line`, số chỗ dùng, biến thể, lệnh grep, code mẫu nguyên văn, ghi chú refactor, khối JSON cuối tệp |
| Out | `docs/ui-inventory/canon.json` + `README.md` | có | tên chuẩn theo nhóm cho thành phần ngoài danh mục; bảng tổng và việc lớn cho refactor |
| Out | `docs/ui-inventory/demos/*.html` | có | `<n>-<slug>.html` cho mục danh mục, `x-<kebab>.html` cho thành phần riêng |
| Out | `ui-inventory.html` (gốc repo) | có | một tệp, mở offline được |

### Rules và capabilities
- RULE-01 (MUST): Mọi khẳng định có `path:line`; mọi code mẫu chép nguyên văn và nằm sau `` `path:start-end` `` (hoặc `/* path:start-end */` trong khối). Chưa qua `verify-refs.mjs` (0 FAIL) thì chưa được tổng hợp.
- RULE-02 (MUST): Demo chỉ dùng class và token có sẵn của app (chép từ `className` thật), không thêm CSS mới, không `<script>`, không URL ngoài. `validate-demos.mjs` phải 0 lỗi.
- RULE-03 (MUST): Trang cuối là MỘT tệp HTML; mỗi lần dựng phải qua `browser-check.mjs`: bấm thật mọi tab chính, các nút A/B và một link "Chi tiết", không có lỗi JS, rồi chụp ít nhất một ảnh A|B để tự xem.
- RULE-04 (MUST): Báo con số thật. Danh mục Name That UI có 91 thành phần, dù trang ghi "93". Đếm từ dữ liệu, đừng chép lời người dùng.
- RULE-05 (SHOULD): Chia việc cho agent song song: ≤16 mục danh mục mỗi agent, ≤160 tệp mỗi agent bản đồ, ≤45 demo mỗi agent; mỗi agent ghi thẳng ra tệp riêng và chỉ trả tóm tắt 5 dòng. Agent dùng thư mục nháp riêng (đã có hai agent ghi đè nháp của nhau).
- RULE-06 (MUST): Không sửa mã nguồn của app trong skill này, chỉ ghi vào `docs/ui-inventory/`, `.demo-build/` (đã được git-exclude) và `ui-inventory.html`.
- Capabilities: đọc và grep toàn repo; chạy Node ≥ 20; chạy `vite` của repo; điều khiển Chrome/Edge headless qua DevTools protocol; ghi tài liệu và tệp HTML.

### Failure boundaries
- `verify-refs` còn FAIL → **partial**: sửa báo cáo cho khớp mã (hoặc bỏ khẳng định), không sửa script cho xanh.
- Repo không có `vite` + `@tailwindcss/vite` → không biên dịch demo bằng CSS thật: **blocked** cho phần demo. Đưa `--css` là CSS đã build của app, hoặc dừng ở bộ tài liệu.
- Skin B chưa có trong CSS của app → A/B vô nghĩa: **blocked**, cần làm skin trước (B01).
- `browser-check` có lỗi JS hoặc tab không hiện → **failed**, không giao tệp.

## HOW

### Main workflow
| Step | Type | Inputs | Action | Outputs/exit | Failure/next |
|---|---|---|---|---|---|
| W01 | deterministic | URL danh mục | `node scripts/fetch-catalogue.mjs --out docs/ui-inventory/parts/_catalogue.md` | danh mục đánh số | mạng lỗi → user đưa tệp |
| W02 | deterministic | repo | Đếm tệp UI, chia lô tệp (≈150/lô), đọc tài liệu thiết kế của repo (primitive dùng chung) | danh sách lô | — |
| W03 | judgment | danh mục + lô | Chạy song song: agent đối chiếu (mỗi agent ≤16 mục), agent bản đồ (mỗi agent một lô tệp), một agent nền móng (phong cách, cặp so sánh, token, motion, đếm vi phạm). Prompt ở `references/agent-prompts.md` | `parts/A-…md`, `parts/M-…md`, `parts/G-foundation.md` | agent chết → chạy lại đúng lô đó |
| W04 | deterministic | từng `parts/*.md` | `node scripts/verify-refs.mjs --repo . docs/ui-inventory/parts/X.md` ngay khi agent xong | 0 FAIL | FAIL → sửa báo cáo |
| W05 | judgment | `aggregate.mjs` (tên thô) | Gộp tên trùng nghĩa thành tên chuẩn theo nhóm chức năng → `canon.json`; chạy lại `aggregate.mjs` tới khi "uncovered: none" | `canon.json` | — |
| W06 | judgment | JSON các phần | Viết `README.md`: kết quả nhanh, cách đọc, kiểm chứng, việc lớn cho refactor (gom ghi chú refactor), bảng 91 mục, bảng thành phần riêng. Tự grep lại 3–5 phát hiện lớn | README | — |
| W07 | judgment | parts + canon | Agent demo song song theo lô (spec `references/demo-spec.md`; chép spec vào `docs/ui-inventory/demos/README.md`) | `demos/*.html` | — |
| W08 | deterministic | demos | `node scripts/compile-demos.mjs --repo . --css <app css>` rồi `node scripts/validate-demos.mjs --repo . --allow <class móc>` | CSS đã biên dịch, 0 lỗi | class bịa → sửa demo |
| W09 | deterministic | mọi thứ trên | `node scripts/build-page.mjs --repo . --blob <…/blob/sha> --old <a1,a2> --new <b> --names "<id>=<Tên>" --brand <…> --mark <…> --drop-fonts "<font không dùng>"` | `ui-inventory.html` | — |
| W10 | effect | trang | `node scripts/browser-check.mjs --url file:///…/ui-inventory.html#gallery --click '#tab-gallery' --click '[data-ab="slider"]' --click '[data-old="<a2>"]' --shot ab.png`; xem ảnh | 0 lỗi, ảnh đúng | lỗi → sửa, dựng lại |
| W11 | effect | repo | Commit `docs/ui-inventory/` + `ui-inventory.html` (không commit `.demo-build/`), push nếu user yêu cầu | commit | — |

### Branches
| ID | Condition | Action | Return |
|---|---|---|---|
| B01 | User đưa thiết kế mới dạng tệp HTML/ảnh, chưa có skin | Dựng skin trong CSS của app trước (khối token `[data-skin=…]` + phần trang trí trong `@scope`), qua kiểm tra độ tương phản của repo nếu có, rồi quay lại W07 | W07 |
| B02 | App không dùng Tailwind | Bỏ `compile-demos`; build app một lần, đưa tệp CSS ra cho `build-page --css`, `validate-demos` vẫn chạy với CSS đó (đặt vào `.demo-build/out/assets/`) | W09 |
| B03 | Không có danh mục chuẩn / user chỉ muốn bản đồ | Bỏ W01, W03 (agent đối chiếu), giữ agent bản đồ + nền móng; trang vẫn có tab Gallery cho thành phần riêng | W04 |
| B04 | User chỉ muốn so sánh A/B trên bộ kiểm kê có sẵn | Chỉ W07–W10 | — |

### Workflow
```text
W01 → W02 → W03 ⇉ (mỗi phần xong) W04 → W05 → W06 → W07 → W08 → W09 → W10 → W11
          B03 bỏ đối chiếu ↗          B01 làm skin trước W07     B02 CSS đã build ↗
```

### Validation và handoff
- Output schema: báo cáo đúng khuôn trong `references/agent-prompts.md`; mỗi tệp kết thúc bằng một khối ```json parse được; `canon.json` là `{nhóm: {tên chuẩn: [tên thô…]}}`.
- Validation: `verify-refs.mjs` 0 FAIL trên mọi `parts/*.md` và `README.md`; `aggregate.mjs` "uncovered: none"; `validate-demos.mjs` 0 lỗi; `browser-check.mjs` 0 lỗi kèm ảnh A|B đã xem.
- Handoff: báo cho user số liệu thật (✅/🟡/❌, số thành phần riêng, số tệp, số tham chiếu đã kiểm), các chỗ demo còn mô phỏng (avatar, iframe, phần do OS vẽ), đường dẫn tệp HTML và commit.

### Examples và anti-patterns
- Ví dụ thật: repo `Rheinmir/openmausbot-study`, nhánh `ctd-dots`: `docs/ui-inventory/` cùng `ui-inventory.html` (A Midnight/Daylight vs B CTD Dots).
- Anti-pattern: một agent quét cả repo rồi viết tay một danh sách dài → không kiểm chứng được, thiếu thành phần.
- Anti-pattern: demo vẽ lại bằng CSS tự viết "cho giống" → không phản ánh token thật, A/B vô nghĩa.
- Anti-pattern: hai tệp HTML (cũ và mới) để người xem tự so → luôn dùng một trang có A/B.
- Anti-pattern: đổi skin bằng một công tắc chung → người xem phải nhớ bản trước; A/B phải hiện đồng thời.

## References
- `references/agent-prompts.md`: prompt mẫu cho agent đối chiếu, agent bản đồ tệp, agent nền móng, agent demo.
- `references/demo-spec.md`: quy ước một tệp demo (chép vào `docs/ui-inventory/demos/README.md` của repo đích).
- `scripts/`: `fetch-catalogue`, `verify-refs`, `aggregate`, `compile-demos`, `validate-demos`, `build-page` (+ `assets/page.html`), `browser-check`.
