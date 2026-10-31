# /rp task — báo cáo tình trạng các task

Chế độ đầu tiên của hub `rp`. Owner (31/10, Issue 452): «báo cáo tình trạng các task đi», «làm thành 1 skill báo cáo dùng skill tạo report hôm qua» (= `book-layout`, Issue 428).

## Nguồn số liệu (chỉ đọc)
- `GET /work/open?room=<phòng>` của chính Hang (cùng dữ liệu MCP `hang_open_work`; mặc định `vinh-hong`, đổi bằng `--room`; không kèm `room` thì Hang gộp mọi phòng gốc token máy thấy nên báo cáo phải luôn truyền), Bearer token máy ở `~/.hang/token`. Mỗi thread mở có: `room`, `name`, `kind` (issue/epic), `status`, `workers[]` (tên, giai đoạn, `health`), `down[]` (agent đã chết, mã mở lại), `blocking[]`, `branch`, `deployed`, `owner_wait`, `idle`, `req[]`.
- `running` = sha đang chạy trên Live.
- Phòng sai tên: script hỏi `GET /rooms/<phòng>` trước (Hang trả `room: null`) và dừng với «blocked», vì `/work/open?room=<tên sai>` trả 0 việc mà không báo lỗi.
- `--src <tệp>.json` (đọc tệp thay cho mạng): báo cáo không ghi tên phòng và không khẳng định «ngoài phòng X không có».
- Script gửi header `User-Agent: hang-rp/1`: cổng công khai từ chối UA mặc định của Python (403).

## Màu (owner 31/10: «tick xanh là tui hiểu xong hết rồi hả»)
Màu tính từ dữ liệu của chính thread (`judge()` trong `task_report.py`); xanh lá cần bằng chứng «xong», không có bằng chứng thì không bao giờ xanh lá.
1. Đỏ, cần xử lý: có agent đã chết (`down[]`), hoặc giai đoạn blocked/failed, hoặc đang làm mà im quá 12 giờ.
2. Vàng, chậm hoặc chờ: chờ owner (`owner_wait`), chờ review, đợi việc khác (`blocking[]`), đang làm mà im quá 2 giờ.
3. Xanh dương: đang làm bình thường, chưa xong.
4. Xám: backlog hoặc xếp hàng, chưa bắt đầu.
5. Xanh lá: XONG, cờ `deployed` true (đã lên Live) và không có agent chết.
Thứ tự ưu tiên: xanh lá, đỏ, vàng, xám/xanh dương. Dòng có nhiều lý do liệt kê hết.

## Báo cáo gồm
1. Bìa: số việc mở, số đã xong, giờ chốt, hình thanh số việc theo màu.
2. Tóm tắt: số việc theo màu, sha Live, kèm CHÚ GIẢI màu ngay dưới (cùng trang, để người đọc biết xanh lá mới là xong).
3. Từng nhóm màu, 1 thẻ mỗi trang. MỖI VIỆC LÀ MỘT THẺ: dòng tiêu đề (chấm màu + tên việc) rồi MỖI Ý MỘT DÒNG có khoảng cách rõ (owner 31/10: «mỗi ý một dòng, có khoảng cách, đọc lần lượt từ trên xuống»): Tình trạng, Người làm, Im bao lâu, Nhánh, Thread. Thanh ngắn ngăn hai thẻ. Không nối ý bằng «;» trong một khối chữ liền.
4. Chưa đo: smoke Live, sha từng nhánh, thứ ngoài phạm vi.

## Cách đọc cho đúng
- `deployed` false = chưa lên Live; `status` review = chờ review (vàng, không phải xong). Không viết «xong» khi dữ liệu không nói.
- «Im» là thời gian từ tin cuối trong thread (`idle`), không phải thời gian agent không làm gì.
- `down` có mã mở lại thì việc mở lại do Điều phối làm; báo cáo chỉ nêu.
- Thread backlog không có người làm là bình thường, không phải lỗi.

## Trước khi đăng: chụp và XEM (owner 31/10: «tự chụp hình preview lại xem nó hợp lý chưa hay lại lạc quẻ pastel»)
Hai dòng `ok` của `check.mjs` chỉ nói không tràn chữ; không nói màu có hợp hay không. Sau khi dựng báo cáo phải mở `<tệp>-390.png` và `<tệp>-1280.png` (check.mjs đã chụp) rồi nhìn: bìa, chấm màu, chú giải, chữ nhỏ hay chồng nhau, số trên bìa khớp tóm tắt. Không đăng khi bìa gợi «xong» (tranh xanh lá, màu pastel nhạt) hay chấm màu khó đọc.
Bìa dùng hình thanh số việc theo màu do chính script sinh (`cover_svg`, nhúng sẵn trong tệp), không dùng tranh núi xanh lá mặc định của `book-layout`; thanh đậm, phẳng, 0 việc thì chỉ còn khung rỗng.

## Hai thứ ngôn ngữ (owner 31/10, Issue /rp: «báo cáo viết tiếng Anh chuẩn hàng không… sẵn 1 nút dịch Việt, không qua token Claude»)
- Báo cáo mở ra bằng tiếng Anh viết theo mẫu ASD-STE100; nút «VI» (góc trên) đổi cả trang sang tiếng Việt, «EN» đổi lại. Đổi bằng CSS, không gọi mạng, không tốn token. Lựa chọn nhớ bằng `localStorage` bọc try/catch (hỏng thì mặc định EN).
- NGUỒN DUY NHẤT của mọi câu do mã sinh là bảng `TX` trong `task_report.py`: khoá → (EN, VI). Selftest đỏ nếu thiếu bản VI hoặc EN và VI dùng chỗ điền khác nhau. Trong md mỗi câu là «⟦EN¦VI⟧»; `finish()` đổi thành hai `<span>` sau `book.py`.
- Tên việc do người đặt bằng tiếng Việt nên giữ nguyên gốc ở cả hai bản. Chuỗi `blocking` và `health` do SERVER sinh nên dịch bằng bảng `TX` (khoá `b_*`, `h_*`): ba mẫu server đã biết (wave sau, thread cha, còn việc khác chờ) có câu EN riêng, mẫu lạ ra câu chung «Another task depends on this task»; selftest chặn chữ Việt lọt vào bản EN ngoài dòng tiêu đề thẻ. Mã `health` không in trong ngoặc nữa («is dead», không «is dead (dead)»). Server đổi câu `blocking` thì thêm mẫu vào `block_text()`. Nút «Translate task names» CHỈ hiện khi `'Translator' in self` (Translator API của Chrome, dịch trên máy), chỉ dịch khi người xem BẤM, hiện «Đang tải bộ dịch trên máy…» lúc tải model, bấm lần nữa trả về tên gốc. Không có API: nút ẩn, không rơi về dịch vụ ngoài. Không dùng widget Google Translate (gửi chữ ra ngoài, nạp script ngoài).
- STE kiểm CƠ HỌC bằng `ste_problems()`, KHÔNG phải chứng nhận ASD-STE100 (từ điển ~900 từ duyệt có bản quyền, không nhúng): câu ≤ 20 chữ, ≤ 1 dấu phẩy, không «;», không viết tắt «'s/n't», không bị động «is/are/was + -ed», không mở câu bằng «-ing», viết tắt chỉ trong `STE_ABBR`, vài từ cấm (should, may, might, shall, get, make). Chạy trên mọi câu EN của bảng `TX`.
- Đếm chữ: tách theo khoảng trắng, nên tiếng Việt đếm mỗi âm tiết một chữ. Mỗi dòng văn ≤ 20 chữ (`CAP`; owner 31/10 hạ từ 25: «10-20 thôi, 25 vẫn dài») ở CẢ hai ngôn ngữ (selftest, kể cả thẻ dài nhất có 5 người làm, nhiều lý do, tên nhánh dài). Mỗi ý một dòng riêng (không gộp để cho đủ 10 chữ: ý ngắn như «Nhánh: x» vẫn một dòng); selftest chặn dòng quá 20 chữ và chặn gộp Workers/Branch/Thread vào một dòng; thẻ 3–5 dòng. Trần 20 chữ mỗi dòng; số đo thực ghi trong tin XONG khi đăng.
- ADR. Bối cảnh: owner chê khối chữ liền và muốn EN chuẩn hàng không + nút dịch không tốn token. Quyết định: song ngữ dựng sẵn bằng mã, nút đổi bằng CSS; tên việc dịch tuỳ chọn bằng Translator API trên máy. Đã loại: Google Translate widget (gửi chữ ra Google, script ngoài), thư viện dịch WASM (vài chục MB, vi→en kém), dịch bằng Claude (tốn token). Hệ quả: tên việc vẫn tiếng Việt ở bản EN nếu trình duyệt không có Translator API. Evidence: `--selftest`, `scripts/check_lang.mjs`, ảnh 390/1280 EN + VI.
- Web font của khung `book-layout` (Google Fonts) vẫn là request ngoài duy nhất của trang: GET không mang chữ báo cáo; chặn nó trang vẫn chạy (đã kiểm). Bỏ hẳn cần sửa `book-layout`.

## Chữ: Lexend Deca Light + mỏng, kiểu tạp chí (owner 1/11: «lexend deca light và mỏng để làm tạp chí», trang mẫu lexend.com)
- Họ font Lexend Deca TỰ PHỤC VỤ: hai tệp `assets/fonts/LexendDeca-vietnamese.woff2` + `LexendDeca-latin.woff2` (font biến thiên wght 100–900, giấy phép OFL: `assets/fonts/OFL-Lexend.txt`) nhúng base64 vào HTML bằng `finish()`. Link Google Fonts của `book-layout` bị gỡ chỉ trong báo cáo này: request ngoài của trang = 0 (trước đó 7). Tên font ở MỘT chỗ: `--sans` trong `CSS`.
- Độ đậm (Kanade DUYỆT): thân, h3, nút, nhãn 300; tiêu đề và số lớn tối thiểu 200; 100 CHỈ khi cỡ chữ ≥ 48 px VÀ khổ ≥ 1100 px (số lớn và h1 bìa). Không chữ nào ≥ 400, TRỪ MỘT NGOẠI LỆ (owner 1/11: «Status và Workers đã in bold đâu?», lời owner mới nhất thắng luật D-c2-002 «chỉ Light»): NHÃN đầu dòng trước «:» (Status, Workers, Branch, Thread, Tình trạng, Người làm, Nhánh, nhãn màu ở chú giải, Sha on Live…) đậm 600 qua `**Nhãn:**` → `<b>`; chữ SAU «:» giữ Light. Font biến thiên wght 100–900 đã nhúng nên không thêm tệp. CSS: `b,strong{font-weight:600}` là chỗ duy nhất ≥ 400; luật kiểm: thẻ `<b>` phải đúng 600 và kết thúc bằng «:», mọi chữ khác ≤ 300, mọi dòng trong thẻ việc mở đầu bằng nhãn đậm. Mọi độ đậm ép bằng `!important` vì `book.css` đặt 500/700/800 ở nhiều chỗ.
- Chữ mảnh bù bằng màu: phần tử ≤ 200 dùng #111; chữ phụ nhỏ `--ink3` từ #8a8a82 (3,3:1) lên #5c5c56 (≥ 6:1). WCAG không tính độ mảnh của nét: «độ mảnh chưa đo bằng số, đã nhìn ảnh».
- Kiểu tạp chí học từ lexend.com (đọc style thật bằng Playwright): nền sáng, chữ đen, tiêu đề lớn mỏng canh trái, lề rộng (`--page-pad` lớn hơn), thân 16 px dòng 1,7. KHÔNG áp khối hero đỏ #ff0000 và chữ nhấn đỏ của trang đó: trong báo cáo đỏ = «cần xử lý», xanh lá = xong.
- `check_lang.mjs` thêm luật chữ ở mọi khổ và cả EN lẫn VI: độ đậm ≤ 300; < 200 chỉ khi ≥ 48 px; chữ ≤ 200 màu gần đen; tương phản ≥ 4,5:1 (< 24 px) hoặc ≥ 3:1; họ font là Lexend Deca; font thật sự nạp từ dữ liệu nhúng; request ngoài (kể cả font) = 0.
- Giới hạn: ký tự ngoài bộ vietnamese + latin (vd →, ≤, ≥, ✓) rơi về font hệ thống ở độ đậm 300 (đã chụp dòng thử: dấu tiếng Việt đủ, mũi tên và ≤ đi font khác nhưng cùng độ nhẹ). Chữ trong hình bìa SVG dùng font hệ thống mảnh (ảnh nhúng không dùng được font của trang). Tệp HTML nặng thêm ~100 KB (font base64 ≈ 70 KB). Độ mảnh của nét: chưa đo bằng số.

## Luật của owner đã chốt (mỗi luật có chỗ kiểm; chi tiết ở `SKILL.md` RULE-06..RULE-14)
Danh sách theo thứ tự owner nói (31/10 → 1/11). Lời owner mới nhất thắng; luật mới đảo luật cũ thì sửa luật cũ ở đây, không để hai luật mâu thuẫn.
1. Xanh lá chỉ khi XONG; không tick «- », không «*…*» (31/10). Kiểm: `--selftest`.
2. Thoáng: mỗi việc một thẻ, mỗi ý một dòng có khoảng cách (31/10). Kiểm: `--selftest`.
3. Mỗi dòng ≤ 20 chữ (10-20, sau đó 25 → 20) ở EN và VI. Kiểm: `--selftest`. «≥ 10» không bắt buộc cho dòng nhãn–giá trị ngắn.
4. EN theo ASD-STE100 cơ học + nút VI không tốn token (31/10). Kiểm: `--selftest`, `check_lang.mjs`.
5. Quyển tập: MỌI tờ cao bằng nhau ±2 px theo khổ chuẩn là tờ bìa; tờ ít nội dung để trống, không nhồi thẻ; khe giữa hai khối trong tờ ≤ 80 px (1/11, bỏ luật «trống cuối ≤ 120»). Kiểm: `check_lang.mjs`.
6. Lexend Deca Light + mỏng, tự phục vụ (1/11). Kiểm: `check_lang.mjs`.
7. Nhãn đầu dòng trước «:» đậm 600 (1/11): ngoại lệ duy nhất của luật 6. Kiểm: `check_lang.mjs`.
8. Tên màu tô màu tương ứng (1/11). Kiểm: `--selftest`, `check_lang.mjs`.
9. Mã máy đóng chip (1/11). Kiểm: `--selftest`, `check_lang.mjs`.
10. Quy trình: tự chụp 390 và 1280, tự xem, gửi ảnh trước/sau (31/10 → 1/11).

## Chấm trạng thái (owner 1/11: «cái dot tròn vẫn vậy, bỏ luôn đi; tôi tưởng bạn làm được dot pastel màu đặc»)
- Trước: emoji 🔴🟡🔵⚪🟢 ở đầu thẻ việc, dòng tóm tắt và chú giải. Emoji bóng loáng (hình cầu có đốm sáng), lệch hàng với chữ và đổi theo hệ điều hành, nên owner bỏ.
- Nay: hình tròn CSS màu ĐẶC pastel, phẳng: đỏ #e98c83, vàng #efc95c, xanh dương #86b3e6, xám #b7bbc1, xanh lá #8dce96 (`DOT_PASTEL`; cùng hue với màu tình trạng, nhạt hơn; tương phản với giấy 1,5–2,4:1: vàng thấp nhất 1,53:1). Cỡ 0,7 em, cách chữ 0,45 em, `vertical-align:-.04em` cho tâm chấm trùng tâm chữ (đo: lệch ≤ 1 px ở 16 px). Marker md `⟐màu⟐` (hằng `DT`, bảng `COLORS`), `finish()` đổi thành `<span class="dot dot-màu" aria-hidden="true">`.
- Chấm chỉ trang trí: màu cũng nằm ở chữ đi kèm (tên màu tô màu ở tiêu đề trang, chú giải, dòng tóm tắt), nên `aria-hidden`.
- `check_lang.mjs`: không còn ký tự chấm màu (emoji, «●») ở bất kỳ chữ nào; mỗi `.dot` đúng màu của bảng, phẳng (không gradient/bóng/viền), tròn (rộng = cao, bo ≥ nửa), tương phản ≥ 1,5:1 với nền thật phía sau, tâm lệch tâm chữ ≤ 3 px; ≥ 8 chấm. Chứng đỏ: bản emoji 5ab8c73 → FAIL (không có `.dot`, thẻ việc không nhận ra).

## Chip cho mã máy (owner 1/11: «mấy mã kiểu này thêm luật vào skill đóng vào chip và highlight lên»)
- Nguồn kiểu: trang mẫu của owner https://uiux.giatbh.io.vn/components/chip.html, Hình 1 «Vỏ chip» (lớp `.cx.fill`), đo bằng Playwright 1/11: `border-radius 999px`, nền pastel theo nhóm (Blue, Violet, Gray, Green, Periwinkle, Yellow, Pink, Teal, Peach), viền 1 px đậm hơn nền ~15 %, chữ #1a1d21, 14 px, padding ngang 14 px, cao 32 px. Rp dùng viên thuốc cùng kiểu nhưng gọn hơn để nằm giữa dòng chữ: padding ngang 12 px, cao 22 px, chữ Lexend Deca 300 (RULE-10 cấm 400); chip dài (> 30 ký tự) bo 14 px để khi xuống dòng không thành viên thuốc phình.
- Mã máy đóng chip: mã mở lại phiên (`sf98721ecbfeb`), sha, id tin (`m1a…`), tên `room:<thread>`, tên nhánh, `hang_open_work`. Trong md: `⟮nhóm‖mã⟯` (hàm `chip(text, kind)`), `finish()` đổi thành `<code class="chip chip-nhóm">`.
- Nhóm theo LOẠI MÃ (bảng `CHIP_WHAT` + `CHIP_KINDS`, giá trị đo ở trang mẫu): sha = Pink #f7c1d9/#d3a5b9; `room:`, `hang_open_work` và tên nhánh = Teal #b2ece2/#97c8c0; mã mở lại = Peach #fae3c8/#d5c1aa. KHÔNG xám (owner m1a19339fed71243; bản xám #dcdcdc bị bỏ), KHÔNG tím (owner m1a1932949ed7b2d «lạc quẻ», Klau m1a1933d34ca6dd5; bản Violet/Periwinkle bị bỏ), không đỏ/xanh lá (Kanade), không vàng/xanh dương (màu tình trạng). Pink (hue ~333°) vừa dưới ngưỡng tông đỏ 335° của luật kiểm. Loại mã do người gọi `chip(text, what)` khai và ghi ra `data-what`; luật kiểm đọc `data-what`, không đoán từ chữ (Kirei: nhánh toàn hex bị đoán nhầm thành sha). Luật kiểm chặn nền chip có tông tím (hue 225–320°), đỏ (≥ 335° hoặc ≤ 12°), xanh lá (75–150°).
- Xuống dòng (owner m1a19338db452775: «lỡ xuống dòng thì chip vẫn bọc kiểu wrapping, đừng bọc kiểu thừa»): chip là `display:inline` + `box-decoration-break:clone` nên mỗi dòng là một viên ôm sát chữ như highlight; trước đó `inline-block` làm slug 2 dòng thành khối chữ nhật rộng hết dòng. Slug ngắt ở dấu «-». Vì trình duyệt không tính đệm của mảnh giữa khi ngắt dòng, đoạn có chip chừa lề phải 26 px (`p:has(.chip)`).
- Không phải mã, không chip: «none», «chưa có», tên người, tên việc, nhãn. Chân trang và dòng chạy đầu trang không đóng chip (trang trí).
- `check_lang.mjs`: mọi mã khớp mẫu ngoài chip là FAIL; mỗi chip phải đúng nhóm (theo `data-what`), đúng nền của nhóm, inline + clone, mỗi mảnh dòng chỉ rộng hơn chữ đúng đệm + viền, viền 1 px đậm hơn nền, bo ≥ 14 px, chữ #1a1d21, Lexend Deca 300, tương phản ≥ 7:1, nổi hơn NỀN THẬT phía sau chip ≥ 1,06:1 (đi ngược tổ tiên tới nền đầu tiên có alpha > 0: giấy `.spread` rgb(251,250,246), trong khối `.stat` rgb(241,239,232); lần đầu lấy nền `.page` trong suốt nên so với đen và không bao giờ FAIL, Kirei bắt ở f51402b); không tràn khung; tối thiểu 8 chip; nền chip KHÔNG có tông đỏ (hue ≥ 335° hoặc ≤ 12°) hoặc xanh lá (75–150°) vì đỏ = cần xử lý, xanh lá = xong (Kanade 1/11); độ đậm chữ chip ≤ 300. Chứng đỏ: nền chip đổi sang #c4f2c8 (xanh lá, hue 125°), #f8c8c4 (đỏ, hue 5°), #f7c1d9 (hồng, hue 335°) đều FAIL; độ đậm 500 FAIL.
- Lịch sử các bản chip bị bỏ: tím #ece8fb (lạc quẻ), xám ấm #ebe8de đơn cách (owner chỉ trang mẫu thay thế). Chứng đỏ: bản đơn cách báo FAIL «họ font không phải Lexend Deca … code.chip»; chip nền #fbfaf6 (trùng giấy) báo FAIL «1.000:1 < 1,06».
- Đã tra uiux.giatbh.io.vn (1/11, `GET /api/search`): «tạp chí», «typography», «báo cáo», «Lexend», «mã máy sha nhánh» → site chỉ lập chỉ mục hai nhóm: hiệu ứng cuộn trang (Ink Transition, Article Details, Staggered Text Reveal…) và mẫu chip (29 mẫu); không có mục chữ, tạp chí hay báo cáo. Hiệu ứng cuộn: KHÔNG dùng (báo cáo là trang tĩnh gửi đính kèm). Mẫu chip: DÙNG Hình 1.

## Màu chữ của tên màu (owner 1/11: «mấy chữ Red, Yellow tô màu tương ứng đi»)
Bảng `TXT` trong `task_report.py`: đỏ #b3261e, vàng #8a6100, xanh dương #1f5fa8, xám #5b6168, xanh lá #2e6b1f. Đậm hơn màu thanh và chấm (vàng #e0a800 chỉ ~2:1 trên giấy) để tương phản ≥ 4,8:1. Áp ở: tiêu đề trang («Red», «Red continued», «Đỏ», «Đỏ tiếp»), nhãn chú giải, nhãn dòng tóm tắt («Red tasks:»), nhãn màu trong hình bìa. Dấu chấm màu ở đầu thẻ việc là emoji, đã có màu sẵn. Trong nhãn đậm thì cả tên màu đậm 600; trong h2 (mảnh 200 phải #111) tên màu dùng 300. Marker trong md: `⟬màu‖chữ⟭` → `<span class="c-màu">`; `check_lang.mjs` kiểm mọi tên màu có `.c-màu` và đúng màu, và số tên màu nhận ra ở bản VI phải BẰNG bản EN (9 = 9 trên dữ liệu có đỏ + vàng). Regex nhận tên màu không dùng `\b`: `\b` của JS không coi «ỏ», «á» là chữ nên «Đỏ:», «Xanh lá:» không khớp (Kirei bắt ở 1cda5bc); dùng `(?=[\s:：]|$)`.

## Giới hạn đã biết
- Chỉ thread mở của MỘT phòng gốc (mặc định `vinh-hong`, tên phòng ghi ở brand và footer của báo cáo).
- Không có smoke, không có sha từng nhánh: ghi «chưa đo». Cần thì thêm nguồn đọc ở Hang trước, rồi mới thêm vào báo cáo.
- Không dùng danh sách «- chữ» của `book-layout` cho dòng việc: nó vẽ dấu tích xanh trước MỌI dòng, kể cả dòng cảnh báo, và owner đọc tích là «xong». Báo cáo không có dấu tích nào (`ul.checks` = 0 trong HTML); selftest chặn dòng «- » quay lại.
- Chữ nhấn «*…*» của `book-layout` có màu XANH LÁ nên báo cáo không dùng nó ở bìa và tiêu đề (xanh lá chỉ dành cho «xong»); selftest chặn «*» quay lại.
- Màu theo giai đoạn mà `/work/open` trả, chưa đọc giai đoạn trong sổ vòng đời: việc đã ĐẠT trong sổ vẫn có thể hiện xám hoặc vàng «chờ review». Đọc giai đoạn sổ là việc để sau.
- Luật khoảng trống ĐÃ ĐỔI nhiều lần (đọc từ cuối): (1) owner 31/10 «chừa quá nhiều khoảng trống»: khe ≤ 80, trống ≤ 120; (2) owner 1/11 «quyển tập bị cắt cụt»: MỌI tờ cao bằng khổ chuẩn của bìa, Klau 1/11 truyền lời owner «để space cũng được, không cần cố nhét»: BỎ luật trống cuối ≤ 120 và BỎ luật «không khe giữa các cặp tờ» (bản «một quyển liền» 8a135ca bị thay). Luật hiện hành: mọi tờ cao bằng nhau ±2 px và khe giữa hai khối trong tờ ≤ 80 px (trừ bìa).
- Dáng QUYỂN TẬP (owner 1/11): khổ > 820 px là các cặp hai tờ kề nhau, khe 40 px và bóng từng cặp là của `book-layout`, giữ nguyên. Mọi tờ (bìa, Tóm tắt, mỗi tờ một thẻ, Not measured) cao BẰNG NHAU: `finish()` nhúng một đoạn JS `eq()` đặt `min-height` của mọi `.page` bằng chiều cao của tờ cao nhất (thường là bìa, vì tiêu đề lớn và hình thanh), tính lại khi đổi EN/VI, đổi khổ, font nạp xong, dịch tên việc; khổ ≤ 820 px bỏ chỉnh. Tờ ít nội dung để trống phía dưới, không nhồi thẻ (một thẻ mỗi tờ). Lịch sử các bản bị bỏ: một cột 640 px; mỗi tờ giấy riêng (vết khuyết như bị cắn); một quyển liền không khe. Ở khổ ≤ 820 px một cột như `book-layout`.
- CSS riêng của rp (trong `finish()`, không sửa `book-layout`): khối số lớn `.stat` có khoảng cách dưới và nền xám ấm thay nền xanh lá nhạt (xanh lá chỉ dành cho «xong»); tiêu đề thẻ `.lead` cách dòng dưới 12 px.
- Footer của trang bìa ở 390 px có thể chồng lên ảnh bìa (lỗi chung của `book-layout`, không sửa ở đây).
- Dịch tên việc bằng Translator API chỉ kiểm bằng bản GIẢ trong Playwright (có API, chưa kiểm bản dịch thật của Chrome): chất lượng dịch và tải model lần đầu: chưa đo.
- Hình bìa là SVG nhúng nên nhãn màu luôn bằng tiếng Anh, không đổi theo nút.
- Không dùng bảng markdown (điện thoại không đọc được); danh sách thay bảng.

## Thêm chế độ khác sau này
Tạo `references/<chế độ>.md` cùng dạng, thêm một dòng vào bảng «Reference» của `SKILL.md`, thêm câu gọi (`/rp <chế độ>`) vào `description`. Không đổi hub ngoài hai chỗ đó.
