---
type: eval
id: book-layout-casestudy
query: "báo cáo patch triển khai có so với cách cũ"
expected: [book-layout]
---

# skill-resolve golden: book-layout (case-study)

Tài liệu giải thích một thay đổi, có so sánh cũ / mới, phải phân giải về book-layout (design mặc định của mọi tài liệu), không về docs-site-macos hay md-to-html.
Câu cố ý không có chữ «tài liệu» / «tạp chí»: với mô tả cũ (d070e51) h@3 ✗ (→ tidy, surface-coverage, harness-update), với mô tả mới h@1 ✓. Đổi ngược mô tả thì ca này đỏ.

## Origin
Owner 30/10 (Hang, phòng Vịnh Hồng): mọi tài liệu theo một design = khuôn book-layout + cách viết case-study của bài uxdesign.cc.
