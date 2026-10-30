# Cách viết case-study trong book-layout

Owner 30/10: mọi tài liệu theo MỘT design = khuôn hình `book-layout` + cách viết case-study của bài «Designing a system for book reviews, a UX case study» (uxdesign.cc). Người đọc đi từ kết luận tới bằng chứng, không phải đọc hết mới biết kết luận.

Dùng cho: tài liệu triển khai, patch, thiết kế, so sánh, báo cáo POC, đề xuất cần người quyết. Không dùng cho ghi chú ngắn hay tin nhắn.

## Thứ tự trang

1. `=== cover`: kicker «Case study: …», tiêu đề hai dòng, `>` MỘT câu kết luận có một con số, rồi một dòng việc người đọc cần quyết (nếu có).
2. `=== toc` khi có từ 4 chương: mỗi dòng một chương; `~` chỉ trang kết quả cho người vội.
3. Bối cảnh và vấn đề: ai bị ảnh hưởng, một ví dụ thật có ngày, cách cũ hỏng ở đâu. Một khối `!` với con số đau nhất và nguồn.
4. Câu hỏi và KPI: `"` một câu «Làm sao để …» (một tài liệu một câu hỏi); khung `### KPI` liệt chỉ số có đơn vị và cách đo.
5. Các chặng, mỗi chặng một trang: Đo hiện trạng, Thiết kế, Thử, So sánh, Kiểm. Bỏ chặng không có việc thật. Mỗi chặng 1 đến 3 đoạn rồi MỘT sản phẩm: GIF có ghim, `!` số đo, `=== cycle` cho luồng ba bước, hoặc ảnh.
6. Cũ so với mới: khối `<>` mỗi chỉ số một dòng, nguồn ở cột cuối. Dòng mà cách mới không hơn dùng `<>!`, không giấu.
7. Bài học và bước tiếp: `### Bài học` mỗi bài một câu viết thành quy tắc lần sau; `### Bước tiếp` các bước `1.` có `;` ghi cờ tắt mặc định hoặc lối lùi.

## Nhịp viết

- Đoạn ngắn, khoảng 30 từ, một ý một đoạn; câu đầu nói điều chính.
- Mỗi chặng kết bằng thứ nó tạo ra, không giải thích thêm.
- Số luôn có nguồn (tệp, sha, ngày); chưa đo thì ghi «chưa đo». Cũ và mới cùng chỉ số, cùng máy, cùng mốc.
- Không bảng, không blur, không nối ý bằng dấu chấm giữa: dùng danh sách, khối `<>`.

## Hình (rút từ bài mẫu)

- Mở bài bằng một hình lớn cho người đọc thấy sản phẩm trước khi đọc chữ: ảnh ở `=== cover` hoặc trang `=== image`.
- Hình ngay sau đoạn giới thiệu nó; không để hai hình liền nhau không có chữ ở giữa (khoảng một GIF mỗi trải hai trang).
- Nhãn nằm trong hoặc ngay trên hình, chữ ngắn: ghim `+ x,y chữ` thay cho chú thích dài dưới hình.
- Luồng ba bước dùng `=== cycle`; trước và sau dùng hai ảnh hoặc khối `<>`.
- Tài liệu nặng (log, JSON) để link ngoài, trong trang chỉ trích một hai dòng.

## Checklist trước khi gửi

- Bìa có MỘT câu kết luận có số; có câu hỏi «Làm sao để …».
- Mỗi chặng đúng một sản phẩm và nguồn của nó.
- Cũ so với mới có dòng `<>!` cho chỗ cách mới không hơn (nếu có).
- `check.mjs` hai dòng `ok` (1280 và 390).

Mẫu đầy đủ: `assets/case-study.md` (khung trống) và `examples/driver-chung.md` (tài liệu thật, số đo xen kẽ của Hang).
