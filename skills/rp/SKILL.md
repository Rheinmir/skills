---
name: rp
description: "Hub báo cáo (report) tình trạng Hang thành trang HTML đọc được trên điện thoại. Chế độ task: /rp task = báo cáo tình trạng các task (thread Issue/Epic đang mở, ai làm, giai đoạn, nhánh, sha Live, việc chờ owner), viết bằng book-layout. Gọi khi owner nói rp, báo cáo tình trạng task, tình hình các task, task đang tới đâu, hoặc /rp."
metadata:
  design-standard: "solid-what-how/1"
  contract-version: "1.0.0"
  loop: utils
---

# Skill: rp

Hub MỘT TÊN cho các báo cáo của Hang (owner 31/10: «báo cáo tình trạng các task đi», «lệnh là /rp»). Mỗi báo cáo là một chế độ ở `references/<chế độ>.md`. Hiện chỉ có chế độ `task`; thêm chế độ (vd tình trạng agent, tình trạng Live) = thêm tệp, không đổi hub này.

## WHAT

### Purpose và context
- **Purpose:** trả lời «các task đang tới đâu» bằng một trang HTML đọc được trên điện thoại, số liệu đọc thẳng từ Hang, mỗi dòng có id để kiểm lại.
- **Trigger (when to use):** owner gõ `/rp task`, hoặc nói «báo cáo tình trạng task», «tình hình các task», «task đang tới đâu». Không có chế độ đi kèm (`/rp` trơn) thì làm `task`.
- **Non-goals:** KHÔNG ghi gì lên Hang ngoài tin báo cáo; KHÔNG sửa, đóng hay giao lại thread; KHÔNG publish lên claude.ai Artifact (owner không mở được); KHÔNG tự đo smoke hay chạy test.

### Mental model
`hang_open_work (GET /work/open?room=vinh-hong, chỉ đọc) → task_report.py gom nhóm + lọc «cần chú ý» → markdown → book-layout (book.py + check.mjs) → HTML → gửi đính kèm`

### Input và output contract
| | Field | Required? | Ý nghĩa |
|---|---|---|---|
| In | máy đã nối Hang | có | `~/.hang/url` + `~/.hang/token` (script chỉ gửi token tới chính Hang đó, không in ra) |
| In | chế độ | không | `task` (mặc định) |
| Out | `rp-task-<ngày>-<giờ>.md` + `.html` | có | một trang bìa, tóm tắt, cần chú ý, từng nhóm trạng thái, trang «chưa đo» |
| Out | hai dòng `ok` của `check.mjs` | có | bằng chứng 1280 + 390: không tràn, đủ dấu |

### Rules và capabilities
- RULE-01 (MUST): chỉ ĐỌC Hang. Tin báo cáo là thứ duy nhất được ghi (gửi owner kèm tệp `.html`).
- RULE-02 (MUST): mỗi dòng của báo cáo mang id kiểm được (room, nhánh, sha, id yêu cầu mở lại); thứ không đo được ghi «chưa đo», không đoán, không điền.
- RULE-03 (MUST): không báo «xong» một việc khi dữ liệu chưa nói vậy: `deployed` false nghĩa là chưa lên Live; thread `review` là chờ review chứ không phải xong.
- RULE-04 (MUST): trang dựng bằng skill `book-layout` (nền sáng, không bảng markdown, danh sách), không viết HTML tay; owner đọc trên điện thoại.
- RULE-05 (MUST): không in token, không đưa token vào báo cáo hay tin gửi.
- Capabilities: chạy python3 và node; đọc `~/.hang`; gửi tin kèm tệp bằng `hang-room-hook send`.

### Failure boundaries
- Không đọc được Hang (`~/.hang/url`/`token` thiếu, mạng, 401/403) → **blocked**: nói đúng lỗi, không dựng báo cáo từ trí nhớ.
- Không có skill `book-layout` → **blocked**: cập nhật skills hoặc chạy từ checkout repo skills; không viết HTML thay.
- `check.mjs` HỎNG → sửa theo bảng nhánh của `book-layout` (tối đa 2 vòng), vẫn hỏng thì gửi kèm số đo và nói rõ.
- Hang trả ít hơn kỳ vọng (không thread nào mở) → báo cáo vẫn hợp lệ: «0 việc mở».

## HOW

### Main workflow
| Step | Type | Inputs | Action | Outputs/exit | Failure/next |
|---|---|---|---|---|---|
| W01 | deterministic | chế độ | chọn `references/<chế độ>.md` (mặc định `task`) rồi làm đúng các bước trong đó | — | chế độ lạ → liệt kê chế độ có |
| W02 | deterministic | Hang | `python3 scripts/task_report.py [--room vinh-hong] --out <thư mục> --build` | `.md` + `.html` | đọc lỗi → blocked |
| W03 | judgment | `.md` | đọc lướt: dòng nào mâu thuẫn dữ liệu thì sửa nguồn/ghi chú, không thêm số không có nguồn | `.md` đã soát | — |
| W04 | deterministic | `.html` | `node <book-layout>/scripts/check.mjs <tệp>.html` (macOS 13: `PW_CHANNEL=chrome`) | hai dòng `ok` | HỎNG → sửa 1 lần, lặp tối đa 2 |
| W05 | effect | `.html` | gửi owner kèm tệp: `sh ~/.hang/bin/hang-room-hook send owner "<2 dòng tóm tắt>" --file <tệp>.html --from $HANG_SESSION --agent claude-code --req <id tin owner> --reply <id tin owner>` | tin có link tệp | — |

### Branches
Không có nhánh phụ. Chế độ mới thêm bằng `references/<chế độ>.md` (cùng dạng bảng bước), không thêm nhánh ở hub.

### Validation và stopping
Xong khi: `task_report.py --selftest` in `ok`, `check.mjs` in hai dòng `ok`, và owner nhận được tệp `.html`. Mỗi báo cáo ghi giờ chốt ở bìa; chạy lại để cập nhật, không sửa tay số liệu.

### Examples
- **Positive:** owner gõ «/rp task» → script đọc 9 thread mở, ra báo cáo 7 trang → check.mjs ok 1280 + 390 → gửi tệp kèm hai dòng tóm tắt (số việc, việc cần chú ý số một).
- **Boundary/failure:** máy chưa nối Hang (không có `~/.hang/token`) → blocked, nói «chưa nối Hang trên máy này», không dựng báo cáo.

### Reference
- `references/task.md`: chế độ `task` (nguồn số liệu, cách gom nhóm, cách đọc «cần chú ý», giới hạn).
- `scripts/task_report.py`: đọc `GET /work/open` → markdown cho `book-layout`; `--selftest`.
