# Mẫu báo cáo: một mục `###` cho mỗi thành phần, trong `parts/*.md`

Mỗi demo `demos/<id>.html` cần một mục cùng tên. Tên tệp `parts/*.md` tuỳ ý (gom vài chục mục một tệp là vừa).
Các trường đọc được viết in đậm hoặc không (`- **Trạng thái:**` hay `- Trạng thái:`); trường không có thì bỏ qua.

## Thành phần trong danh mục Name That UI (demo `N-slug.html`)

Tiêu đề bắt đầu bằng số thứ tự trong `references/catalogue.md`:

```md
### 12. Segmented Control — `macos/segmented-control`
- **Trạng thái:** ✅ Có            (✅ có đủ · 🟡 một phần · ❌ không có)
- **Tên trong code:** `.tabs-toggle`, `SegmentedControl`
- **Tên gọi khác:** tab pill, toggle group
- **Định nghĩa:** `assets/app.css:812`, `src/ui/Segmented.tsx:8`
- **Nơi dùng:** trang Pricing, trang Settings
- **Biến thể:** hai cỡ (sm, md); có icon hoặc chỉ chữ
- **Code mẫu:** `assets/app.css:812-840`
```css
.tabs-toggle { display: inline-flex; padding: 3px; border-radius: 10px; }
```
- **Ghi chú refactor:**
  - điều cần sửa khi làm lại
```

## Thành phần riêng của trang (demo `x-slug.html`)

Tiêu đề là tên chuẩn; `slug(tên)` phải trùng phần sau `x-` của tệp demo
(ví dụ `### Pricing Card` ↔ `demos/x-pricing-card.html`):

```md
### Pricing Card
- Nhóm: Bán hàng
- Mô tả: thẻ giá một gói: tên gói, giá theo tháng, danh sách quyền lợi và nút mua; gói nổi bật có viền màu.
- Tên trong code: `.plan-card`, `.plan-card--featured`
- Tên gọi khác: plan card, price tier
- Định nghĩa: `assets/app.css:1204`
- Biến thể: thường, nổi bật, đang dùng
- Trạng thái: ✅ Có

`assets/app.css:1204-1230`
```css
.plan-card { border: 1px solid var(--line); border-radius: 16px; padding: 24px; }
```
```

Câu đầu của **Mô tả** trở thành dòng "Map khi…" trong ontology, nên viết nó như cách người ta *nhận ra* thành phần
(hình dạng, vị trí, hành vi), không phải cách nó được code.
