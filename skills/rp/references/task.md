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
1. 🔴 Đỏ, cần xử lý: có agent đã chết (`down[]`), hoặc giai đoạn blocked/failed, hoặc đang làm mà im quá 12 giờ.
2. 🟡 Vàng, chậm hoặc chờ: chờ owner (`owner_wait`), chờ review, đợi việc khác (`blocking[]`), đang làm mà im quá 2 giờ.
3. 🔵 Xanh dương: đang làm bình thường, chưa xong.
4. ⚪ Xám: backlog hoặc xếp hàng, chưa bắt đầu.
5. 🟢 Xanh lá: XONG, cờ `deployed` true (đã lên Live) và không có agent chết.
Thứ tự ưu tiên: xanh lá, đỏ, vàng, xám/xanh dương. Dòng có nhiều lý do liệt kê hết.

## Báo cáo gồm
1. Bìa: số việc mở, số đã xong, giờ chốt, hình thanh số việc theo màu.
2. Chú giải màu (đầu báo cáo, để người đọc biết xanh lá mới là xong).
3. Tóm tắt: số việc theo màu, sha Live.
4. Từng nhóm màu (4 thread mỗi trang). Mỗi dòng là MỘT đoạn văn: chấm màu, tên, lý do, người làm (giai đoạn), nhánh, im bao lâu, `room:<mã>`.
5. Chưa đo: smoke Live, sha từng nhánh, thứ ngoài phạm vi.

## Cách đọc cho đúng
- `deployed` false = chưa lên Live; `status` review = chờ review (vàng, không phải xong). Không viết «xong» khi dữ liệu không nói.
- «Im» là thời gian từ tin cuối trong thread (`idle`), không phải thời gian agent không làm gì.
- `down` có mã mở lại thì việc mở lại do Điều phối làm; báo cáo chỉ nêu.
- Thread backlog không có người làm là bình thường, không phải lỗi.

## Trước khi đăng: chụp và XEM (owner 31/10: «tự chụp hình preview lại xem nó hợp lý chưa hay lại lạc quẻ pastel»)
Hai dòng `ok` của `check.mjs` chỉ nói không tràn chữ; không nói màu có hợp hay không. Sau khi dựng báo cáo phải mở `<tệp>-390.png` và `<tệp>-1280.png` (check.mjs đã chụp) rồi nhìn: bìa, chấm màu, chú giải, chữ nhỏ hay chồng nhau, số trên bìa khớp tóm tắt. Không đăng khi bìa gợi «xong» (tranh xanh lá, màu pastel nhạt) hay chấm màu khó đọc.
Bìa dùng hình thanh số việc theo màu do chính script sinh (`cover_svg`, nhúng sẵn trong tệp), không dùng tranh núi xanh lá mặc định của `book-layout`; thanh đậm, phẳng, 0 việc thì chỉ còn khung rỗng.

## Giới hạn đã biết
- Chỉ thread mở của MỘT phòng gốc (mặc định `vinh-hong`, tên phòng ghi ở brand và footer của báo cáo).
- Không có smoke, không có sha từng nhánh: ghi «chưa đo». Cần thì thêm nguồn đọc ở Hang trước, rồi mới thêm vào báo cáo.
- Không dùng danh sách «- chữ» của `book-layout` cho dòng việc: nó vẽ dấu tích xanh trước MỌI dòng, kể cả dòng cảnh báo, và owner đọc tích là «xong». Báo cáo không có dấu tích nào (`ul.checks` = 0 trong HTML); selftest chặn dòng «- » quay lại.
- Chữ nhấn «*…*» của `book-layout` có màu XANH LÁ nên báo cáo không dùng nó ở bìa và tiêu đề (xanh lá chỉ dành cho «xong»); selftest chặn «*» quay lại.
- Màu theo giai đoạn mà `/work/open` trả, chưa đọc giai đoạn trong sổ vòng đời: việc đã ĐẠT trong sổ vẫn có thể hiện xám hoặc vàng «chờ review». Đọc giai đoạn sổ là việc để sau.
- Footer của trang bìa ở 390 px có thể chồng lên ảnh bìa (lỗi chung của `book-layout`, không sửa ở đây).
- Không dùng bảng markdown (điện thoại không đọc được); danh sách thay bảng.

## Thêm chế độ khác sau này
Tạo `references/<chế độ>.md` cùng dạng, thêm một dòng vào bảng «Reference» của `SKILL.md`, thêm câu gọi (`/rp <chế độ>`) vào `description`. Không đổi hub ngoài hai chỗ đó.
