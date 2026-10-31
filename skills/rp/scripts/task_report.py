#!/usr/bin/env python3
"""rp task: đọc trạng thái các task của Hang (chỉ ĐỌC GET /work/open) rồi sinh báo cáo HTML song ngữ (EN mặc định, nút VI) qua skill book-layout.

  python3 task_report.py [--room vinh-hong] [--out DIR] [--src work-open.json] [--build] [--now UNIX]
  python3 task_report.py --selftest

Nguồn: GET <HANG_URL>/work/open?room=<phòng> (cùng dữ liệu tool MCP hang_open_work; mặc định vinh-hong, không kèm room thì Hang gộp mọi phòng gốc token máy thấy) với Bearer token máy ở ~/.hang/token; --src đọc tệp JSON thay cho mạng.
Không ghi gì lên Hang, không in token. Mỗi việc mang id thread (room), req hoặc nhánh làm bằng chứng; thứ không đo được ghi «chưa đo».
MÀU (owner 31/10: «tick xanh là tui hiểu xong hết rồi hả»): xanh lá CHỈ khi việc thật sự xong (đã lên Live). Việc đang làm, chờ, chậm, chết, chưa bắt đầu KHÔNG BAO GIỜ xanh lá.
THOÁNG (owner 31/10): mỗi việc là một thẻ (tiêu đề một dòng + 1–3 dòng ngắn), mỗi dòng ≤ 20 chữ; không «- » (tích xanh), không «*…*» (xanh lá).
SONG NGỮ (owner 31/10: «viết bằng tiếng Anh chuẩn hàng không… sẵn 1 nút dịch tiếng Việt, không qua token Claude»): mọi câu do mã sinh nằm MỘT nơi, bảng TX (EN, VI). EN viết theo mẫu ASD-STE100, chỉ KIỂM CƠ HỌC bằng ste_problems(), KHÔNG phải chứng nhận STE.
Trong markdown mỗi câu là «⟦EN¦VI⟧», tên việc là «⟪tên⟫»; sau book.py, finish() đổi thành <span class=en>/<span class=vi> và thêm nút. Nút không gọi mạng.
Tên việc (tiếng Việt do người đặt) giữ nguyên; chỉ khi trình duyệt có Translator API và người xem BẤM nút «Translate task names» thì dịch trên máy, không gửi chữ ra ngoài.
Python 3.9, chỉ stdlib."""
from __future__ import annotations

import argparse, base64, html as htmllib, json, os, re, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOM = "vinh-hong"   # phòng gốc mặc định; tên hiển thị lấy từ chính tham số, không gõ cứng ở brand/footer
PER_PAGE = 2   # thẻ mỗi trang: thoáng (book-layout muốn ≤ 120 chữ mỗi trang)
CAP = 20   # chữ tối đa mỗi dòng văn (owner 31/10: m1a19291cd4a58d3 «10-25», rồi m1a192aae03f1e9c «10-20 thôi, 25 vẫn dài»); VI đếm theo khoảng trắng (mỗi âm tiết một chữ)
QUIET = 2 * 3600   # đang làm mà im quá mức này → vàng
STALE = 12 * 3600   # đang làm mà im quá mức này → đỏ
OPEN, SEP, CLOSE, NO, NC = "⟦", "¦", "⟧", "⟪", "⟫"   # dấu đánh dấu cặp EN/VI và tên việc trong md; book.py không đụng tới, finish() đổi thành HTML
# (khoá, chấm, hạng) theo thứ tự hiện trong báo cáo; chữ nhãn/nghĩa ở bảng TX (khoá c_<màu>, m_<màu>)
COLORS = (("red", "🔴"), ("yellow", "🟡"), ("blue", "🔵"), ("gray", "⚪"), ("green", "🟢"))
HEX = {"red": "#c0392b", "yellow": "#e0a800", "blue": "#2f6fb5", "gray": "#9aa0a6", "green": "#3b7a2a"}   # màu thanh ở bìa: đậm, phẳng, không pastel
DOT = dict(COLORS)

# NGUỒN DUY NHẤT của mọi câu do mã sinh: khoá -> (EN theo ASD-STE100 cơ học, VI). {tên} điền lúc dựng.
# Luật EN (ste_problems): câu ≤ 20 chữ, một ý một câu, tối đa 1 dấu phẩy, không «;», không viết tắt «'s n't», không bị động «is/are/was + -ed»,
# không mở câu bằng «-ing», không từ cấm (should may might shall get make). Danh sách viết tắt cho phép: STE_ABBR.
TX = {
    "title": ("Task status report", "Báo cáo tình trạng task"),
    "vol": ("Report", "Báo cáo"),
    "kick": ("Task status", "Tình trạng task"),
    "cover_h": ("{n} open tasks, {g} done.", "{n} việc mở, {g} xong."),
    "cover_lead": ("Report time: {stamp}. The data comes from Hang. Only green means done.", "Chốt lúc {stamp}. Số liệu đọc thẳng từ Hang. Chỉ màu xanh lá mới là xong."),
    "cover_alt": ("Tasks by color", "Số việc theo màu"),
    "footer": ("source: hang_open_work{room}. Live {sha}", "nguồn: hang_open_work{room}. Live {sha}"),
    "legend": ("Legend", "Chú giải"),
    "summary": ("Summary", "Tóm tắt"),
    "summary_stat": ("tasks done out of {n} open tasks", "việc đã xong trong {n} việc đang mở"),
    "sum_row": ("{label} tasks: {n}", "{label}: {n} việc"),
    "sum_sha": ("Sha on Live: {sha}", "Sha đang chạy trên Live: {sha}"),
    "unknown": ("unknown", "chưa biết"),
    "c_red": ("Red", "Đỏ"), "c_yellow": ("Yellow", "Vàng"), "c_blue": ("Blue", "Xanh dương"), "c_gray": ("Gray", "Xám"), "c_green": ("Green", "Xanh lá"),
    "m_red": ("Act now. An agent is dead. Or the task stops. Or there is no news for 12 hours.", "cần xử lý: agent đã chết, hoặc bị chặn, hoặc đang làm mà im hơn 12 giờ"),
    "m_yellow": ("Slow. It waits for the owner or a review. Or there is no news for 2 hours.", "chậm hoặc đang chờ: chờ owner, chờ review, hoặc im quá 2 giờ"),
    "m_blue": ("In progress. Work is normal. The task is not done.", "đang làm bình thường (chưa xong)"),
    "m_gray": ("Not started. The task is in the backlog or in the queue.", "chưa bắt đầu (backlog, xếp hàng)"),
    "m_green": ("DONE. The task is live. Only this color means done.", "XONG: đã lên Live. Chỉ màu này mới là xong"),
    "cont": ("continued", "tiếp"),
    # lý do (judge): vì sao thẻ có màu đó
    "r_dead": ("Agent {name} is dead ({health}). Reopen with: {reopen}.", "{name} đã chết ({health}), mở lại: {reopen}"),
    "r_noreopen": ("no reopen request", "chưa có yêu cầu mở lại"),
    "r_stage": ("The stage code is {st}.", "giai đoạn {st}"),
    "r_stale": ("Work is in progress, but no news for {dur}.", "đang làm mà im {dur}"),
    "r_owner": ("The task waits for the owner.", "chờ owner trả lời"),
    "r_wait": ("The task waits for: {text}.", "chờ: {text}"),
    "r_review": ("The task waits for a review. Work is not done.", "chờ review, việc chưa xong"),
    "r_live": ("The task is live.", "đã lên Live"),
    "r_queue": ("Not started. The task waits in the queue.", "chưa bắt đầu, việc đang chờ trong hàng"),
    "r_ok": ("Work is in progress and normal. Last news {when}.", "đang làm, tin cuối {when}"),
    "r_other": ("The stage code is {st}.", "giai đoạn {st}"),
    "r_more": ("Plus {n} more.", "Còn {n} lý do nữa."),
    # thẻ
    "s_status": ("Status: {x}", "Tình trạng: {x}"),
    "s_who": ("Workers: {x}.", "Người làm: {x}."),
    "s_nobody": ("none yet", "chưa có"),
    "s_more": ("{n} more", "{n} người nữa"),
    "s_idle": ("No news for {dur}.", "Im {dur}."),
    "s_branch": ("Branch: {b}.", "Nhánh: {b}."),
    "s_thread": ("Thread: room:{room}", "Thread: room:{room}"),
    "s_nobranch": ("none", "chưa có"),
    # đơn vị thời gian
    "t_now": ("just now", "vừa xong"),
    "t_min": ("{n} minutes", "{n} phút"), "t_hour": ("{n} hours", "{n} giờ"), "t_day": ("{n} days", "{n} ngày"),
    "t_ago": ("{d} ago", "{d} trước"),
    # worker status
    "w_in_progress": ("working", "đang làm"), "w_review": ("review", "review"), "w_done": ("done", "xong"), "w_fixing": ("fixing", "đang sửa"),
    "w_assigned": ("assigned", "đã nhận"), "w_open": ("new", "mới mở"), "w_blocked": ("stopped", "bị chặn"), "w_failed": ("failed", "thất bại"),
    "w_backlog": ("waiting", "chờ"), "w_queued": ("queued", "xếp hàng"),
    # trang cuối
    "nm": ("Not measured", "Chưa đo"),
    "nm_h": ("Limits", "Giới hạn"),
    "nm_smoke": ("Latest smoke result of Live: not measured. This report has no source for smoke.", "Kết quả smoke mới nhất của Live: chưa đo (báo cáo này không có nguồn đọc smoke)."),
    "nm_sha": ("Sha of each branch in review: not measured. Hang gives the branch name, not the sha.", "Sha từng nhánh đang review: chưa đo (hang_open_work chỉ cho tên nhánh, không cho sha)."),
    "nm_done": ("Done comes from the deployed flag. A thread without the flag is never green.", "«Xong» lấy từ cờ deployed của thread. Thread chưa có cờ thì không bao giờ ra xanh lá."),
    "nm_stage": ("The color follows the work list stage. The review log is not read.", "Màu theo giai đoạn của danh sách việc, chưa đọc sổ review."),
    "nm_pass": ("A task with a pass can still show yellow.", "Việc đã ĐẠT trong sổ vẫn có thể hiện vàng hoặc xám."),
    "nm_closed": ("Closed threads are not in this report.", "Thread đã đóng không có trong báo cáo."),
    "nm_room": ("Tasks outside room {room} are not in this report.", "Việc ngoài phòng {room} cũng không có."),
    "nm_src": ("The room of the source file: not measured.", "Phạm vi phòng của tệp nguồn: chưa đo."),
    "nm_hand": ("If a value is not measured, write not measured.", "Chưa đo thì ghi chưa đo."),
    # giao diện của trang (nút); nút ngắn tiếng Anh, giải thích tiếng Việt (luật UI Hang)
    "btn_vi": ("VI", "EN"),
    "btn_vi_title": ("Chuyển báo cáo sang tiếng Việt, không gọi mạng", "Switch the report to English"),
    "btn_tr": ("Translate task names", "Translate task names"),
    "btn_tr_title": ("Dịch tên việc sang tiếng Anh ngay trên máy bằng Translator của trình duyệt, không gửi chữ ra ngoài", "Dịch tên việc sang tiếng Anh ngay trên máy bằng Translator của trình duyệt, không gửi chữ ra ngoài"),
}
STE_ABBR = {"DONE", "ID", "UTC"}   # chữ HOA ≥ 2 ký tự được phép trong câu EN
STE_BANNED = {"should", "may", "might", "shall", "get", "gets", "got", "make", "makes"}   # vài từ STE cấm hay gặp; không phải từ điển STE đầy đủ (bản quyền ASD)


def L(key, lang, **kw):
    """Một câu theo ngôn ngữ; kw có thể là hàm f(lang) để giá trị đổi theo ngôn ngữ (thời gian, tên trạng thái)."""
    i = 0 if lang == "en" else 1
    return TX[key][i].format(**{k: (v(lang) if callable(v) else v) for k, v in kw.items()})


def bi(key, **kw):
    return f"{OPEN}{L(key, 'en', **kw)}{SEP}{L(key, 'vi', **kw)}{CLOSE}"


def pair(key, **kw):
    return (L(key, "en", **kw), L(key, "vi", **kw))


def mark(en, vi):
    return f"{OPEN}{en}{SEP}{vi}{CLOSE}"


def expand(md, lang):
    """md song ngữ → md một ngôn ngữ (cho selftest và cho ai muốn bản chữ thuần)."""
    i = 0 if lang == "en" else 1
    md = re.sub(re.escape(OPEN) + r"(.*?)" + re.escape(SEP) + r"(.*?)" + re.escape(CLOSE), lambda m: m.group(1 + i), md)
    return md.replace(NO, "").replace(NC, "")


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


def dur(sec, lang):
    """Khoảng thời gian: «8 hours» / «8 giờ»."""
    sec = max(0, int(sec))
    if sec < 90:
        return L("t_now", lang)
    if sec < 5400:
        return L("t_min", lang, n=round(sec / 60))
    if sec < 2 * 86400:
        return L("t_hour", lang, n=round(sec / 3600))   # từ 90 phút trở lên: làm tròn ≥ 2 nên luôn số nhiều
    return L("t_day", lang, n=round(sec / 86400))   # từ 2 ngày trở lên: số nhiều


def when(sec, lang):
    """«5 minutes ago» / «5 phút trước»; dưới 90 giây chỉ «just now»."""
    return dur(sec, lang) if max(0, int(sec)) < 90 else L("t_ago", lang, d=dur(sec, lang))


def short(s, n=64):
    s = " ".join(str(s or "").split()).replace("*", "").replace(OPEN, "").replace(CLOSE, "").replace(SEP, "").replace(NO, "").replace(NC, "")   # «*» sẽ thành chữ xanh lá; dấu đánh dấu của mình không được lọt vào tên
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def judge(t):
    """(màu, [(EN, VI) lý do]) của một thread, chỉ từ dữ liệu của chính thread. Xanh lá cần bằng chứng «xong» (deployed); không có bằng chứng thì không bao giờ xanh lá."""
    idle, st = t.get("idle") or 0, t.get("status")
    red, yel = [], []
    for d in t.get("down") or []:
        red.append(pair("r_dead", name=d.get("name") or "agent", health=d.get("health"), reopen=d.get("reopen") or (lambda lg: L("r_noreopen", lg))))
    if st in ("blocked", "failed"):
        red.append(pair("r_stage", st=st))
    if st == "in_progress" and idle > STALE:
        red.append(pair("r_stale", dur=lambda lg: dur(idle, lg)))
    if t.get("owner_wait"):
        yel.append(pair("r_owner"))
    for b in t.get("blocking") or []:
        yel.append(pair("r_wait", text=short(str(b).split(" («")[0], 50)))   # bỏ phần liệt kê tên việc trong ngoặc: dài và đã có ở thread kia
    if st == "review":
        yel.append(pair("r_review"))
    if st == "in_progress" and QUIET < idle <= STALE:
        yel.append(pair("r_stale", dur=lambda lg: dur(idle, lg)))
    if t.get("deployed") and not red and not yel:
        return "green", [pair("r_live")]
    if red:
        return "red", red + yel
    if yel:
        return "yellow", ([pair("r_live")] if t.get("deployed") else []) + yel   # đã lên Live mà còn chờ owner / việc khác: chưa phải xong
    if st in ("backlog", "queued"):
        return "gray", [pair("r_queue")]   # người làm hiện ở dòng riêng của thẻ, không lặp ở lý do
    if st == "in_progress":
        return "blue", [pair("r_ok", when=lambda lg: when(idle, lg))]
    return "gray", [pair("r_other", st=st or L("unknown", "vi"))]


def words(s):
    return len(s.split())


def card(t, color, why):
    """Một việc = một thẻ: dòng tiêu đề (lead: chấm màu + tên) rồi mỗi ý MỘT dòng (tình trạng, người làm, im bao lâu, nhánh, thread), mỗi dòng ≤ 20 chữ có nhãn. Không «- » (tích xanh), không «*…*» (xanh lá)."""
    idle = t.get("idle") or 0
    shown = list(why)
    while True:
        extra = len(why) - len(shown)
        st = (" ".join(x[0] for x in shown) + (" " + L("r_more", "en", n=extra) if extra else ""), "; ".join(x[1] for x in shown) + "." + (" " + L("r_more", "vi", n=extra) if extra else ""))
        seg1 = (L("s_status", "en", x=st[0]), L("s_status", "vi", x=st[1]))
        if len(shown) == 1 or (words(seg1[0]) <= CAP and words(seg1[1]) <= CAP):
            break
        shown.pop()
    ws = t.get("workers") or []
    one = lambda lg: ", ".join(f"{w.get('name') or str(w.get('agent'))[:8]} ({L('w_' + str(w.get('status')), lg) if 'w_' + str(w.get('status')) in TX else w.get('status')})" for w in ws[:3])
    who = lambda lg: (one(lg) + (", " + L("s_more", lg, n=len(ws) - 3) if len(ws) > 3 else "")) if ws else L("s_nobody", lg)
    quiet = not any("im " in x[1] or "no news" in x[0] for x in why)   # lý do «đang làm mà im N» đã nói rồi thì không lặp
    seg2 = tuple(L("s_who", lg, x=who(lg)) for lg in ("en", "vi"))
    seg3 = tuple(L("s_idle", lg, dur=lambda l2: dur(idle, l2)) for lg in ("en", "vi")) if quiet else None
    br = lambda lg: t.get("branch") or L("s_nobranch", lg)
    seg4 = tuple(L("s_branch", lg, b=br) for lg in ("en", "vi"))
    seg5 = tuple(L("s_thread", lg, room=t.get("room")) for lg in ("en", "vi"))
    segs = [x for x in (seg1, seg2, seg3, seg4, seg5) if x]
    return [f"> {DOT[color]} {NO}{short(t.get('name'), 60)}{NC}"] + [mark(e, v) for e, v in segs]   # MỖI Ý MỘT DÒNG (owner 31/10 m1a192af76ee1bb0): không gộp nhiều ý vào một khối chữ


def cover_svg(n, lang_en=True):
    """Hình bìa: thanh ngang số việc theo màu (thay tranh núi xanh lá mặc định của book-layout: xanh lá ở bìa đọc như «ổn»/«xong»). Thanh dài theo số việc; 0 việc thì chỉ còn khung rỗng.
    Nhãn viết bằng EN: ảnh SVG nhúng không đổi theo nút ngôn ngữ."""
    top, mx, rows = 42, max(max(n.values()), 1), []
    for i, (k, _) in enumerate(COLORS):
        y, w = top + i * 40, round(n[k] / mx * 170)
        rows.append(f'<text x="14" y="{y + 19}" font-size="17" fill="#3d3d3a">{L("c_" + k, "en")}</text>'
                    f'<rect x="136" y="{y}" width="206" height="26" rx="4" fill="none" stroke="#c9c9c2"/>'
                    + (f'<rect data-c="{k}" x="136" y="{y}" width="{max(w + 36, 36)}" height="26" rx="4" fill="{HEX[k]}"/>' if n[k] else "")
                    + f'<text x="356" y="{y + 20}" font-size="20" font-weight="700" fill="#1d1d1b">{n[k]}</text>')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 260" font-family="Be Vietnam Pro, Helvetica Neue, Helvetica, Arial, sans-serif">'   # ảnh SVG không tải được web font: lùi về sans hệ thống, không để rơi vào font có chân
           '<rect width="400" height="260" fill="#fbfaf6"/><text x="14" y="26" font-size="15" fill="#6b6b66">' + L("cover_alt", "en") + "</text>" + "".join(rows) + "</svg>")
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def build_md(d, now, room=ROOM):   # room=None: nguồn là tệp JSON, không biết phòng nào → không ghi tên phòng, không khẳng định «ngoài phòng X không có»
    ts = sorted(d.get("open") or [], key=lambda t: t.get("opened") or 0)
    running = str(d.get("running") or "")
    sha = running[:12] or L("unknown", "en")
    sha_vi = running[:12] or L("unknown", "vi")
    rows = [(t, *judge(t)) for t in ts]
    n = {k: sum(1 for _, c, _ in rows if c == k) for k, _ in COLORS}
    stamp = time.strftime("%d/%m/%Y %H:%M", time.localtime(now))
    rm = f" room={room}" if room else " (file)"
    rm_vi = f" room={room}" if room else " (tệp)"
    alt = L("cover_alt", "en") + ": " + ", ".join(f"{L('c_' + k, 'en').lower()} {n[k]}" for k, _ in COLORS)
    o = ["---", f"title: {bi('title')}", f"brand: Hang · {room}" if room else "brand: Hang", f"date: {stamp}", f"vol: {bi('vol')}",
         "footer: " + mark(L("footer", "en", room=rm, sha=running[:7] or L("unknown", "en")), L("footer", "vi", room=rm_vi, sha=running[:7] or L("unknown", "vi"))), "---",
         "=== cover", f"^ {bi('kick')}", f"# {bi('cover_h', n=len(ts), g=n['green'])}",
         f"> {bi('cover_lead', stamp=stamp)}", "---",
         f"![{alt}]({cover_svg(n)})", "",
         "=== page", f"@ {bi('legend')}", f"# {bi('legend')}", "---"]
    o += [f"{DOT[k]} {bi('c_' + k)}: {bi('m_' + k)}" for k, _ in COLORS] + [""]
    o += ["=== page", f"@ {bi('summary')}", f"# {bi('summary')}", "---",
          f"! {n['green']} | {bi('summary_stat', n=len(ts))} | " + (f"room:{room}, hang_open_work" if room else "hang_open_work")]
    o += [f"{DOT[k]} " + mark(*(L("sum_row", lg, label=L("c_" + k, lg), n=n[k]) for lg in ("en", "vi"))) for k, _ in COLORS if n[k]]
    o += [mark(L("sum_sha", "en", sha=sha), L("sum_sha", "vi", sha=sha_vi)), ""]
    for k, dot in COLORS:
        grp = [(t, w) for t, c, w in rows if c == k]
        for i in range(0, len(grp), PER_PAGE):
            o += ["=== page", f"@ {bi('c_' + k)}", f"# {bi('c_' + k)}" + (f" {bi('cont')}" if i else ""), "---"]
            o += [x for j, (t, w) in enumerate(grp[i:i + PER_PAGE]) for x in (["---"] if j else []) + card(t, k, w)] + [""]   # thanh ngắn giữa hai thẻ cho thấy ranh giới
    o += ["=== page", f"@ {bi('nm')}", f"# {bi('nm')}", "---", bi("nm_smoke"), bi("nm_sha"), bi("nm_done"), bi("nm_stage"), bi("nm_pass"),
          (mark(L("nm_closed", "en") + " " + L("nm_room", "en", room=room), L("nm_closed", "vi") + " " + L("nm_room", "vi", room=room)) if room
           else mark(L("nm_closed", "en") + " " + L("nm_src", "en"), L("nm_closed", "vi") + " " + L("nm_src", "vi"))),
          f"~ {bi('nm_hand')}", ""]
    return "\n".join(o)


# --- phần HTML sau book.py: đổi dấu đánh dấu thành span EN/VI + nút ngôn ngữ (không gọi mạng) ---
CSS = ("html[data-lang=en] .vi,html[data-lang=vi] .en{display:none}"
       ".stat{margin:28px 0;background:#f1efe8}.lead{margin-bottom:12px}.page:not(.cover){min-height:0}"   # book-layout: .stat có margin-top:auto (đẩy xuống đáy trang cao 760 px → khoảng trống lớn, owner m1a192b837fe75fa) và không có margin dưới (m1a192add91168b0): trang ôm nội dung, khối cách đều 28 px; nền sage xanh lá nhạt đổi xám ấm vì xanh lá chỉ dành cho «xong»
       "@media (min-width:821px){.spread{align-items:start;background:none;box-shadow:none;overflow:visible;column-gap:0}.spread::after{display:none}"   # QUYỂN TẬP mở hai trang (owner m1a192ced35a0c67: «hình quyển tập đâu?»): mỗi tờ giấy riêng ôm nội dung, không kéo dãn theo tờ kề nên không để lại giấy trống; gáy là bóng trong ở mép giữa
       ".spread .page{background:var(--paper);box-shadow:0 1px 2px #0000000f,0 12px 32px #00000014}"
       ".spread .page:nth-child(odd){border-radius:6px 0 0 6px;box-shadow:inset -22px 0 22px -22px #00000030,0 1px 2px #0000000f,0 12px 32px #00000014}"
       ".spread .page:nth-child(even){border-radius:0 6px 6px 0;box-shadow:inset 22px 0 22px -22px #00000030,0 1px 2px #0000000f,0 12px 32px #00000014}}"

       "#rp-bar{display:flex;gap:8px;justify-content:flex-end;padding:10px 16px;font:600 13px/1.2 'Be Vietnam Pro',Helvetica,Arial,sans-serif}"
       "#rp-bar button{font:inherit;color:#1d1d1b;background:#fbfaf6;border:1px solid #c9c9c2;border-radius:6px;padding:8px 12px;min-height:36px;cursor:pointer}"
       "#rp-bar button:focus-visible{outline:2px solid #1d1d1b;outline-offset:2px}"
       "html[data-lang=vi] #rp-tr{display:none}")
JS = """(function(){var h=document.documentElement,b=document.getElementById('rp-lang'),t=document.getElementById('rp-tr'),K='rp-lang',T=%(T)s;
function set(l){h.setAttribute('data-lang',l);h.lang=l;b.textContent=T[l].t;b.title=T[l].h;try{localStorage.setItem(K,l)}catch(e){}}
var q=(location.search.match(/[?&]lang=(en|vi)/)||[])[1],s=null;try{s=localStorage.getItem(K)}catch(e){}
set(q||(s==='en'||s==='vi'?s:null)||h.getAttribute('data-lang')||'en');
b.onclick=function(){set(h.getAttribute('data-lang')==='en'?'vi':'en')};
if('Translator' in self){t.hidden=false;var tr=null,on=false;t.onclick=async function(){var ns=document.querySelectorAll('.tn');
if(on){ns.forEach(function(n){if(n.dataset.o)n.textContent=n.dataset.o});on=false;t.setAttribute('aria-pressed','false');return}
t.disabled=true;var old=t.textContent;t.textContent='Đang tải bộ dịch trên máy…';
try{tr=tr||await Translator.create({sourceLanguage:'vi',targetLanguage:'en'});
for(var i=0;i<ns.length;i++){var n=ns[i];if(!n.dataset.o)n.dataset.o=n.textContent;n.textContent=await tr.translate(n.dataset.o)}
on=true;t.setAttribute('aria-pressed','true')}catch(e){t.title='Không dịch được trên máy này'}
t.textContent=old;t.disabled=false}}})();"""


def finish(page):
    """HTML của book.py → HTML song ngữ. Ngoài <title> và thuộc tính (chỉ lấy EN) mọi «⟦en¦vi⟧» thành hai span; «⟪tên⟫» thành span.tn; thêm thanh nút đầu trang."""
    pat = re.compile(re.escape(OPEN) + r"(.*?)" + re.escape(SEP) + r"(.*?)" + re.escape(CLOSE), re.S)
    page = re.sub(r"<title>.*?</title>", lambda m: pat.sub(lambda x: x.group(1), m.group(0)), page, flags=re.S)
    page = re.sub(r'(\b(?:alt|aria-label|title)=")([^"]*)(")', lambda m: m.group(1) + pat.sub(lambda x: x.group(1), m.group(2)) + m.group(3), page)
    page = pat.sub(lambda m: f'<span class="en" lang="en">{m.group(1)}</span><span class="vi" lang="vi">{m.group(2)}</span>', page)
    page = re.sub(re.escape(NO) + r"(.*?)" + re.escape(NC), r'<span class="tn">\1</span>', page)
    T = {"en": {"t": L("btn_vi", "en"), "h": L("btn_vi_title", "en")}, "vi": {"t": L("btn_vi", "vi"), "h": L("btn_vi_title", "vi")}}
    bar = ('<div id="rp-bar"><button type="button" id="rp-tr" hidden aria-pressed="false" title="' + htmllib.escape(L("btn_tr_title", "en")) + '">' + L("btn_tr", "en") + "</button>"
           '<button type="button" id="rp-lang" title="' + htmllib.escape(L("btn_vi_title", "en")) + '">' + L("btn_vi", "en") + "</button></div>")
    page = re.sub(r"<html([^>]*)>", lambda m: "<html" + re.sub(r'\s(lang|data-lang)="[^"]*"', "", m.group(1)) + ' lang="en" data-lang="en">', page, count=1)
    page = page.replace("</head>", f"<style>{CSS}</style></head>", 1) if "</head>" in page else CSS and page
    page = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + bar, page, count=1)
    return page.replace("</body>", "<script>" + JS % {"T": json.dumps(T, ensure_ascii=False)} + "</script></body>", 1)


# --- kiểm tra STE cơ học ---
def ste_problems(sentence):
    """Lỗi cơ học của một câu EN (rỗng = qua). KHÔNG phải chứng nhận ASD-STE100: chỉ chặn vài lỗi dễ đo."""
    s, bad = sentence.strip(), []
    w = s.split()
    if len(w) > 20:
        bad.append(f"{len(w)} chữ (> 20)")
    if ";" in s:
        bad.append("dấu «;»")
    if s.count(",") > 1:
        bad.append("quá 1 dấu phẩy")
    if re.search(r"\w'(s|t|re|ve|ll|d)\b", s):
        bad.append("viết tắt có dấu '")
    if re.search(r"\b(is|are|was|were|be|been|being)\s+\w+ed\b", s, re.I):
        bad.append("bị động")
    if w and re.match(r"[A-Za-z]+ing$", w[0].rstrip(":")):
        bad.append("mở câu bằng «-ing»")
    for x in re.findall(r"\b[A-Z]{2,}\b", s):
        if x not in STE_ABBR:
            bad.append("viết tắt chưa cho phép " + x)
    for x in re.findall(r"[A-Za-z]+", s.lower()):
        if x in STE_BANNED:
            bad.append("từ cấm " + x)
    return bad


def sentences(en):
    return [x for x in re.split(r"(?<=[.!?])\s+", en.strip()) if x]


def selftest():
    now = 1793431800
    T = lambda room, status, idle=60, **k: {"room": room, "name": "Việc " + room, "status": status, "idle": idle, "opened": len(room), "workers": [{"name": "Kai", "status": status}], **k}
    cases = (("agent chết", T("a", "in_progress", down=[{"name": "Kai", "health": "dead", "reopen": "s123"}]), "red", "Kai đã chết (dead), mở lại: s123", "Agent Kai is dead (dead). Reopen with: s123."),
             ("bị chặn", T("b", "blocked"), "red", "giai đoạn blocked", "The stage code is blocked."),
             ("im quá 12 giờ", T("c", "in_progress", idle=13 * 3600), "red", "đang làm mà im 13 giờ", "no news for 13 hours"),
             ("im quá 2 giờ", T("d", "in_progress", idle=3 * 3600), "yellow", "đang làm mà im 3 giờ", "no news for 3 hours"),
             ("chờ owner", T("e", "in_progress", owner_wait=True), "yellow", "chờ owner trả lời", "waits for the owner"),
             ("chờ review", T("f", "review"), "yellow", "chờ review", "waits for a review"),
             ("đợi việc khác", T("g", "in_progress", blocking=["Kai còn việc khác chờ («Việc x»)"]), "yellow", "chờ: Kai còn việc khác chờ", "waits for: Kai còn việc khác chờ."),
             ("backlog", T("h", "backlog", workers=[]), "gray", "chưa bắt đầu", "Not started."),
             ("đang làm ổn", T("i", "in_progress", idle=300), "blue", "đang làm, tin cuối 5 phút", "Last news 5 minutes ago"),
             ("đã lên Live", T("j", "done", deployed=True), "green", "đã lên Live", "The task is live."),
             ("deployed mà vẫn chờ review", T("n", "review", deployed=True), "yellow", "chờ review", "waits for a review"),
             ("đã lên Live nhưng agent chết", T("k", "review", deployed=True, down=[{"name": "Kai", "health": "dead"}]), "red", "đã chết", "is dead"),
             ("đã lên Live nhưng còn chờ owner", T("m", "review", deployed=True, owner_wait=True), "yellow", "chờ owner trả lời", "waits for the owner"),
             ("deployed false không xanh lá", T("l", "review", deployed=False), "yellow", "chờ review", "waits for a review"))
    for name, t, want, vi, en in cases:
        c, w = judge(t)
        assert c == want and any(vi in x[1] for x in w) and any(en in x[0] for x in w), (name, c, w)
    assert dur(5400, "en") == "2 hours" and dur(3600, "en") == "60 minutes" and when(30, "vi") == "vừa xong" and when(300, "en") == "5 minutes ago"
    fx = {"running": "c031e2312e03ebc2974b9672daee8cecbf5498e3", "open": [c[1] for c in cases]}
    md = build_md(fx, now)

    # 1. bảng TX: mọi câu EN có bản VI, không rỗng; câu EN cố định qua kiểm STE cơ học
    for k, (en, vi) in TX.items():
        assert en.strip() and vi.strip(), ("thiếu bản dịch", k)
        assert sorted(re.findall(r"\{(\w+)\}", en)) == sorted(re.findall(r"\{(\w+)\}", vi)), ("EN và VI dùng chỗ điền khác nhau", k)
        if not k.startswith(("btn_", "title", "vol", "footer", "c_", "unknown", "w_", "t_")):
            for snt in sentences(re.sub(r"\{\w+\}", "x", en)):
                assert not ste_problems(snt), ("câu EN vi phạm STE cơ học", k, snt, ste_problems(snt))
    assert ste_problems("The valve is closed by the pilot.") and ste_problems("You should check it; then go.") and ste_problems("Don't touch.")   # bộ lọc có cắn
    assert not ste_problems("The task waits for a review.")

    # 2. mỗi ngôn ngữ: không «- », không «*», dòng văn ≤ CAP chữ, thẻ 1–3 dòng, mỗi việc đúng một thẻ
    dots = ("> 🔴", "> 🟡", "> 🔵", "> ⚪", "> 🟢")
    mins = []
    for lang in ("en", "vi"):
        x = expand(md, lang)
        assert OPEN not in x and SEP not in x and CLOSE not in x and NO not in x, ("sót dấu đánh dấu", lang)
        assert not [ln for ln in x.splitlines() if ln.startswith("- ")], "còn danh sách «- » (tick xanh)"
        assert "*" not in x, "còn chữ nhấn «*…*» (book-layout tô xanh lá)"
        Ls = x.splitlines()
        body = Ls[Ls.index("=== cover"):]
        for ln in body:
            if ln.startswith(("=== ", "@ ", "^ ", "# ", "---", "! ", "![", "> 🔴", "> 🟡", "> 🔵", "> ⚪", "> 🟢")) or not ln.strip():
                continue
            t = ln[2:] if ln.startswith(("> ", "~ ")) else ln
            assert words(t) <= CAP, ("dòng quá CAP chữ", lang, words(t), ln)
        cards = 0
        for i, ln in enumerate(Ls):
            if not ln.startswith(dots):
                continue
            blk = []
            for y in Ls[i + 1:]:
                if not y.strip() or y.startswith(("> ", "=== ", "---")):
                    break
                blk.append(y)
            cards += 1
            assert 3 <= len(blk) <= 5, ("thẻ phải 3–5 dòng, mỗi ý một dòng", lang, ln, blk)
            mins += [(words(y), lang, y) for y in blk]
        assert cards == len(cases), (lang, cards)   # mỗi việc đúng một thẻ
        if lang == "en":
            for ln in body:   # câu EN do mã sinh trong thẻ và trang: ≤ 20 chữ (tên việc, nhánh là dữ liệu nên bỏ dòng tiêu đề thẻ)
                if ln.startswith(("=== ", "@ ", "^ ", "# ", "---", "! ", "![", "~ ")) or ln.startswith(dots) or not ln.strip():
                    continue
                for snt in sentences(ln[2:] if ln.startswith("> ") else ln):
                    assert len(snt.split()) <= 20 or "Branch:" in snt or "Workers:" in snt, ("câu EN > 20 chữ", snt)
    assert all(not (" Branch:" in m[2] or " Thread:" in m[2] or " Workers:" in m[2]) for m in mins), "mỗi ý một dòng: không gộp Workers/Branch/Thread vào một dòng"
    # thẻ dài nhất có thể: ba worker + nhiều lý do + tên nhánh dài vẫn ≤ CAP chữ mỗi dòng
    big = T("z" * 3, "in_progress", idle=14 * 3600, name="Một tên việc rất dài " * 6, branch="nhanh/" + "x" * 60, owner_wait=True,
            blocking=["một việc rất dài cần chờ " * 6, "việc khác"], down=[{"name": "Kai", "health": "dead", "reopen": "s1"}], workers=[{"name": f"Agent{i}", "status": "review"} for i in range(5)])
    c, w = judge(big)
    for lg in (0, 1):
        for ln in card(big, c, w)[1:]:
            assert words(expand(ln, "en" if lg == 0 else "vi")) <= CAP, (lg, ln)
    assert len(card(big, c, w)) <= 6

    # 3. màu, bìa, tên phòng
    import re as _re
    m = _re.search(r"!\[([^\]]+)\]\(data:image/svg\+xml;base64,([^)]+)\)", md)
    assert m and m.group(1).startswith("Tasks by color: red"), "bìa thiếu hình thanh số việc theo màu"
    svg = base64.b64decode(m.group(2)).decode()
    assert all(f'data-c="{k}"' in svg for k in ("red", "yellow", "blue", "gray", "green")), svg[:200]   # fx có đủ năm màu
    z = {"red": 2, "yellow": 1, "blue": 0, "gray": 0, "green": 0}
    assert 'data-c="green"' not in cover_svg(z) and 'data-c="blue"' not in cover_svg(z)   # 0 việc: không thanh (khung rỗng), nhất là xanh lá
    assert "núi" not in md and "mountain" not in md
    ex, vx = expand(md, "en"), expand(md, "vi")
    assert "# 14 open tasks, 1 done." in ex and "# 14 việc mở, 1 xong." in vx
    assert len([ln for ln in ex.splitlines() if ln.startswith("> 🟢 ")]) == 1   # đúng MỘT thẻ xanh lá (việc đã lên Live)
    g = ex.splitlines().index(next(ln for ln in ex.splitlines() if ln.startswith("> 🟢 ")))
    assert "room:j" in "\n".join(ex.splitlines()[g:g + 7])
    assert "Only green means done." in ex and "Chỉ màu xanh lá mới là xong." in vx
    for k in ("room:a", "room:h", "Sha on Live: c031e2312e03", "not measured"):
        assert k in ex, k
    for k in ("Sha đang chạy trên Live: c031e2312e03", "chưa đo"):
        assert k in vx, k
    assert "brand: Hang · vinh-hong" in md and "room=vinh-hong" in ex and "outside room vinh-hong" in ex and "ngoài phòng vinh-hong" in vx
    mt = expand(build_md(fx, now, None), "en")   # --src: không biết phòng
    assert "brand: Hang\n" in mt and "outside room" not in mt and "not measured" in mt and "vinh-hong" not in mt
    md2 = build_md(fx, now, "phong-khac")
    assert "brand: Hang · phong-khac" in md2 and "vinh-hong" not in md2   # tên phòng đi theo tham số, không gõ cứng
    e = expand(build_md({"open": [], "running": ""}, now), "en")
    assert "0 done." in e and e.count("=== page") >= 3 and "0 xong." in expand(build_md({"open": [], "running": ""}, now), "vi")
    assert "*" not in short("a *b* c") and OPEN not in short("x⟦y")

    # 4. finish(): span EN/VI, nút, tên việc, không URL ngoài, localStorage bọc try/catch, Translator chỉ khi 'Translator' in self và chỉ sau khi bấm
    fake = '<!doctype html><html lang="vi"><head><title>⟦Task¦Việc⟧</title></head><body><p>⟦Red¦Đỏ⟧ ⟪Tên *việc*⟫</p><img alt="⟦A¦B⟧"></body></html>'
    out = finish(fake)
    assert "<title>Task</title>" in out and 'alt="A"' in out, out
    assert '<span class="en" lang="en">Red</span><span class="vi" lang="vi">Đỏ</span>' in out and '<span class="tn">Tên *việc*</span>' in out
    assert '.stat{margin:28px 0' in out and '.page:not(.cover){min-height:0}' in out, "khối số lớn không bị đẩy xuống đáy trang (margin-top:auto của book-layout) và trang không kéo cao 760 px"
    assert '@media (min-width:821px){.spread{align-items:start' in out and '.spread::after{display:none}' in out, "khổ rộng giữ dáng quyển tập hai tờ, mỗi tờ ôm nội dung"
    assert 'lang="en" data-lang="en"' in out and 'id="rp-lang"' in out and 'id="rp-tr" hidden' in out
    assert OPEN not in out and SEP not in out and NO not in out
    assert not re.search(r"https?://|src=\"http|@import|fetch\(|XMLHttpRequest|translate\.google", out), "trang song ngữ không được gọi ra ngoài"
    assert out.count("localStorage") == 2 and out.count("try{") >= 2, "mọi đọc/ghi localStorage bọc try/catch"
    assert "'Translator' in self" in out and out.index("'Translator' in self") < out.index("Translator.create"), "kiểm có API trước, không gọi thử rồi bắt lỗi"
    assert out.index("Translator.create") > out.index("t.onclick"), "chỉ dịch khi người xem bấm"
    print("task_report selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--room", default=ROOM, help="phòng gốc cần báo cáo (mặc định vinh-hong)")
    ap.add_argument("--out", default=".", help="thư mục ghi rp-task-<giờ>.md")
    ap.add_argument("--src", help="đọc JSON này thay cho GET /work/open")
    ap.add_argument("--now", type=int, help="giờ unix (cho test)")
    ap.add_argument("--build", action="store_true", help="chạy book.py của skill book-layout để ra .html song ngữ")
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
        html.write_text(finish(html.read_text(encoding="utf-8")), encoding="utf-8")
        print(html)


if __name__ == "__main__":
    main()
