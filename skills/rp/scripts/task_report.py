#!/usr/bin/env python3
"""rp task: đọc trạng thái các task của Hang (chỉ ĐỌC GET /work/open) rồi sinh markdown cho skill book-layout.

  python3 task_report.py [--room vinh-hong] [--out DIR] [--src work-open.json] [--build] [--now UNIX]
  python3 task_report.py --selftest

Nguồn: GET <HANG_URL>/work/open?room=<phòng> (cùng dữ liệu tool MCP hang_open_work; mặc định vinh-hong, không kèm room thì Hang gộp mọi phòng gốc token máy thấy) với Bearer token máy ở ~/.hang/token; --src đọc tệp JSON thay cho mạng.
Không ghi gì lên Hang, không in token. Mỗi dòng báo cáo mang id thread (room), req hoặc nhánh làm bằng chứng; thứ không đo được ghi «chưa đo».
MÀU (owner 31/10: «tick xanh là tui hiểu xong hết rồi hả»): xanh lá CHỈ khi việc thật sự xong (đã lên Live). Việc đang làm, chờ, chậm, chết, chưa bắt đầu KHÔNG BAO GIỜ xanh lá.
Không dùng danh sách «- chữ» của book-layout (dấu tích xanh trước MỌI dòng, đọc thành «xong») và không dùng chữ nhấn «*…*» (book-layout tô nó XANH LÁ). Mỗi dòng là một đoạn văn mở đầu bằng chấm màu tính từ dữ liệu.
Python 3.9, chỉ stdlib."""
from __future__ import annotations

import argparse, base64, json, os, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOM = "vinh-hong"   # phòng gốc mặc định; tên hiển thị lấy từ chính tham số, không gõ cứng ở brand/footer
PER_PAGE = 4   # thread mỗi trang: book-layout muốn ≤ 120 chữ mỗi trang
QUIET = 2 * 3600   # đang làm mà im quá mức này → vàng
STALE = 12 * 3600   # đang làm mà im quá mức này → đỏ
# (khoá, chấm, nhãn, nghĩa) theo thứ tự hiện trong báo cáo
COLORS = (("red", "🔴", "Đỏ", "cần xử lý: agent đã chết, hoặc bị chặn, hoặc đang làm mà im hơn 12 giờ"),
          ("yellow", "🟡", "Vàng", "chậm hoặc đang chờ: chờ owner, chờ review, đợi việc khác, im quá 2 giờ"),
          ("blue", "🔵", "Xanh dương", "đang làm bình thường (chưa xong)"),
          ("gray", "⚪", "Xám", "chưa bắt đầu (backlog, xếp hàng)"),
          ("green", "🟢", "Xanh lá", "XONG: đã lên Live. Chỉ màu này mới là xong"))
HEX = {"red": "#c0392b", "yellow": "#e0a800", "blue": "#2f6fb5", "gray": "#9aa0a6", "green": "#3b7a2a"}   # màu thanh ở bìa: đậm, phẳng, không pastel
DOT = {k: d for k, d, _, _ in COLORS}
LABEL = {k: n for k, _, n, _ in COLORS}


def hang_home():
    return Path(os.environ.get("HANG_HOME") or Path.home() / ".hang")


def get(url, tok):
    rq = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok, "User-Agent": "hang-rp/1"})   # UA mặc định của urllib bị cổng công khai từ chối (403)
    with urllib.request.urlopen(rq, timeout=30) as r:
        return json.load(r)


def fetch(room):
    home = hang_home()
    url = (home / "url").read_text().strip().rstrip("/")
    tok = (home / "token").read_text().strip()
    q = urllib.parse.quote(room)
    if get(f"{url}/rooms/{q}?limit=1", tok).get("room") is None:   # /work/open?room=<tên sai> trả 0 việc mà không báo lỗi: tên phòng sai không được thành «0 việc mở»
        sys.exit(f"blocked: phòng «{room}» không có trên Hang (kiểm tên phòng với hang_rooms)")
    return get(f"{url}/work/open?room={q}", tok)


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


def judge(t):
    """(màu, [lý do]) của một thread, chỉ từ dữ liệu của chính thread. Xanh lá cần bằng chứng «xong» (deployed); không có bằng chứng thì không bao giờ xanh lá."""
    idle, st = t.get("idle") or 0, t.get("status")
    red, yel = [], []
    for d in t.get("down") or []:
        red.append(f"{d.get('name') or 'agent'} đã chết ({d.get('health')}), mở lại: {d.get('reopen') or 'chưa có yêu cầu mở lại'}")
    if st in ("blocked", "failed"):
        red.append("giai đoạn " + st)
    if st == "in_progress" and idle > STALE:
        red.append(f"đang làm mà im {ago(idle)}")
    if t.get("owner_wait"):
        yel.append("chờ owner trả lời")
    for b in t.get("blocking") or []:
        yel.append("chờ: " + short(str(b).split(" («")[0], 70))   # bỏ phần liệt kê tên việc trong ngoặc: dài và đã có ở thread kia
    if st == "review":
        yel.append("chờ review")
    if st == "in_progress" and QUIET < idle <= STALE:
        yel.append(f"đang làm mà im {ago(idle)}")
    if t.get("deployed") and not red and not yel:
        return "green", ["đã lên Live"]
    if red:
        return "red", red + yel
    if yel:
        return "yellow", (["đã lên Live"] if t.get("deployed") else []) + yel   # đã lên Live mà còn chờ owner / việc khác: chưa phải xong
    if st in ("backlog", "queued"):
        return "gray", ["chưa bắt đầu"]   # người làm hiện ở cột riêng của dòng, không lặp ở lý do
    if st == "in_progress":
        return "blue", [f"đang làm, tin cuối {ago(idle)} trước"]
    return "gray", [f"giai đoạn {st or 'không rõ'}"]


def line(t, color, why):
    who = ", ".join(f"{w.get('name') or str(w.get('agent'))[:8]} ({w.get('status')})" for w in t.get("workers") or []) or "chưa có người làm"
    bits = [f"{DOT[color]} {short(t.get('name'))}", "; ".join(why), f"người làm: {who}", f"nhánh: {t.get('branch') or 'chưa có'}", f"im {ago(t.get('idle') or 0)}", f"room:{t.get('room')}"]
    return "; ".join(bits)   # một đoạn văn thường: không «- » (tick xanh), không **đậm** (dòng danh sách là flex)


def cover_svg(n):
    """Hình bìa: thanh ngang số việc theo màu (thay tranh núi xanh lá mặc định của book-layout: xanh lá ở bìa đọc như «ổn»/«xong»). Thanh dài theo số việc; 0 việc thì chỉ còn khung rỗng."""
    top, mx, rows = 42, max(max(n.values()), 1), []
    for i, (k, _, label, _) in enumerate(COLORS):
        y, w = top + i * 40, round(n[k] / mx * 170)
        rows.append(f'<text x="14" y="{y + 19}" font-size="17" fill="#3d3d3a">{label}</text>'
                    f'<rect x="136" y="{y}" width="206" height="26" rx="4" fill="none" stroke="#c9c9c2"/>'
                    + (f'<rect data-c="{k}" x="136" y="{y}" width="{max(w + 36, 36)}" height="26" rx="4" fill="{HEX[k]}"/>' if n[k] else "")
                    + f'<text x="356" y="{y + 20}" font-size="20" font-weight="700" fill="#1d1d1b">{n[k]}</text>')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 260" font-family="Be Vietnam Pro, Helvetica Neue, Helvetica, Arial, sans-serif">'   # ảnh SVG không tải được web font: lùi về sans hệ thống, không để rơi vào font có chân
           '<rect width="400" height="260" fill="#fbfaf6"/><text x="14" y="26" font-size="15" fill="#6b6b66">Số việc theo màu</text>' + "".join(rows) + "</svg>")
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def build_md(d, now, room=ROOM):   # room=None: nguồn là tệp JSON, không biết phòng nào → không ghi tên phòng, không khẳng định «ngoài phòng X không có»
    ts = sorted(d.get("open") or [], key=lambda t: t.get("opened") or 0)
    running = str(d.get("running") or "")
    rows = [(t, *judge(t)) for t in ts]
    n = {k: sum(1 for _, c, _ in rows if c == k) for k, *_ in COLORS}
    stamp = time.strftime("%d/%m/%Y %H:%M", time.localtime(now))
    o = ["---", "title: Báo cáo tình trạng task", f"brand: Hang · {room}" if room else "brand: Hang", f"date: {stamp}", "vol: Báo cáo",
         f"footer: nguồn hang_open_work{f' room={room}' if room else ' (tệp)'} · Live {running[:7] or 'chưa biết'}", "---",
         "=== cover", "^ Tình trạng task", f"# {len(ts)} việc mở / {n['green']} xong.",
         f"> Chốt lúc {stamp}. Số liệu đọc thẳng từ Hang. Màu chỉ nói ĐÚNG tình trạng: xanh lá mới là xong.", "---",
         "![Số việc theo màu: " + ", ".join(f"{LABEL[k].lower()} {n[k]}" for k, *_ in COLORS) + f"]({cover_svg(n)})", "",
         "=== page", "@ Chú giải", "# Chú giải / màu", "---"]
    o += [f"{DOT[k]} {LABEL[k]}: {meaning}" for k, _, _, meaning in COLORS] + [""]
    o += ["=== page", "@ Tóm tắt", "# Tóm tắt / một trang", "---", f"! {n['green']} | việc đã xong trong {len(ts)} việc đang mở" + (f" | room:{room}, hang_open_work" if room else " | hang_open_work")]
    o += [f"{DOT[k]} {LABEL[k]}: {n[k]} việc" for k, *_ in COLORS if n[k]] + [f"Sha đang chạy trên Live: {running[:12] or 'chưa biết'}", ""]
    for k, dot, label, _ in COLORS:
        grp = [(t, w) for t, c, w in rows if c == k]
        for i in range(0, len(grp), PER_PAGE):
            o += ["=== page", f"@ {label}", f"# {label}" + (" / tiếp" if i else ""), "---"]
            o += [line(t, k, w) for t, w in grp[i:i + PER_PAGE]] + [""]
    o += ["=== page", "@ Chưa đo", "# Chưa đo / và giới hạn", "---",
          "Kết quả smoke mới nhất của Live: chưa đo (báo cáo này không có nguồn đọc smoke).",
          "Sha từng nhánh đang review: chưa đo (hang_open_work chỉ cho tên nhánh, không cho sha).",
          "«Xong» lấy từ cờ deployed của thread, không phải từ so sánh sha: thread chưa có cờ thì không bao giờ ra xanh lá.",
          "Màu theo giai đoạn mà /work/open trả, chưa đọc giai đoạn trong sổ vòng đời: một việc đã được review ĐẠT trong sổ vẫn có thể hiện xám hoặc vàng «chờ review» ở đây (đọc thêm giai đoạn sổ để sau).",
          "Thread đã đóng không có trong báo cáo" + (f"; việc ngoài phòng {room} cũng không." if room else "; phạm vi phòng của tệp nguồn: chưa đo."),
          "~ Chưa đo thì ghi / chưa đo.", ""]
    return "\n".join(o)


def selftest():
    now = 1793431800
    T = lambda room, status, idle=60, **k: {"room": room, "name": "Việc " + room, "status": status, "idle": idle, "opened": len(room), "workers": [{"name": "Kai", "status": status}], **k}
    cases = (("agent chết", T("a", "in_progress", down=[{"name": "Kai", "health": "dead", "reopen": "s123"}]), "red", "Kai đã chết (dead), mở lại: s123"),
             ("bị chặn", T("b", "blocked"), "red", "giai đoạn blocked"),
             ("im quá 12 giờ", T("c", "in_progress", idle=13 * 3600), "red", "đang làm mà im 13 giờ"),
             ("im quá 2 giờ", T("d", "in_progress", idle=3 * 3600), "yellow", "đang làm mà im 3 giờ"),
             ("chờ owner", T("e", "in_progress", owner_wait=True), "yellow", "chờ owner trả lời"),
             ("chờ review", T("f", "review"), "yellow", "chờ review"),
             ("đợi việc khác", T("g", "in_progress", blocking=["Kai còn việc khác chờ («Việc x»)"]), "yellow", "chờ: Kai còn việc khác chờ"),
             ("backlog", T("h", "backlog", workers=[]), "gray", "chưa bắt đầu"),
             ("đang làm ổn", T("i", "in_progress", idle=300), "blue", "đang làm, tin cuối 5 phút"),
             ("đã lên Live", T("j", "done", deployed=True), "green", "đã lên Live"),
             ("deployed mà vẫn chờ review", T("n", "review", deployed=True), "yellow", "chờ review"),
             ("đã lên Live nhưng agent chết", T("k", "review", deployed=True, down=[{"name": "Kai", "health": "dead"}]), "red", "đã chết"),
             ("đã lên Live nhưng còn chờ owner", T("m", "review", deployed=True, owner_wait=True), "yellow", "chờ owner trả lời"),
             ("deployed false không xanh lá", T("l", "review", deployed=False), "yellow", "chờ review"))
    for name, t, want, why in cases:
        c, w = judge(t)
        assert c == want and any(why in x for x in w), (name, c, w)
    fx = {"running": "c031e2312e03ebc2974b9672daee8cecbf5498e3", "open": [c[1] for c in cases]}
    md = build_md(fx, now)
    assert "# 14 việc mở / 1 xong." in md, md[:400]
    assert not [ln for ln in md.splitlines() if ln.startswith("- ")], "còn danh sách «- » (tick xanh)"
    assert "*" not in md, "còn chữ nhấn «*…*» (book-layout tô xanh lá)"   # ngoài dòng 🟢 cũng không có «*»   # book-layout vẽ tick xanh trước mọi dòng «- »
    import re
    m = re.search(r"!\[Số việc theo màu: ([^\]]+)\]\(data:image/svg\+xml;base64,([^)]+)\)", md)
    assert m, "bìa thiếu hình thanh số việc theo màu"
    svg = base64.b64decode(m.group(2)).decode()
    assert all(f'data-c="{k}"' in svg for k in ("red", "yellow", "blue", "gray", "green")), svg[:200]   # fx có đủ năm màu
    assert 'data-c="green"' not in cover_svg({"red": 2, "yellow": 1, "blue": 0, "gray": 0, "green": 0}) and 'data-c="blue"' not in cover_svg({"red": 2, "yellow": 1, "blue": 0, "gray": 0, "green": 0})   # 0 việc: không thanh (khung rỗng), nhất là xanh lá
    assert "xanh lá 0" in build_md({"open": [], "running": ""}, now) and "núi" not in md
    greens = [ln for ln in md.splitlines() if ln.startswith("🟢 ") and "room:" in ln]
    assert len(greens) == 1 and "room:j" in greens[0], greens   # đúng MỘT dòng việc xanh lá (việc đã lên Live)
    assert "xanh lá mới là xong" in md and "Chỉ màu này mới là xong" in md
    for k in ("room:a", "room:h", "Sha đang chạy trên Live: c031e2312e03", "chưa đo"):
        assert k in md, k
    assert "brand: Hang · vinh-hong" in md and "room=vinh-hong" in md and "ngoài phòng vinh-hong" in md
    mt = build_md(fx, now, None)   # --src: không biết phòng
    assert "brand: Hang\n" in mt and "ngoài phòng" not in mt and "chưa đo" in mt and "vinh-hong" not in mt
    md2 = build_md(fx, now, "phong-khac")
    assert "brand: Hang · phong-khac" in md2 and "vinh-hong" not in md2   # tên phòng đi theo tham số, không gõ cứng
    e = build_md({"open": [], "running": ""}, now)
    assert "0 xong." in e and e.count("=== page") >= 3
    print("task_report selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--room", default=ROOM, help="phòng gốc cần báo cáo (mặc định vinh-hong)")
    ap.add_argument("--out", default=".", help="thư mục ghi rp-task-<giờ>.md")
    ap.add_argument("--src", help="đọc JSON này thay cho GET /work/open")
    ap.add_argument("--now", type=int, help="giờ unix (cho test)")
    ap.add_argument("--build", action="store_true", help="chạy book.py của skill book-layout để ra .html")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    now = a.now or int(time.time())
    d = json.loads(Path(a.src).read_text(encoding="utf-8")) if a.src else fetch(a.room)
    room = None if a.src else a.room
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    md = out / ("rp-task-" + time.strftime("%Y%m%d-%H%M", time.localtime(now)) + ".md")
    md.write_text(build_md(d, now, room), encoding="utf-8")
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
