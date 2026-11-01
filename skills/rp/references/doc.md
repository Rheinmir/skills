# /rp doc: báo cáo, tài liệu thường

Chế độ thứ hai của hub `rp` (owner 1/11: «aware tự xài skill /rp để làm report», «cứ đụng tới report thì trigger»). Dùng cho MỌI báo cáo / tài liệu / tổng kết / tóm tắt / so sánh / đề xuất không phải tình trạng task. Cùng đường ống với `task`: md → `book-layout` (book.py) → `finish()` → `check.mjs` + `check_lang.mjs` → gửi owner. Agent KHÔNG viết HTML tay.

## Cách dùng
1. Viết nguồn (markdown đơn giản, mỗi ý MỘT dòng, ≤ 20 chữ mỗi dòng). Mẫu:
```
# Tiêu đề báo cáo
kicker: Báo cáo công cụ
> Một dòng dẫn cho bìa.
stat: 3 | plugin đã cài | pm-toolkit pm-execution
## Tóm tắt
Nguồn: phuryn/pm-skills của Pawel Huryn.
Phạm vi: mức người dùng, chỉ Mac mini.
## Rủi ro
Cập nhật: một tác giả ngoài giữ kho này.
```
2. `python3 scripts/doc_report.py <nguồn>.md --check`: nguồn chưa đạt thì script in TỪNG lỗi kèm dòng nào và sửa thế nào (quá 20 chữ, dòng mở đầu bằng «- », chữ nhấn «*…*», trang trống, trang quá 9 dòng…). Sửa rồi chạy lại.
3. `python3 scripts/doc_report.py <nguồn>.md --out <thư mục> --build` → `rp-doc-<giờ>.md` + `.html`.
4. Cổng kiểm như `task` (W04, W04a, W04b): `check.mjs` hai dòng `ok`, `check_lang.mjs` không FAIL, XEM ảnh 390 và 1280.
5. Gửi owner kèm tệp (W05).

## Hai ngôn ngữ
- `--lang vi` (MẶC ĐỊNH): một ngôn ngữ, không kiểm STE, không nút EN/VI. Owner đọc tiếng Việt.
- `--lang both`: nguồn JSON mà mọi chuỗi là cặp `{"en": "…", "vi": "…"}`; EN kiểm STE cơ học (như `task`), trang có nút EN/VI. Chỉ dùng khi người đọc cần cả hai. Cấu trúc JSON: `{"title","kicker","lead":[…],"stat":{"n","label","codes":[…]},"pages":[{"title","lines":[{"label","text"}]}],"footer"}`.

## Luật (giữ như `task`, trừ phần riêng tình trạng task)
- Giữ: nền sáng, Lexend Deca Light (RULE-10), khổ quyển tập và tờ cao bằng nhau (RULE-09), mã máy đóng chip pastel theo nhóm (RULE-15; script TỰ nhận sha, `room:…`, nhánh/đường dẫn có «/», mã tin `m…`, mã mở lại `s…` và đóng chip), mỗi ý một dòng ≤ 20 chữ (RULE-06/07), không danh sách «- », không chữ nhấn «*…*» (RULE-13), 0 request ngoài, nhãn đậm trước «:» (RULE-08).
- Bỏ (riêng task): chấm màu tình trạng, tên màu tô màu, nút Translator trên tên việc. `check_lang.mjs` đọc `data-mode` ở `<html>` (finish() ghi `task` hoặc `doc`) và chỉ chạy các luật đó khi `task`.
- Bìa: hình phẳng trung tính do script sinh (số dòng mỗi trang, màu xám ấm), KHÔNG tranh núi xanh lá mặc định của book-layout, KHÔNG xanh lá, KHÔNG đỏ (xanh lá đọc là «xong», đỏ là «cần xử lý»).

## Không làm
- Không ghi gì lên Hang ngoài tin báo cáo (như `task`).
- Không bịa số: số không có nguồn thì ghi «chưa đo».
