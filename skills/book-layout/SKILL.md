---
name: book-layout
description: "Design MẶC ĐỊNH cho mọi tài liệu HTML (owner 30/10): khuôn SÁCH / TẠP CHÍ (trải hai trang có gáy, bìa, mục lục số lớn, đầu chương, trích dẫn, số liệu nổi bật, so sánh cách cũ / cách mới, danh sách icon, sơ đồ vòng, ảnh tràn trang, chữ viết tay gạch vàng) cộng cách viết CASE STUDY (kết luận trước, bối cảnh, câu hỏi, KPI, các chặng, cũ so với mới, bài học, bước tiếp) từ một tệp markdown ngắn bằng script, nên layout tốn 0 token đầu ra. Nền giấy sáng, font Be Vietnam Pro + Patrick Hand đủ dấu tiếng Việt, kiểm Playwright 1280 + 390. Gọi khi user nhờ viết BẤT KỲ tài liệu nào gửi người đọc (tài liệu triển khai, patch, thiết kế, so sánh, báo cáo, proposal), hoặc nói \"viết doc kiểu tạp chí\", \"case study\", \"so với cách cũ\", \"tài liệu dạng sách\", \"layout sách\", \"book layout\", \"magazine layout\", \"sổ tay HTML\", \"html tài liệu đẹp như sách\", hoặc /book-layout. KHÁC `docs-site-macos` (site tài liệu kính mờ kiểu macOS) và `hallmark` (thiết kế UI mới): đây là KHUÔN CỐ ĐỊNH, chỉ đổ chữ."
metadata:
  design-standard: "solid-what-how/1"
  contract-version: "1.0.0"
  loop: utils
---

# Skill: book-layout

Tài liệu HTML trông như một cuốn sách in (layout theo mẫu Dribbble «Book interior layout», owner chọn 30/10). Agent chỉ viết markdown có vài dấu khối; `scripts/book.py` đổ vào khuôn `assets/book.css`. Một sổ tay 8 trang: markdown 2,6 KB thay cho HTML 21 KB viết tay (ít hơn khoảng 8 lần token đầu ra).

## WHAT

### Purpose và context
- **Purpose:** ra MỘT tệp HTML tự chứa (chỉ tải Google Fonts) dạng sách: trải hai trang trên màn rộng, một cột trên điện thoại.
- **Trigger (when to use):**
  - Báo cáo, sổ tay, hướng dẫn, proposal cần đọc như tạp chí, gửi người xem trên điện thoại.
  - User nói "viết doc kiểu tạp chí", "tài liệu dạng sách", "book layout", "/book-layout".
- **Non-goals:** KHÔNG thiết kế lại khuôn mỗi lần (muốn kiểu khác → `hallmark`); KHÔNG dark mode (luật owner: tài liệu nền sáng); KHÔNG trang tài liệu nhiều tệp có điều hướng (→ `docs-site-macos`).

### Mental model
`markdown (front matter + «=== kiểu» mỗi trang) → book.py parse từng dòng theo dấu đầu dòng → HTML từng trang → ghép hai trang một trải → nhúng book.css → một tệp .html → check.mjs đo 1280 + 390`

### Input và output contract
| | Field | Required? | Ý nghĩa |
|---|---|---|---|
| In | tệp `.md` theo cú pháp dưới | có | nội dung; mẫu đủ mọi khối: `assets/example.md` |
| In | ảnh (`![mô tả](đường-dẫn)`) | không | thiếu thì bìa và trang ảnh tràn dùng minh hoạ SVG có sẵn |
| Out | `<tên>.html` | có | một tệp, CSS nhúng sẵn |
| Out | `<tên>-1280.png`, `<tên>-390.png` + dòng `ok` | có | bằng chứng từ `scripts/check.mjs` |

### Cú pháp markdown
Mỗi dòng `=== <kiểu>` mở một trang (`cover`, `toc`, `page`, `cycle`, `image`); hai trang liền nhau thành một trải. Front matter: `title`, `brand`, `date`, `vol`, `footer`.

| Dòng bắt đầu bằng | Ra |
|---|---|
| `^ chữ` | kicker in hoa nhỏ |
| `# Dòng một / *dòng hai*` | tiêu đề lớn, ` / ` xuống dòng, `*…*` màu xanh nhấn |
| `### chữ` | tiêu đề nhỏ (tiêu đề khung việc / danh sách icon kế dưới) |
| `> chữ` | câu dẫn |
| `---` | gạch vàng ngắn |
| `" câu -- nguồn` | trích dẫn lớn |
| `! 325 \| chữ \| nguồn` | khối số liệu nổi bật |
| `- chữ` | danh sách tích xanh trong khung |
| `1. chữ ; ghi chú` | các bước đánh số trong khung |
| `* Tiêu đề :: mô tả` | danh sách icon (trang `cycle`: ba nút của vòng) |
| `01 \| Tiêu đề \| mô tả \| 06` | dòng mục lục (trang `toc`) |
| `~ chữ / *gạch vàng*` | chữ viết tay góc dưới phải |
| `![mô tả](ảnh)` | ảnh (trang `image`: tràn trang, chữ đè) |
| `![mô tả](x.gif "x.png")` | GIF trong cùng khung ảnh, kèm ảnh tĩnh cho người tắt chuyển động |
| `+ 30,40 chữ` | ghim chú thích số 1, 2… trên ảnh/GIF ngay trên (x, y theo %), chữ thành danh sách đánh số dưới khung |
| `@ chữ` | tiêu đề chạy góc phải (vd «Chương 2») |
| `<> Chỉ số \| cũ \| mới \| nguồn` | một dòng so sánh cách cũ / cách mới (dòng liền nhau thành một khối, `### …` ngay trên làm tiêu đề); cũ gạch mờ, mới xanh đậm; màn hẹp thành thẻ có nhãn trong ô, không bảng |
| `<>! Chỉ số \| cũ \| mới \| nguồn` | dòng mà cách mới KHÔNG hơn: không tô xanh, không gạch cách cũ (đừng giấu chỗ kém) |
| `<> \| Nhãn cũ \| Nhãn mới` | đổi nhãn hai cột (mặc định «Cách cũ» / «Cách mới») |
| dòng khác | đoạn văn, `**đậm**` được |

### Rules và capabilities
- RULE-01 (MUST): KHÔNG viết HTML/CSS tay cho tài liệu này: viết `.md` rồi chạy `book.py`. Cần khối mới → thêm vào `book.py` + `book.css` + selftest, không chèn HTML vào markdown (book.py escape mọi HTML).
- RULE-02 (MUST): chạy `node scripts/check.mjs <tệp>.html` và chỉ báo xong khi cả hai dòng là `ok` (0 cuộn ngang, 0 chữ tràn, tiêu đề không cắt dấu, lề trái đều, sơ đồ vòng `cyc` đều: tâm nút cách tâm vòng như nhau ± 1 px, góc 360/n ± 1°, nhãn cách nút như nhau, mũi tên nằm trên vòng giữa hai nút, `hit` 0 = nhãn không đè mũi tên/nút).
- RULE-03 (MUST): giữ nền sáng và hai font có dấu tiếng Việt; tiêu đề `line-height` ≥ 1.2.
- RULE-05 (MUST): tài liệu giải thích một thay đổi / quyết định / so sánh viết theo `references/case-study.md`: bìa là MỘT câu kết luận có số, có câu hỏi «Làm sao để …», mỗi chặng một sản phẩm có nguồn, trang «cũ so với mới» bằng khối `<>` (chỗ cách mới không hơn dùng `<>!`). Khung trống: `assets/case-study.md`.
- RULE-04 (SHOULD): mỗi trang một ý, ≤ 120 chữ đoạn văn; chữ dài hơn → tách thêm `=== page`.
- Capabilities: đọc/ghi tệp trong dự án; chạy python3 và node (Playwright cài global).

### Failure boundaries
- Dòng `=== <kiểu>` lạ hoặc chữ đứng trước trang đầu → `book.py` dừng, báo lỗi rõ → sửa markdown.
- Không có mạng tới Google Fonts → `check.mjs` ghi «font chưa tải» → chữ lùi về font hệ thống; vẫn đọc được nhưng không đúng mẫu.
- Playwright chưa cài → `check.mjs` lỗi import → **blocked**: `npm i -g playwright` (hoặc đặt `PW_ROOT`). Playwright không có Chromium cho máy (vd macOS 13: «does not support chromium… on mac13») → `PW_CHANNEL=chrome node scripts/check.mjs …` dùng Google Chrome đã cài.
- `check.mjs` báo HỎNG → sửa nội dung (chữ quá dài trong một ô) hoặc khuôn, chạy lại; 2 vòng vẫn hỏng → báo user kèm số đo.

## HOW

### Main workflow
| Step | Type | Inputs | Action | Outputs/exit | Failure/next |
|---|---|---|---|---|---|
| W01 | judgment | yêu cầu user | Chia nội dung thành trang: bìa, mục lục (nếu ≥ 4 chương), mỗi chương 1–2 trang, ảnh tràn làm nhịp nghỉ. Tài liệu về một thay đổi / so sánh: theo thứ tự trang của `references/case-study.md` | dàn trang | — |
| W02 | effect | dàn trang | Viết `<tên>.md` theo cú pháp (chép khung từ `assets/example.md`) | tệp .md | — |
| W03 | deterministic | .md | `python3 scripts/book.py <tên>.md -o <tên>.html` | tệp .html | lỗi cú pháp → sửa W02 |
| W04 | deterministic | .html | `node scripts/check.mjs <tên>.html` | 2 dòng ok + 2 ảnh | HỎNG → B01 |
| W05 | effect | .html + ảnh | Gửi user tệp HTML + ảnh 1280 | xong | — |

### Branches
| ID | Kind | Guard | Hành vi | Skip / failure | Rejoin |
|---|---|---|---|---|---|
| B01 | recovery | check.mjs HỎNG | đọc số đo: `over` → rút chữ trong ô, `uneven` → bỏ khối lạ đầu trang, `sw` → ảnh/bảng quá rộng | 2 vòng vẫn hỏng → báo user | W04 |
| B02 | conditional | user có ảnh thật | thêm `![mô tả](ảnh)` vào `cover` / `image` / `page` | không có → giữ SVG mặc định | W03 |

### Khi nào dùng GIF (pattern ưu tiên, không máy móc)
Owner 30/10: «ưu tiên luôn GIF với annotation». Khung ảnh trong trang (`page`) mặc định là **GIF có ghim chú thích**; ảnh tĩnh chỉ khi GIF không hợp.
- **GIF + chú thích (mặc định)**: thao tác, diễn biến, trước rồi sau, luồng 2–4 bước, bằng chứng UI. Mỗi GIF một ý, 3–8 giây, lặp, dưới 2 MB. Ghim `+ x,y chữ` đánh số đúng chỗ người cần nhìn (nút bấm, toast, số đổi); 1–4 ghim, chữ ngắn nói ĐIỀU XẢY RA («Bấm Save», «Toast Đã lưu hiện»).
- **Ảnh tĩnh** khi chuyển động không thêm thông tin: bìa, trang `image` tràn có chữ đè, ảnh không khí, sơ đồ. Ảnh tĩnh vẫn ghim được.
- Không có GIF thật thì đừng bịa: dùng ảnh tĩnh hoặc minh hoạ SVG sẵn có. GIF quay bằng Playwright (vd `tests/lib/record_gif.mjs` của Hang) dùng thẳng được.
- Khoảng 1 GIF mỗi trải hai trang; hai GIF cạnh nhau tranh nhau sự chú ý.
- Luôn kèm poster tĩnh: `![mô tả](thao-tac.gif "thao-tac.png")`; người bật «giảm chuyển động» thấy ảnh tĩnh. `mô tả` ghi điều GIF cho thấy, không ghi «ảnh động».

Mẫu:
```
![Gõ «vẽ sơ đồ», archify hiện ở dòng gợi ý](flow.gif "flow.png")
+ 30,28 Gõ một ý vào ô tìm
+ 60,62 Skill gần nghĩa có chip «gợi ý»
```

### Validation và stopping
Xong khi `check.mjs` in hai dòng `ok` (1280 và 390) và user có tệp HTML. Selftest của script: `python3 scripts/book.py --selftest`.

### Examples
- **Positive:** "làm sổ tay onboarding 6 trang kiểu tạp chí" → viết .md 6 trang (cover, toc, 3 page, image) → book.py → check.mjs ok ở 1280 và 390 → gửi HTML.
- **Boundary/failure:** user muốn "tài liệu dark mode kiểu tạp chí" → nói rõ khuôn chỉ nền sáng (luật owner), đề xuất `hallmark` nếu cần kiểu khác.

### Reference — Assets
- `assets/book.css`: khuôn (biến màu ở `:root`: `--green`, `--sun`, `--sage`, `--paper`). Đổi màu thương hiệu: sửa biến, không sửa từng khối.
- `assets/example.md`: mẫu đủ mọi kiểu trang và mọi khối.
- `assets/case-study.md`: khung trống của tài liệu case-study (8 trang).
- `references/case-study.md`: thứ tự trang, nhịp viết, cách đặt hình, checklist (rút từ bài uxdesign.cc owner chọn).
- `examples/driver-chung.md`: tài liệu thật theo khuôn case-study (driver chung của Hang, số đo xen kẽ cũ / mới).
- `scripts/book.py`: markdown → HTML, stdlib, Python 3.9.
- `scripts/check.mjs`: đo 1280 + 390, chụp ảnh.

## Origin
- Owner 30/10 (phòng Vịnh Hồng, Hang): «đóng thành skill, sau này mọi thể loại tài liệu viết ra theo design này» sau khi gửi bài uxdesign.cc «Designing a system for book reviews, a UX case study»; trả lời thẻ hỏi: design = cả hai, book-layout làm khuôn hình + cách viết case-study. Kèm «compare so với cách cũ, lưu vào tài liệu patch triển khai để có chứng cứ phải đổi» → khối `<>` / `<>!`. Đo trên tài liệu driver chung: trang cũ cần 11,4 KB mã dựng viết tay riêng (`build_page.py`, font Iowan Old Style chỉ có trên máy Apple), trang mới 4,3 KB markdown dùng chung khuôn, cả hai 0 tràn ở 1280 và 390.
- Owner 30/10 (phòng Vịnh Hồng, Hang): GIF có chú thích là loại khung ưu tiên. Yêu cầu gốc: «xem trang web và ảnh này dribbble.com/shots/27684270-Book-interior-layout-magazine-layout-design thiết kế html theo layout này ra skill». Trang mẫu viết tay được duyệt («trông ok»), kèm ý «tốn nhiều token out» → đóng gói thành khuôn + script để agent chỉ viết markdown.
