# `meta.json` trong thư mục inventory

`capture.mjs` tạo sẵn một bản; sửa tay sau đó (nó không bị ghi đè).

```json
{
  "product": "Acme",                    // tên sản phẩm: tiêu đề tab, prompt cho agent, ontology
  "wordmark": "Acme.",                  // logo chữ trên header (mặc định: từ đầu của product + ".")
  "title": "Thành phần này tên là gì",   // tiêu đề hero (luôn kết bằng dấu ? tô màu)
  "lede": "…",                          // câu dưới tiêu đề hero
  "css": "site.css",                    // CSS đã biên dịch của trang; được phép một dấu *: "../dist/assets/styles-*.css"
  "fontsDir": "fonts",                  // nơi tìm tệp .woff2 mà site.css trỏ tới (để nhúng vào file)
  "fontKeep": "(latin|latin-ext|vietnamese)",  // chỉ nhúng các subset font này
  "skins": [{ "id": "light", "name": "Sáng" }], // giá trị data-skin trang hỗ trợ; [] thì ẩn nút Skin
  "skinAttr": "data-theme",              // thuộc tính trên <html> mà theme của trang đọc (mặc định data-skin)
  "stageBg": "var(--aw-bg-primary)",     // biến nền trang của site: nền sân khấu bản xem trước theo theme (mặc định var(--color-app))
  "defaultSkin": "light",
  "houseFont": "Lexend Deca Light",     // font chuẩn, nhắc trong quy tắc map và prompt
  "ownLabel": "Riêng app",              // tên tab cho các thành phần ngoài danh mục
  "frames": {                           // các khung ở hero; null thì không có khung
    "desktop": { "ids": ["x-app-shell"], "cap": "Desktop 1440 × 900 (thu nhỏ) · khung app", "url": "acme.com" },
    "phones": [
      { "ids": ["x-inbox", "x-composer"], "cap": "Điện thoại 390 × 844 · hộp thư" },
      { "ids": ["x-onboarding"], "cap": "Điện thoại 390 × 844 · làm quen" }
    ]
  }
}
```

(Chú thích `//` ở trên chỉ để đọc; tệp thật là JSON thuần.)
