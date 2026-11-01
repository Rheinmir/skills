# vendor/ste-lint.py

Linter structural cho ASD-STE100, đóng gói NGUYÊN VĂN từ repo ngoài (owner 01/11: «áp chuẩn ASD-STE100 theo danyuchn/asd-ste100-skill»).

- Nguồn: https://github.com/danyuchn/asd-ste100-skill (scripts/ste-lint.py)
- Commit: f5493be06ff82799d90c24fb803457086506e996 (v0.4.0, 2026-11-01)
- Giấy phép: MIT, © 2026 Dustin Yuchen Teng (LICENSE-asd-ste100-skill.txt, sha256 d3c674e8592076c9021a59b55177adbcba6fd7e1710082becb922522b22ec672)
- sha256 ste-lint.py: 6e241c386dce17c7c8e7e7ceaf641420efb6126d2b79b14687bcea0d27da1ac4  (cũng ghim trong task_report.py: STE_SHA256)
- Không có từ điển ASD (ASD không cho phân phối lại): chỉ luật cấu trúc kiểm được.

## Quy tắc cập nhật
1. KHÔNG kéo tự động. Muốn lên commit khác: đọc lại diff của ste-lint.py, rồi đổi băm ở file này VÀ ở `STE_SHA256` trong task_report.py.
2. Selftest của /rp (`doc_report.py --selftest`, `task_report.py --selftest`) đỏ khi băm lệch hoặc khi tệp có subprocess, socket, urllib, requests, os.system, eval, exec, __import__.
3. Chỉ gọi hàm `lint(text, filename)` trên chữ cần kiểm. KHÔNG dùng `--fix`, KHÔNG ghi đè tệp của người dùng.
