---
name: rp
description: "Hub báo cáo (report) tình trạng Hang thành trang HTML đọc được trên điện thoại. Chế độ task: /rp task = báo cáo tình trạng các task (thread Issue/Epic đang mở, ai làm, giai đoạn, nhánh, sha Live, việc chờ owner), viết bằng book-layout. Gọi khi owner nói rp, báo cáo tình trạng task, tình hình các task, task đang tới đâu, hoặc /rp."
metadata:
  design-standard: "solid-what-how/1"
  contract-version: "1.0.0"
  loop: utils
---

# Skill: rp

Hub MỘT TÊN cho các báo cáo của Hang (owner 31/10: «báo cáo tình trạng các task đi», «lệnh là /rp»). Mỗi báo cáo là một chế độ ở `references/<chế độ>.md`. Hiện chỉ có chế độ `task`; thêm chế độ (vd tình trạng agent, tình trạng Live) = thêm tệp, không đổi hub này.

## WHAT

### Purpose và context
- **Purpose:** trả lời «các task đang tới đâu» bằng một trang HTML đọc được trên điện thoại, số liệu đọc thẳng từ Hang, mỗi dòng có id để kiểm lại.
- **Trigger (when to use):** owner gõ `/rp task`, hoặc nói «báo cáo tình trạng task», «tình hình các task», «task đang tới đâu». Không có chế độ đi kèm (`/rp` trơn) thì làm `task`.
- **Non-goals:** KHÔNG ghi gì lên Hang ngoài tin báo cáo; KHÔNG sửa, đóng hay giao lại thread; KHÔNG publish lên claude.ai Artifact (owner không mở được); KHÔNG tự đo smoke hay chạy test.

### Mental model
`hang_open_work (GET /work/open?room=vinh-hong, chỉ đọc) → task_report.py gom nhóm, mỗi việc một thẻ ngắn, song ngữ EN (STE cơ học) / VI → markdown → book-layout (book.py) → finish(): nút EN/VI → check.mjs + check_lang.mjs → HTML → gửi đính kèm`

### Input và output contract
| | Field | Required? | Ý nghĩa |
|---|---|---|---|
| In | máy đã nối Hang | có | `~/.hang/url` + `~/.hang/token` (script chỉ gửi token tới chính Hang đó, không in ra) |
| In | chế độ | không | `task` (mặc định) |
| Out | `rp-task-<ngày>-<giờ>.md` + `.html` | có | bìa, chú giải màu, tóm tắt, từng nhóm màu (đỏ, vàng, xanh dương, xám, xanh lá), trang «chưa đo» |
| Out | hai dòng `ok` của `check.mjs` + không dòng FAIL của `check_lang.mjs` | có | bằng chứng 1280 + 390, EN và VI: không tràn, đủ dấu, đủ RULE-06..RULE-12 |

### Rules và capabilities
- RULE-01 (MUST): chỉ ĐỌC Hang. Tin báo cáo là thứ duy nhất được ghi (gửi owner kèm tệp `.html`).
- RULE-02 (MUST): mỗi dòng của báo cáo mang id kiểm được (room, nhánh, sha, id yêu cầu mở lại); thứ không đo được ghi «chưa đo», không đoán, không điền.
- RULE-03 (MUST): màu của mỗi việc tính từ dữ liệu và xanh lá CHỈ khi việc thật sự xong (`deployed` true, đã lên Live). Đỏ = cần xử lý (agent chết, bị chặn, im > 12 giờ); vàng = chậm hoặc chờ (chờ owner, chờ review, đợi việc khác, im > 2 giờ); xanh dương = đang làm bình thường; xám = chưa bắt đầu. KHÔNG dùng danh sách «- » của book-layout cho dòng việc: nó vẽ dấu tích xanh trước mọi dòng và owner đọc tích là «xong» (31/10).
- RULE-04 (MUST): trang dựng bằng skill `book-layout` (nền sáng, không bảng markdown, danh sách), không viết HTML tay; owner đọc trên điện thoại.
- RULE-05 (MUST): không in token, không đưa token vào báo cáo hay tin gửi.
- RULE-06 (MUST, owner m1a19291cd4a58d3 + m1a192aae03f1e9c «10-20 thôi, 25 vẫn dài»): mỗi dòng văn ≤ 20 chữ ở CẢ EN và VI (VI đếm theo khoảng trắng). «≥ 10 chữ» là mục tiêu cho câu văn, KHÔNG áp cho dòng nhãn–giá trị ngắn (Branch, Thread) vì RULE-07 thắng. Kiểm: `--selftest` (kể cả thẻ dài nhất).
- RULE-07 (MUST, owner m1a192af76ee1bb0 «mỗi ý một dòng, có khoảng cách»): mỗi việc là MỘT thẻ: dòng tiêu đề (chấm màu + tên) rồi mỗi ý một dòng riêng (Status, Workers, Quiet for, Branch, Thread). Không gộp ý bằng «;» hay «·». Kiểm: `--selftest` (thẻ 3–5 dòng, chặn gộp).
- RULE-08 (MUST, owner m1a19305e82029d5 «Status và Workers đã in bold đâu?»): nhãn đầu dòng trước «:» in đậm 600, chữ sau «:» giữ Light; đây là NGOẠI LỆ DUY NHẤT của RULE-10. Kiểm: `check_lang.mjs` (mọi dòng thẻ mở đầu bằng nhãn đậm).
- RULE-09 (MUST, owner 1/11: m1a192ced35a0c67 «hình quyển tập đâu?», m1a192e97d6f36b4 «bị chuột cắn», m1a19319b1e5380f «cắt cụt ngắn», Klau m1a1931ae86c7507 «để space cũng được, không cần cố nhét»): khổ > 820 px là quyển tập các cặp hai tờ (khe 40 px và bóng từng cặp của `book-layout`, KHÔNG gộp thành một quyển liền) và MỌI tờ cao BẰNG NHAU ±2 px theo khổ chuẩn là tờ bìa (một đoạn JS chỉnh `min-height` của mọi tờ theo tờ cao nhất, tính lại khi đổi EN/VI, đổi khổ, nạp font). Tờ ít nội dung để trống phía dưới, KHÔNG nhồi thẻ; một thẻ mỗi tờ. Khe giữa hai khối kề nhau trong tờ ≤ 80 px (trừ bìa). BỎ luật «trống cuối ≤ 120 px». Khổ ≤ 820 px một cột. Kiểm: `check_lang.mjs` (các tờ lệch > 2 px là FAIL).
- RULE-10 (MUST, owner m1a192fa92c41dfb): chữ Lexend Deca Light + mỏng, tự phục vụ (nhúng base64, 0 request ngoài). Thân, h3, nút 300; tiêu đề và số lớn ≥ 200; 100 chỉ khi ≥ 48 px và khổ ≥ 1100 px; không chữ nào ≥ 400 trừ RULE-08; chữ ≤ 200 màu #111; tương phản ≥ 4,5:1 (< 24 px) hoặc ≥ 3:1. Không áp hero đỏ của lexend.com. Kiểm: `check_lang.mjs` + `--selftest`.
- RULE-11 (MUST, owner m1a19308ad5a5402 «Red, Yellow tô màu tương ứng»): tên màu (Red/Yellow/Blue/Gray/Green, Đỏ/Vàng/Xanh dương/Xám/Xanh lá) ở tiêu đề trang, chú giải, dòng tóm tắt và hình bìa tô đúng màu tương ứng (bảng `TXT`, đủ tương phản trên giấy). Kiểm: `--selftest` + `check_lang.mjs`.
- RULE-12 (MUST, owner m1a192938f513344): báo cáo mở bằng tiếng Anh viết theo ASD-STE100 (kiểm CƠ HỌC, không phải chứng nhận) và có nút «VI» đổi cả trang sang tiếng Việt, không qua token Claude, không gọi mạng; tên việc giữ nguyên, nút «Translate task names» chỉ khi trình duyệt có Translator API và người xem bấm. Mọi câu do mã sinh nằm ở bảng `TX` (EN, VI). Kiểm: `--selftest` + `check_lang.mjs`.
- RULE-13 (MUST, owner 31/10): không danh sách «- » (dấu tích xanh đọc là «xong»), không chữ nhấn «*…*» (book-layout tô xanh lá) ngoài nhãn đậm RULE-08; xanh lá CHỈ khi việc đã lên Live. Kiểm: `--selftest`.
- RULE-14 (MUST, owner 31/10 + 1/11): trước khi gửi owner phải TỰ chụp 390 và 1280 (EN và VI), TỰ XEM, và gửi ảnh trước/sau kèm tệp; không nới luật kiểm khi FAIL, chỉnh bố cục.
- RULE-15 (MUST, owner 1/11 «mấy mã kiểu này … đóng vào chip và highlight lên»; m1a1932efb1c24bd «chip ở trong này đẹp thế cơ mà» chỉ mẫu https://uiux.giatbh.io.vn/components/chip.html; m1a19338db452775 «lỡ xuống dòng thì chip vẫn bọc kiểu wrapping»; m1a19339fed71243 «hạn chế màu xám, dùng bộ màu pastel»): mọi MÃ MÁY trong báo cáo hiển thị thành chip KIỂU TRANG MẪU ĐÓ (Hình 1 «Vỏ chip», `.cx.fill`, đo bằng Playwright): viên thuốc bo tròn, nền pastel PHÂN NHÓM, viền 1 px đậm hơn nền, chữ tối #1a1d21. KHÔNG XÁM và KHÔNG TÍM (owner m1a1932949ed7b2d chê tím «lạc quẻ», Klau m1a1933d34ca6dd5): sha = Pink #f7c1d9; `room:…`, `hang_open_work` và tên nhánh = Teal #b2ece2; mã mở lại phiên (s…) = Peach #fae3c8. Luật kiểm chặn tông tím (hue 225–320°). Loại mã do bản dựng khai (`data-what`), KHÔNG đoán từ chữ (nhánh toàn chữ hex như «deadbee» vẫn là nhánh). Cấm màu tình trạng và tông đỏ (hue ≥ 335° hoặc ≤ 12°) / xanh lá (75–150°): đỏ = cần xử lý, xanh lá = xong (Kanade). Chữ chip Lexend Deca 300 như chữ thường (RULE-10). Chip xuống dòng phải ÔM SÁT CHỮ từng dòng như highlight (`display:inline` + `box-decoration-break:clone`), KHÔNG thành khối chữ nhật thừa chỗ; slug dài ngắt ở dấu «-». «none», «chưa có» không phải mã, không chip. Kiểm: `--selftest` + `check_lang.mjs` (mã ngoài chip là FAIL; chip phải đúng nhóm theo `data-what`, đúng nền, viền 1 px đậm hơn nền, bo tròn, chữ #1a1d21 ≤ 300, tương phản ≥ 7:1, nổi hơn nền THẬT phía sau ≥ 1,06:1, inline + clone, mỗi mảnh dòng chỉ rộng hơn chữ đúng đệm + viền, không tràn).
- RULE-16 (MUST, owner m1a193435b762da4 «cái dot tròn vẫn vậy, bỏ luôn đi; tôi tưởng bạn làm được dot pastel màu đặc», Klau m1a19343a8962014): KHÔNG dùng emoji chấm màu (🔴🟡🔵⚪🟢: bóng loáng, lệch hàng). Chấm trạng thái là hình tròn CSS màu ĐẶC pastel, phẳng (không bóng, không viền, không gradient), cùng hue với màu tình trạng: đỏ #e98c83, vàng #efc95c, xanh dương #86b3e6, xám #b7bbc1, xanh lá #8dce96; tương phản ≥ 1,5:1 với nền (có chữ màu đi kèm nên chấm không là chỗ duy nhất mang nghĩa); THẲNG HÀNG với chữ (tâm chấm lệch tâm chữ ≤ 3 px). Marker md `⟐màu⟐` → `<span class="dot dot-màu" aria-hidden>`. Kiểm: `--selftest` + `check_lang.mjs` (còn ký tự chấm màu là FAIL; chấm phải đúng màu, phẳng, tròn, thẳng hàng).
- Capabilities: chạy python3 và node; đọc `~/.hang`; gửi tin kèm tệp bằng `hang-room-hook send`.

### Failure boundaries
- Không đọc được Hang (`~/.hang/url`/`token` thiếu, mạng, 401/403) → **blocked**: nói đúng lỗi, không dựng báo cáo từ trí nhớ.
- Không có skill `book-layout` → **blocked**: cập nhật skills hoặc chạy từ checkout repo skills; không viết HTML thay.
- `check.mjs` HỎNG → sửa theo bảng nhánh của `book-layout` (tối đa 2 vòng), vẫn hỏng thì gửi kèm số đo và nói rõ.
- Phòng không có trên Hang (`--room` sai tên) → **blocked**: báo tên sai, không dựng báo cáo «0 việc».
- Hang trả ít hơn kỳ vọng (phòng có mà không thread nào mở) → báo cáo vẫn hợp lệ: «0 việc mở».

## HOW

### Main workflow
| Step | Type | Inputs | Action | Outputs/exit | Failure/next |
|---|---|---|---|---|---|
| W01 | deterministic | chế độ | chọn `references/<chế độ>.md` (mặc định `task`) rồi làm đúng các bước trong đó | — | chế độ lạ → liệt kê chế độ có |
| W02 | deterministic | Hang | `python3 scripts/task_report.py [--room vinh-hong] --out <thư mục> --build` | `.md` + `.html` | đọc lỗi → blocked |
| W03 | judgment | `.md` | đọc lướt: dòng nào mâu thuẫn dữ liệu thì sửa nguồn/ghi chú, không thêm số không có nguồn | `.md` đã soát | — |
| W04 | deterministic | `.html` | `node <book-layout>/scripts/check.mjs <tệp>.html` (macOS 13: `PW_CHANNEL=chrome`) | hai dòng `ok` | HỎNG → sửa 1 lần, lặp tối đa 2 |
| W04a | deterministic | `.html` | `PW_CHANNEL=chrome node scripts/check_lang.mjs <tệp>.html <thư mục ảnh>` | mọi dòng `ok`: bấm VI/EN đổi cả trang, không request ngoài, localStorage hỏng vẫn chạy, Translator chỉ khi bấm, không khoảng trống thừa (khe ≤ 80 px, trống đáy ≤ 120 px), luật chữ Lexend Deca (độ đậm ≤ 300, tương phản, 0 request ngoài) | FAIL → sửa `task_report.py`, tối đa 2 vòng |
| W04b | judgment | `<tệp>-390.png`, `<tệp>-1280.png` (check.mjs đã chụp) | XEM ảnh bằng mắt (đọc ảnh, không chỉ tin hai dòng `ok`) và phán thẳng 5 điểm: bìa không có tranh hay màu gợi «xong» sai (không xanh lá, không pastel nhạt); chấm màu đủ rõ; chú giải đúng màu; không chữ nhỏ hay chồng nhau ở 390; số trên bìa khớp trang tóm tắt | ảnh đã duyệt | sai điểm nào → sửa `task_report.py`, dựng lại, chụp lại (tối đa 2 vòng), nói rõ điểm sai nếu vẫn hỏng |
| W05 | effect | `.html` + ảnh 390 | gửi owner kèm tệp (và ảnh 390 màn đầu): `sh ~/.hang/bin/hang-room-hook send owner "<2 dòng tóm tắt>" --file <tệp>.html --from $HANG_SESSION --agent claude-code --req <id tin owner> --reply <id tin owner>` | tin có link tệp | — |

### Branches
Không có nhánh phụ. Chế độ mới thêm bằng `references/<chế độ>.md` (cùng dạng bảng bước), không thêm nhánh ở hub.

### Validation và stopping
Xong khi: `task_report.py --selftest` in `ok`, `check.mjs` in hai dòng `ok` (chạy cả bản EN và bản VI), `check_lang.mjs` không dòng FAIL, đã XEM ảnh 390 và 1280 (W04b) và thấy hợp lý, và owner nhận được tệp `.html`. Mỗi báo cáo ghi giờ chốt ở bìa; chạy lại để cập nhật, không sửa tay số liệu.

### Examples
- **Positive:** owner gõ «/rp task» → script đọc 9 thread mở, ra báo cáo 7 trang → check.mjs ok 1280 + 390 → gửi tệp kèm hai dòng tóm tắt (số việc, việc cần chú ý số một).
- **Boundary/failure:** máy chưa nối Hang (không có `~/.hang/token`) → blocked, nói «chưa nối Hang trên máy này», không dựng báo cáo.

### Reference
- `references/task.md`: chế độ `task` (nguồn số liệu, cách gom nhóm, cách đọc «cần chú ý», giới hạn).
- `scripts/task_report.py`: đọc `GET /work/open` → markdown song ngữ cho `book-layout` + `finish()` thêm nút EN/VI; `--selftest`.
- `scripts/check_lang.mjs`: Playwright kiểm nút ngôn ngữ, không request ngoài, localStorage hỏng, Translator giả.
