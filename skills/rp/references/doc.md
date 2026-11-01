# /rp doc: báo cáo, tài liệu thường

Chế độ thứ hai của hub `rp` (owner 1/11: «aware tự xài skill /rp để làm report», «cứ đụng tới report thì trigger»). Dùng cho MỌI báo cáo / tài liệu / tổng kết / tóm tắt / so sánh / đề xuất không phải tình trạng task. Cùng đường ống với `task`: md → `book-layout` (book.py) → `finish()` → `check.mjs` + `check_lang.mjs` → gửi owner. Agent KHÔNG viết HTML tay.

## Cách dùng
1. Viết nguồn bằng TIẾNG ANH (markdown đơn giản, mỗi ý MỘT dòng, ≤ 20 chữ mỗi dòng, theo ASD-STE100 cơ học: câu ngắn, chủ động, tối đa 1 dấu phẩy, không «;», không viết tắt ngoài DONE/ID/UTC, không từ cấm should/may/might/shall/get/make). Mẫu:
```
# Report title
kicker: Tool report
> One lead line for the cover.
stat: 3 | plugins installed | pm-toolkit pm-execution
## Summary
Source: phuryn/pm-skills by Pawel Huryn.
Scope: user level, Mac mini only.
## Risks
Updates: an outside author owns the repository.
```
2. `python3 scripts/doc_report.py <nguồn>.md --check`: nguồn chưa đạt thì script in TỪNG lỗi kèm dòng nào và sửa thế nào (quá 20 chữ, dòng mở đầu bằng «- », chữ nhấn «*…*», trang trống, trang quá 9 dòng, lỗi STE như viết tắt PM/JSON/MCP/PRD kèm cách diễn đạt lại…). Sửa rồi chạy lại. `--build` cũng chặn khi nguồn chưa đạt.
3. `python3 scripts/doc_report.py <nguồn>.md --out <thư mục> --build` → `rp-doc-<giờ>.md` + `.html`.
4. Cổng kiểm như `task` (W04, W04a, W04b): `check.mjs` hai dòng `ok`, `check_lang.mjs` không FAIL, XEM ảnh 390 và 1280.
5. Gửi owner kèm tệp (W05).

## Ngôn ngữ (owner 1/11: «mặc định tiếng Anh theo chuẩn hàng không ASD-STE100 và có nút translate native không cần token»)
- `--lang en` (MẶC ĐỊNH): trang MỘT ngôn ngữ tiếng Anh. Nút «Translate» (góc trên) chỉ hiện khi trình duyệt có Translator API; bấm thì dịch EN→VI ngay trong trình duyệt (không qua token, không gọi mạng của trang), mã máy trong chip giữ nguyên, bấm lần nữa về tiếng Anh. Agent KHÔNG tự viết bản tiếng Việt.
- `--lang vi`: một ngôn ngữ Việt, không STE, không nút. Chỉ khi owner đòi rõ.
- `--lang both`: nguồn JSON mà mọi chuỗi là cặp `{"en": "…", "vi": "…"}`; EN kiểm STE, nút EN/VI. Chỉ khi owner đòi song ngữ. Cấu trúc JSON: `{"title","kicker","lead":[…],"stat":{"n","label","codes":[…]},"pages":[{"title","lines":[{"label","text"}]}],"footer"}`.

## Luật (giữ như `task`, trừ phần riêng tình trạng task)
- Giữ: nền sáng, Lexend Deca Light (RULE-10), khổ quyển tập và tờ cao bằng nhau (RULE-09), mã máy đóng chip pastel theo nhóm (RULE-15; script TỰ nhận sha, `room:…`, nhánh/đường dẫn có «/», mã tin `m…`, mã mở lại `s…` và đóng chip), mỗi ý một dòng ≤ 20 chữ (RULE-06/07), không danh sách «- », không chữ nhấn «*…*» (RULE-13), 0 request ngoài, nhãn đậm trước «:» (RULE-08).
- Bỏ (riêng task): chấm màu tình trạng, tên màu tô màu, nút Translator trên tên việc. `check_lang.mjs` đọc `data-mode` ở `<html>` (finish() ghi `task` hoặc `doc`) và chỉ chạy các luật đó khi `task`.
- Bìa: hình phẳng trung tính do script sinh (số dòng mỗi trang, màu xám ấm), KHÔNG tranh núi xanh lá mặc định của book-layout, KHÔNG xanh lá, KHÔNG đỏ (xanh lá đọc là «xong», đỏ là «cần xử lý»).

## Không làm
- Không ghi gì lên Hang ngoài tin báo cáo (như `task`).
- Không bịa số: số không có nguồn thì ghi «chưa đo».
