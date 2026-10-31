#!/usr/bin/env python3
"""rp task: đọc trạng thái các task của Hang (chỉ ĐỌC GET /work/open) rồi sinh markdown cho skill book-layout.

  python3 task_report.py [--out DIR] [--src work-open.json] [--build] [--now UNIX]
  python3 task_report.py --selftest

Nguồn: GET <HANG_URL>/work/open (cùng dữ liệu tool MCP hang_open_work) với Bearer token máy ở ~/.hang/token; --src đọc tệp JSON thay cho mạng.
Không ghi gì lên Hang, không in token. Mỗi dòng báo cáo mang id thread (room), req hoặc nhánh làm bằng chứng; thứ không đo được ghi «chưa đo».
Python 3.9, chỉ stdlib."""
from __future__ import annotations

import argparse, json, os, subprocess, sys, time, urllib.request
from pathlib import Path

PER_PAGE = 4   # thread mỗi trang: book-layout muốn ≤ 120 chữ mỗi trang
STAGES = (("blocked", "Bị chặn"), ("in_progress", "Đang làm"), ("review", "Chờ review"), ("queued", "Xếp hàng"), ("backlog", "Backlog"))
QUIET = 2 * 3600   # thread đang làm mà im quá mức này thì đưa vào «cần chú ý»


def hang_home():
    return Path(os.environ.get("HANG_HOME") or Path.home() / ".hang")


def fetch():
    home = hang_home()
    url = (home / "url").read_text().strip().rstrip("/")
    tok = (home / "token").read_text().strip()
    rq = urllib.request.Request(url + "/work/open", headers={"Authorization": "Bearer " + tok, "User-Agent": "hang-rp/1"})   # UA mặc định của urllib bị cổng công khai từ chối (403)
    with urllib.request.urlopen(rq, timeout=30) as r:
        return json.load(r)


def ago(sec):
    sec = max(0, int(sec))
    if sec < 90:
        return "vừa xong"
    if sec < 5400:
        return f"{round(sec / 60)} phút"
    if sec < 2 * 86400:
        return f"{round(sec / 3600)} giờ"
    return f"{round(sec / 86400)} ngày"


def short(s, n=64):
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def attention(t):
    """Lý do thread cần người nhìn, mỗi lý do kèm bằng chứng nằm ngay trong dữ liệu thread."""
    out = []
    if t.get("owner_wait"):
        out.append("chờ owner trả lời")
    for d in t.get("down") or []:
        out.append(f"{d.get('name') or 'agent'} đã chết ({d.get('health')}), mở lại: {d.get('reopen') or 'chưa có yêu cầu mở lại'}")
    for b in t.get("blocking") or []:
        out.append("bị chặn: " + short(str(b).split(" («")[0], 70))   # bỏ phần liệt kê tên việc trong ngoặc: dài và đã có ở thread kia
    if t.get("status") == "in_progress" and (t.get("idle") or 0) > QUIET:
        out.append(f"đang làm mà im {ago(t['idle'])}")
    return out


def line(t):
    who = ", ".join(f"{w.get('name') or str(w.get('agent'))[:8]} ({w.get('status')})" for w in t.get("workers") or []) or "chưa có người làm"
    bits = [short(t.get("name")), f"người làm: {who}", f"nhánh: {t.get('branch') or 'chưa có'}",
            "đã lên Live" if t.get("deployed") else "chưa lên Live", f"im {ago(t.get('idle') or 0)}", f"room:{t.get('room')}"]
    return "- " + "; ".join(bits)   # không **đậm** và không « · »: dòng danh sách của book-layout là flex, mỗi đoạn thành một ô và chữ rớt từng từ ở 390 px


def build_md(d, now):
    ts = sorted(d.get("open") or [], key=lambda t: t.get("opened") or 0)
    running = str(d.get("running") or "")
    by = {k: [t for t in ts if t.get("status") == k] for k, _ in STAGES}
    other = [t for t in ts if t.get("status") not in by]
    att = [(t, r) for t in ts for r in attention(t)]
    dead = sum(len(t.get("down") or []) for t in ts)
    stamp = time.strftime("%d/%m/%Y %H:%M", time.localtime(now))
    o = ["---", "title: Báo cáo tình trạng task", "brand: Hang · Vịnh Hồng", f"date: {stamp}", "vol: Báo cáo", f"footer: nguồn hang_open_work · Live {running[:7] or 'chưa biết'}", "---",
         "=== cover", "^ Tình trạng task", f"# {len(ts)} việc mở / *{len(by['in_progress'])} đang làm.*",
         f"> Chốt lúc {stamp}. Số liệu đọc thẳng từ Hang, không ước lượng; mục chưa đo ghi rõ ở trang cuối.", "---", "",
         "=== page", "@ Tóm tắt", "# Tóm tắt / *một trang*", "---"]
    o += [f"! {len(ts)} | thread Issue/Epic đang mở | room:vinh-hong, hang_open_work"]
    o += [f"- {label}: {len(by[k])}" for k, label in STAGES if by[k]] + ([f"- Trạng thái khác: {len(other)}"] if other else [])
    o += [f"- Agent đã chết trong các thread mở: {dead}", f"- Sha đang chạy trên Live: {running[:12] or 'chưa biết'}", ""]
    if att:
        o += ["=== page", "@ Cần chú ý", "# Cần / *chú ý*", "---"]
        for i in range(0, len(att), 4):
            if i:
                o += ["", "=== page", "@ Cần chú ý", "### Tiếp"]
            o += [f"- {short(t.get('name'), 48)}: {r}; room:{t.get('room')}" for t, r in att[i:i + 4]]
        o.append("")
    for k, label in STAGES + (("_other", "Khác"),):
        items = by.get(k) if k != "_other" else other
        for i in range(0, len(items or []), PER_PAGE):
            o += ["=== page", f"@ {label}", f"# {label}" + (" / *tiếp*" if i else ""), "---"]
            o += [line(t) for t in items[i:i + PER_PAGE]] + [""]
    o += ["=== page", "@ Chưa đo", "# Chưa đo / *và giới hạn*", "---",
          "- Kết quả smoke mới nhất của Live: chưa đo (báo cáo này không có nguồn đọc smoke).",
          "- Sha từng nhánh đang review: chưa đo (hang_open_work chỉ cho tên nhánh, không cho sha).",
          "- «Đã lên Live» lấy từ cờ deployed của thread, không phải từ so sánh sha.",
          "- Thread đã đóng không có trong báo cáo; việc ngoài phòng Vịnh Hồng cũng không.",
          "~ Chưa đo thì ghi / *chưa đo.*", ""]
    return "\n".join(o)


def selftest():
    now = 1793431800
    fx = {"running": "c031e2312e03ebc2974b9672daee8cecbf5498e3", "open": [
        {"room": "a-1", "name": "Việc A", "status": "in_progress", "idle": 10800, "branch": "x/a", "deployed": False,
         "workers": [{"name": "Kai", "status": "in_progress"}], "down": [{"name": "Kai", "health": "dead", "reopen": "s123"}], "opened": 1},
        {"room": "b-2", "name": "Việc B", "status": "review", "idle": 120, "deployed": True, "workers": [], "owner_wait": True, "opened": 2},
        {"room": "c-3", "name": "Việc C", "status": "backlog", "idle": 100000, "workers": [], "blocking": ["Kai còn việc khác chờ"], "opened": 3}]}
    md = build_md(fx, now)
    for want in ("# 3 việc mở / *1 đang làm.*", "room:a-1", "Kai đã chết (dead), mở lại: s123", "chờ owner trả lời", "đang làm mà im 3 giờ",
                 "bị chặn: Kai còn việc khác chờ", "Sha đang chạy trên Live: c031e2312e03", "chưa đo", "nhánh: chưa có", "chưa lên Live", "đã lên Live"):
        assert want in md, want
    assert "```" not in md and "|" not in md.split("=== page", 1)[1].split("---", 1)[0]   # không bảng markdown
    assert build_md({"open": [], "running": ""}, now).count("=== page") >= 2
    print("task_report selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=".", help="thư mục ghi rp-task-<giờ>.md")
    ap.add_argument("--src", help="đọc JSON này thay cho GET /work/open")
    ap.add_argument("--now", type=int, help="giờ unix (cho test)")
    ap.add_argument("--build", action="store_true", help="chạy book.py của skill book-layout để ra .html")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    now = a.now or int(time.time())
    d = json.loads(Path(a.src).read_text(encoding="utf-8")) if a.src else fetch()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    md = out / ("rp-task-" + time.strftime("%Y%m%d-%H%M", time.localtime(now)) + ".md")
    md.write_text(build_md(d, now), encoding="utf-8")
    print(md)
    if a.build:
        here = Path(__file__).resolve()
        cands = [here.parents[2] / "book-layout" / "scripts" / "book.py", Path.home() / ".claude/skills/book-layout/scripts/book.py", Path.home() / ".agents/skills/book-layout/scripts/book.py"]
        bk = next((c for c in cands if c.is_file()), None)
        if not bk:
            sys.exit("blocked: không thấy skill book-layout (cập nhật skills hoặc chạy từ checkout repo skills)")
        html = md.with_suffix(".html")
        subprocess.run([sys.executable, str(bk), str(md), "-o", str(html)], check=True)
        print(html)


if __name__ == "__main__":
    main()
