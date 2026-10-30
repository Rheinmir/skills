---
title: Driver chung thay cửa sổ và hook
brand: Hang
date: 30.10.2026
vol: Case study 01
footer: Driver chung: tài liệu patch triển khai
---
=== cover
^ Case study: tài liệu patch triển khai
# Đẩy tin thẳng vào / *agent đang rảnh.*
> Driver chung thay cửa sổ và hook: mở phiên nhanh hơn ở cả ba hãng, tin tới phiên rảnh trong 2 đến 3 giây.
---
Nên làm, bật theo cờ, mặc định tắt, giữ lối lùi về cửa sổ.

=== toc
# Mục lục
01 | Bối cảnh và vấn đề | Cửa sổ và hook vỡ theo ba đường | 03
02 | Câu hỏi và KPI | Một câu hỏi, đo cùng mốc | 04
03 | Đo cách cũ | 443 yêu cầu mở phiên | 05
04 | Thiết kế và POC | Holder giữ tiến trình agent | 06
05 | Cũ so với mới | Đo xen kẽ từng vòng | 07
06 | Bài học và bước tiếp | Cờ tắt mặc định, lối lùi | 08
~ Đọc trang 7 trước / *nếu vội*

=== page
@ Chương 1
^ Bối cảnh và vấn đề
# Tin nằm im / *ở phiên rảnh.*
Hang mở agent trong một cửa sổ rồi chờ agent tự hỏi tin bằng hook. Phiên Codex đứng rảnh không đọc hộp thư vì Codex không có hook Stop.
Tin của chủ Hang chờ khoảng 20 phút (30/10). Antigravity chỉ có hook trước mỗi lần gọi model nên cũng không nhận tin lúc rảnh.
! 13% | yêu cầu mở phiên kẹt ở màn chào lần đầu, cần người bấm | 59 trên 443 yêu cầu, 20 đến 30/10, spawn_history.json

=== page
@ Chương 2
^ Câu hỏi thiết kế
# Một câu hỏi, / *đo cùng mốc.*
" Làm sao để Hang đẩy được một lượt vào agent mà không cần cửa sổ và hook kéo tin, và chỉ đổi khi số đo cạnh nhau cho thấy tốt hơn? -- Câu hỏi của tài liệu
### KPI
- Mở phiên và resume: từ lúc chạy lệnh tới chữ đầu của câu trả lời
- Tin tới phiên đang rảnh, bộ nhớ, lỗi mở, lượt chạy hai lần sau kill
- Cùng máy, cùng lúc, đo xen kẽ cũ và mới từng vòng

=== page
@ Chương 3
^ Chặng 1: đo cách cũ
# Cửa sổ herdr, / *gõ vào pane.*
Mở agent trong cửa sổ như Hang đang làm, gõ lệnh vào pane, đọc màn hình mỗi 0,25 giây. Mỗi hãng 5 lần mở phiên, 3 lần resume, 1 lần kill giữa lượt.
### Thấy gì
- Antigravity hiện hộp «tin thư mục này không» 5 trên 5 lần
- Claude cách cũ hỏng 2 trên 5 lần mở khi máy tải cao
- Codex cần patch pane-nudge mới nhận tin lúc rảnh, sau 13 giây
~ old_way.py / *script đo*

=== cycle
@ Chương 4
^ Chặng 2 và 3: thiết kế và POC
# Holder giữ / *tiến trình agent.*
* Server có tin :: đẩy một lượt vào holder
* Holder :: gửi lượt vào stdin, đọc sự kiện ra
* Agent trả lời :: ack received, running, idle về server

=== page
@ Chương 5
^ Chặng 4: cũ so với mới
# Đo xen kẽ, / *cùng điều kiện.*
### Mở phiên mới, trung vị, n = 5 mỗi cách
<> | Cửa sổ + hook | Driver chung
<> Claude | 15,4 s (ra 3/5) | 3,5 s (5/5) | nhanh hơn 78%, 3/3 vòng
<> Codex | 9,7 s | 6,1 s | nhanh hơn 37%, 4/5 vòng
<> Antigravity | 8,1 s | 6,6 s | nhanh hơn 19%, 5/5 vòng
### Ngoài tốc độ
<> | Cửa sổ + hook | Driver chung
<> Tin tới phiên rảnh | 13 s Codex, không có đường Antigravity | 2 đến 3 s cả ba hãng
<> Hộp chặn mở phiên | 13% yêu cầu kẹt | 0 trên 15 lần
<>! Resume bằng tiến trình mới | Claude 7,8 s, Codex 6,3 s, Antigravity 5,0 s | Claude 3,8 s, Codex 6,5 s, Antigravity 6,1 s | không hơn tổng thể: giữ tiến trình sống, chỉ resume khi nó chết

=== page
@ Chương 6
^ Bài học và bước tiếp
# Không thiết kế / *quanh resume.*
### Bài học
- So hai cách phải cùng mốc và cùng lúc: số nháp đo hai mốc khác nhau suýt kết luận sai
- Lợi ích thật nằm ở đẩy được lượt lúc rảnh và bỏ hộp chặn, không ở tốc độ một lượt
### Bước tiếp
1. Antigravity qua holder ; cờ tắt mặc định, lùi về cửa sổ
2. Codex qua app-server ; khoá phiên bản giao thức
3. Đo trên MacBook, PC Master, Windows ; nhiều phiên song song, rảnh vài giờ
~ Bật theo cờ, / *giữ lối lùi*
