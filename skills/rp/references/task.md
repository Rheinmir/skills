# /rp task — báo cáo tình trạng các task

Chế độ đầu tiên của hub `rp`. Owner (31/10, Issue 452): «báo cáo tình trạng các task đi», «làm thành 1 skill báo cáo dùng skill tạo report hôm qua» (= `book-layout`, Issue 428).

## Nguồn số liệu (chỉ đọc)
- `GET /work/open?room=<phòng>` của chính Hang (cùng dữ liệu MCP `hang_open_work`; mặc định `vinh-hong`, đổi bằng `--room`; không kèm `room` thì Hang gộp mọi phòng gốc token máy thấy nên báo cáo phải luôn truyền), Bearer token máy ở `~/.hang/token`. Mỗi thread mở có: `room`, `name`, `kind` (issue/epic), `status`, `workers[]` (tên, giai đoạn, `health`), `down[]` (agent đã chết, mã mở lại), `blocking[]`, `branch`, `deployed`, `owner_wait`, `idle`, `req[]`.
- `running` = sha đang chạy trên Live.
- Script gửi header `User-Agent: hang-rp/1`: cổng công khai từ chối UA mặc định của Python (403).

## Báo cáo gồm
1. Bìa: số việc mở, số đang làm, giờ chốt.
2. Tóm tắt: số theo từng giai đoạn, số agent đã chết, sha Live.
3. Cần chú ý (chỉ khi có): chờ owner; agent đã chết kèm mã mở lại; bị chặn; đang làm mà im quá 2 giờ.
4. Từng nhóm: Bị chặn, Đang làm, Chờ review, Xếp hàng, Backlog (4 thread mỗi trang). Mỗi dòng: tên, người làm (giai đoạn), nhánh, lên Live chưa, im bao lâu, `room:<mã>`.
5. Chưa đo: smoke Live, sha từng nhánh, thứ ngoài phạm vi.

## Cách đọc cho đúng
- `deployed` false = chưa lên Live; `status` review = chờ review. Không viết «xong» khi dữ liệu không nói.
- «Im» là thời gian từ tin cuối trong thread (`idle`), không phải thời gian agent không làm gì.
- `down` có mã mở lại thì việc mở lại do Điều phối làm; báo cáo chỉ nêu.
- Thread backlog không có người làm là bình thường, không phải lỗi.

## Giới hạn đã biết
- Chỉ thread mở của MỘT phòng gốc (mặc định `vinh-hong`, tên phòng ghi ở brand và footer của báo cáo).
- Không có smoke, không có sha từng nhánh: ghi «chưa đo». Cần thì thêm nguồn đọc ở Hang trước, rồi mới thêm vào báo cáo.
- `book-layout` vẽ dấu tích xanh đầu mỗi dòng danh sách, kể cả dòng cảnh báo: đừng đọc dấu tích là «ổn».
- Không dùng bảng markdown (điện thoại không đọc được); danh sách thay bảng.

## Thêm chế độ khác sau này
Tạo `references/<chế độ>.md` cùng dạng, thêm một dòng vào bảng «Reference» của `SKILL.md`, thêm câu gọi (`/rp <chế độ>`) vào `description`. Không đổi hub ngoài hai chỗ đó.
