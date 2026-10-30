---
title: Sổ tay Hang
brand: Sổ tay Hang
date: Tháng 10, 2026
vol: Tập 1
---
=== cover
^ Mỗi phiên một dấu vết
# Giữ lại / *mọi phiên.*
> Kho chỉ-thêm cho code và hội thoại của mọi agent, trên mọi máy của bạn.
---

=== toc
@ Mục lục
# Có gì / bên trong
---
01 | Vì sao cần kho chỉ-thêm | Không gì bị ghi đè, mọi bản đều lấy lại được. | 06
02 | Phòng và agent | Người gõ một câu, Hang giao đúng người. | 24
03 | Việc nhỏ, đổi lớn | Mỗi lần báo XONG kèm một sha và một số đo. | 42
04 | Khi máy rớt mạng | Watcher tự nối lại, phiên giữ nguyên. | 60
05 | Kế hoạch của bạn | Năm bước để nối máy mới trong mười phút. | 78

=== page
@ Chương 1
^ Chương 1
# Vì sao cần / kho chỉ-thêm
> Agent làm nhanh hơn người đọc lại. Thứ duy nhất không được mất là lịch sử.
---
Một lệnh **reset** nhầm, một bộ cài ghi đè skill, một phiên hết context giữa chừng: chuyện xảy ra mỗi tuần.
" Thứ gì đã ghi thì không bao giờ phải viết lại lần hai. -- Luật chỉ-thêm của Hang

=== cycle
* Gõ tin :: Người viết một câu trong phòng.
* Hang giao :: Đúng người, đúng máy.
* Agent làm :: Báo XONG kèm sha và số đo.

=== page
@ Chương 2
# Phòng / và agent
> Giao việc bằng một câu (khỏi phải nhớ ai đang rảnh).
---
Mỗi phòng có một điều phối và vài worker. Hang ghi lại ai nhận việc gì và tự đóng Issue khi bản mới đã lên.
! 325 | phiên agent trong bảy ngày, mỗi phiên đều đọc lại được. | Đo trên Mac mini, 30/10

=== page
@ Chương 2
### Bốn cách giữ phòng gọn gàng
* Mỗi việc một thread :: Issue riêng cho từng lỗi.
* Tin ngắn, mỗi ý một dòng :: Nhãn trước: XONG, Cần quyết, Hỏi.
* Bằng chứng trước lời nói :: Test đỏ rồi xanh, GIF bấm thật, sha.
* Phiên cũ tắt hẳn :: Chuyển phiên khi context đầy.
~ Phòng gọn là / *phòng chạy nhanh.*

=== image
# Tiến bộ, / không hoàn hảo.
> Mỗi lần ghép nhỏ, smoke xanh, rồi mới tới bước kế.

=== page
@ Chương 3
# Việc nhỏ, / *đổi lớn*
> Sức mạnh của những lần ghép nhỏ.
---
Một nhánh nhỏ, một test đỏ rồi xanh, một trang concept: lặp lại đủ lâu thì thành nền vững.
### Thử ngay
- Bắt đầu bằng một test đỏ.
- Sửa ít nhất có thể cho nó xanh.
- Báo XONG kèm đúng một sha.
~ Nhánh nhỏ, / *review nhanh.*
