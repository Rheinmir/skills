---
name: make-agent-uiux-map
description: "Bóc giao diện của MỘT trang web bất kỳ (URL) hoặc một bộ kiểm kê có sẵn ra MỘT file HTML tự chứa kiểu Name That UI — lưới mọi thành phần có bản xem trước chạy bằng chính CSS của trang, trang chi tiết kèm code mẫu thật, và ONTOLOGY (JSON nhúng script#ui-ontology) để agent tự map một thiết kế bất kỳ vào đúng thành phần mà áp giao diện. Standalone: mọi công cụ nằm trong thư mục skill (capture.mjs, snip.mjs, build-gallery.mjs, giao diện, danh mục 91 thành phần). Giao FILE, không host: in đường dẫn khi xong. Gọi khi user nói 'make-agent-uiux-map', 'uiux map', 'gallery thành phần', 'showcase kiểu name that ui', 'bóc component của web này ra html', 'kiểm kê giao diện trang X', 'ontology giao diện cho agent', 'gói UI thành một file để đưa agent', hoặc /make-agent-uiux-map <url>. KHÁC extract-site (trích token/DESIGN.md) và ui-kit-from-code (chép hệ thiết kế thành UI kit): skill này GỌI TÊN từng thành phần theo danh mục Name That UI và sinh ontology map."
metadata:
  design-standard: "solid-what-how/1"
  contract-version: "1.0.0"
  loop: utils
---

# Skill: make-agent-uiux-map

> **Giao file, không host.** Không bao giờ dựng localhost / http.server cho đầu ra. Xong việc thì đưa user đúng ba
> dòng `build-gallery.mjs` in ở cuối (`HTML:` đường dẫn tuyệt đối, `URL:` file://, `Open:` lệnh mở) kèm gợi ý
> `! open "<đường dẫn>"` (phiên chạy nền không tự bật trình duyệt được).

## WHAT

### Purpose và context
- **Purpose:** biến giao diện của một trang (hoặc một bộ kiểm kê có sẵn) thành MỘT file HTML vừa xem bằng mắt vừa đọc
  bằng agent: lưới thành phần có bản xem trước thật, trang chi tiết có code mẫu, ontology để map thiết kế mới vào đúng
  thứ đã có, và tab **Layout**: 12 bố cục trang (Bento Grid, Command Palette, Canvas Editor, Mega Menu, Sticky Sidebar,
  Three-Pane Inbox, Kanban Board, Timeline, Zig-Zag, Map + List, Product Page, Chat + Artifact) dựng bằng chính thành phần
  của map, để thấy giao diện này trông thế nào ở mỗi dạng bố cục.
- **Trigger (when to use):** cần "gọi tên" toàn bộ UI của một site/app; cần một tài liệu tự chứa để giao cho agent áp
  giao diện; cần showcase thành phần kiểu Name That UI.
- **Non-goals:** không trích bộ token/DESIGN.md (đó là `extract-site`); không dựng lại cả trang chạy được; không host;
  không tự đoán tên thành phần thay agent — phân loại và mô tả là việc agent làm ở bước 2 và 4.

### Mental model
`URL → capture (CSS + font + ảnh + DOM + vùng ứng viên) → kiểm kê (map vùng vào 91 mục Name That UI, phần còn lại đặt tên
riêng) → snip (outerHTML thật → demos/) → báo cáo parts/*.md → build → <product>-uiux-map.html`. Bộ kiểm kê có sẵn thì vào
thẳng bước build.

### Input và output contract
- **Input:** một URL công khai, hoặc thư mục inventory gồm `demos/*.html` + `parts/*.md` (+ tuỳ chọn `meta.json`,
  `site.css`, `fonts/`, `catalogue.md`, `README.md` với bảng `| **Tên** | số | … | tên thô |`).
- **Output:** `<inventory>/<product>-uiux-map.html` (không bao giờ `index.html`), tự chứa CSS, font, demo, dữ liệu,
  ontology JSON trong `script#ui-ontology`. Mở thẳng bằng `file://`.
- **Định dạng:** `references/report-template.md` (một mục `###` mỗi thành phần), `references/meta.md` (`meta.json`),
  `references/catalogue.md` (91 thành phần: số, slug, tên, một câu nhận diện), `references/layouts.json` (bố cục: lưới CSS
  các ô, từ khoá vai trò mỗi ô, ô đặc trưng; inventory có thể đặt `layouts.json` riêng để ghi đè).
- **Ontology** có thêm `layouts`: mỗi bố cục → ô → id thành phần (hoặc `(wire)` khi map chưa có thành phần hợp).

### Rules và capabilities
- Công cụ (đều trong thư mục skill, gọi bằng `node`):

  | Tệp | Việc |
  |---|---|
  | `scripts/capture.mjs <url> <inv> [--pages 12]` | đi các trang cùng domain, gom CSS → `site.css` + `fonts/`, ảnh + DOM → `capture/`, vùng ứng viên → `candidates.json`, tạo `meta.json` |
  | `scripts/snip.mjs <inv> <picks.json>` | cắt `outerHTML` thật từng thành phần → `demos/<id>.html` (có `before`: click/hover/wait để mở phần ẩn) |
  | `scripts/build-gallery.mjs <inv> [--out thư-mục-hoặc-tệp.html]` | gộp tất cả thành một file; in `HTML:` / `URL:` / `Open:` |
  | `scripts/gallery.css`, `gallery.js`, `pw.mjs` | giao diện (nhúng vào file); `pw.mjs` tự tìm Playwright cục bộ hoặc toàn máy |

- Id demo: `N-slug` cho mục danh mục (N = số trong `catalogue.md`), `x-<slug(tên chuẩn)>` cho thành phần riêng.
- Layout: lúc build mỗi ô lấy thành phần khớp nhất (từ khoá trúng tên ×3, trúng tên trong code/cue ×1, ưu tiên status full,
  không lặp trong một bố cục); không khớp → khung wireframe xám. Thẻ bấm được → `#/layouts/<id>` bản lớn đọc được từng ô.
  Ghép sai vai → sửa `want` trong `layouts.json` rồi build lại.
- Câu đầu của **Mô tả** là dòng "Map khi…" trong ontology: viết như cách người ta *nhận ra* nó (hình dạng, vị trí, hành vi).
- Giao diện file: phong cách Name That UI (nền xám, header nổi, logo chữ, tấm trắng, hero căn giữa với ô tìm kiếm lớn, tab
  gạch chân); header mỗi mục = icon + **tối đa 2 từ**; bản xem trước khung theo vùng nội dung thật, không phóng quá 1:1,
  nền theo `--color-app` của skin; file phải cuộn được (gallery.css mở lại `html/body` mà CSS của app có thể khoá).

### Failure boundaries
- Không có Playwright → `pw.mjs` dừng với lệnh cài (`npm i -g playwright && npx playwright install chromium`).
- Trang cần đăng nhập / chặn bot → `capture.mjs` bỏ trang đó (`skip`); dùng bộ kiểm kê dựng tay thay vì bóc.
- Selector sai trong `picks.json` → `snip.mjs` in `skip <id>`; sửa selector rồi chạy lại.
- Thiếu `site.css` → build vẫn chạy nhưng cảnh báo bản xem trước không có style.
- Mục thiếu mô tả → build in danh sách; chưa giao cho tới khi "without a description: 0".

## HOW

### Main workflow
| Step | Type | Inputs | Action | Outputs/exit | Failure/next |
|---|---|---|---|---|---|
| W01 | effect | URL | `capture.mjs` đi các trang cùng domain | `site.css`, `fonts/`, `capture/`, `candidates.json`, `meta.json` | trang chặn bot → skip; site đăng nhập → B01 |
| W02 | judgment | `candidates.json` + ảnh | Map vùng vào `catalogue.md`, đặt tên phần còn lại | `picks.json` | — |
| W03 | effect | `picks.json` | `snip.mjs` cắt outerHTML thật | `demos/*.html` | `skip <id>` → sửa selector, lặp W03 |
| W04 | judgment | demos | Viết `parts/*.md`, sửa `meta.json` | báo cáo + meta | — |
| W05 | deterministic | inventory | `build-gallery.mjs` | `<product>-uiux-map.html` + ba dòng đường dẫn | thiếu mô tả → về W04 |
| W06 | deterministic | file | Audit `file://` (cuộn, lỗi JS, 390px, thẻ trống) + soát ảnh | file đạt → giao ba dòng `HTML:`/`URL:`/`Open:` | lỗi → sửa, lặp W05 |

Chi tiết từng bước (nguồn chân lý cho W01–W06). Đặt `S=~/.claude/skills/make-agent-uiux-map`.
1. **Thu thập** — `node $S/scripts/capture.mjs https://site.com ./inventory --pages 12`. Xem `capture/*.png`; ghi lại
   thao tác mở phần ẩn (menu, dialog, dropdown) cho bước 3.
2. **Kiểm kê** (agent suy luận) — đọc `candidates.json` + ảnh, cắt màn thành vùng theo vai trò, đối chiếu
   `references/catalogue.md`: khớp → `N-slug`; không khớp → tên chuẩn tiếng Anh ngắn, `x-slug`, xếp vào một nhóm. Mỗi
   thành phần một selector tiêu biểu vào `picks.json`: `[{"id":"2-context-menu","url":"…","selector":"…","before":["click:button.more"]}]`.
3. **Dựng demo** — `node $S/scripts/snip.mjs ./inventory picks.json`; mở `demos/` soát nhanh.
4. **Viết báo cáo** — mỗi demo một mục `###` trong `parts/*.md` theo `references/report-template.md` (bắt buộc: tiêu đề
   đúng, Mô tả, Trạng thái, Tên trong code; nên có: Code mẫu, Biến thể, Tên gọi khác). Sửa `meta.json` (product, wordmark,
   skins nếu trang có theme, frames: 1 demo desktop + 1–2 demo điện thoại).
5. **Đóng gói** — `node $S/scripts/build-gallery.mjs ./inventory` → `./inventory/<product>-uiux-map.html`.
6. **Kiểm tra rồi giao** — KHÔNG dựng localhost. Kiểm bằng `file://` qua Playwright: cuộn được (đo `scrollY`), không lỗi
   JS, 390px không cuộn ngang, mỗi thẻ có bản xem trước, tab Layout không ô nào trống; chụp hero, lưới, một trang chi tiết,
   Ontology, Layout. Rồi in ba dòng
   `HTML:` / `URL:` / `Open:` cho user.

### Branches
- **B01 · Đã có bộ kiểm kê** (ví dụ `docs/ui-inventory` của một repo; bộ kiểm kê từ codebase thì dựng bằng `/ui-inventory`,
  có kiểm chứng path:line) → bỏ bước 1–3; thêm `meta.json` trỏ `css` vào CSS đã biên
  dịch (cho phép một `*`: `"../../dist/assets/styles-*.css"`), `fontsDir`, `skins` theo `data-skin` của app; build.
- **B02 · Trang có theme/skin** → khai `skins` + `defaultSkin` trong `meta.json`; nút Skin hiện và đổi bản xem trước tại chỗ.
- **B03 · Không có skin** → `skins: []`, nút Skin tự ẩn.
- **B04 · Theme đọc thuộc tính khác** (`data-theme`, `class`…) → `skinAttr` + `stageBg` (biến nền của site) trong `meta.json`.

### Validation và stopping
Dừng khi: build in "without a description: 0", audit `file://` đạt (cuộn, 0 lỗi JS, không tràn ngang 390px, không thẻ
trống) và đã soát ảnh. Giao bằng ba dòng đường dẫn; không mở server.

### Examples
- `/make-agent-uiux-map https://uiux.giatbh.io.vn/namethatui/` → 2 trang, `site.css` 153 KB, 11 font, 65 vùng ứng viên →
  5 demo (Header/Navbar, Tabs, Search Field, Segmented Control, Site Footer) → `goi-ten-ui-uiux-map.html` 0,8 MB.
- `/make-agent-uiux-map https://uiux.giatbh.io.vn/` → 8 trang, `site.css` 292 KB (`@import` Google Fonts và font icon
  nhúng sẵn), 15 thành phần (7 danh mục + 8 riêng: Hero Title, KPI Strip, Kit Card…), code CSS thật từ `site.css`, theme
  Sáng/Tối qua `skinAttr: data-theme` + `stageBg` → `uiux-asset-uiux-map.html` 0,4 MB.
- Bộ kiểm kê CTD Bot (203 thành phần, 14 skin): `node $S/scripts/build-gallery.mjs docs/ui-inventory --out docs/ui-gallery`
  → `docs/ui-gallery/ctd-bot-uiux-map.html` 2,9 MB, 195 thành phần có code mẫu.
