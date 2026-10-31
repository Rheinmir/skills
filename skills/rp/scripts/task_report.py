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
PER_PAGE = 1   # thẻ mỗi trang: hai tờ kề nhau (quyển tập) phải cao gần bằng nhau; một thẻ mỗi tờ thì chênh chiều cao chỉ vài dòng xuống dòng (owner 1/11: «quyển tập bị chuột cắn»)
CAP = 20   # chữ tối đa mỗi dòng văn (owner 31/10: m1a19291cd4a58d3 «10-25», rồi m1a192aae03f1e9c «10-20 thôi, 25 vẫn dài»); VI đếm theo khoảng trắng (mỗi âm tiết một chữ)
QUIET = 2 * 3600   # đang làm mà im quá mức này → vàng
STALE = 12 * 3600   # đang làm mà im quá mức này → đỏ
TXT = {"red": "#b3261e", "yellow": "#8a6100", "blue": "#1f5fa8", "gray": "#5b6168", "green": "#2e6b1f"}   # MÀU CHỮ của tên màu (owner 1/11: «Red, Yellow tô màu tương ứng»): đậm hơn màu thanh/chấm để đủ tương phản (≥ 4,8:1) trên giấy
CHB, CHE = "⟮", "⟯"   # ⟮mã⟯ → <code class="chip"> (owner 1/11: «mấy mã kiểu này … đóng vào chip và highlight lên»)
CB, CS, CE = "⟬", "‖", "⟭"   # ⟬màu‖chữ⟭ → <span class="c-màu">; book.py không đụng tới
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
    "sum_row": ("**{label} tasks:** {n}", "**{label}:** {n} việc"),
    "sum_sha": ("**Sha on Live:** {sha}", "**Sha đang chạy trên Live:** {sha}"),
    "unknown": ("unknown", "chưa biết"),
    "c_red": ("Red", "Đỏ"), "c_yellow": ("Yellow", "Vàng"), "c_blue": ("Blue", "Xanh dương"), "c_gray": ("Gray", "Xám"), "c_green": ("Green", "Xanh lá"),
    "m_red": ("Act now. An agent is dead. Or the task stops. Or there is no news for 12 hours.", "cần xử lý: agent đã chết, hoặc bị chặn, hoặc đang làm mà im hơn 12 giờ"),
    "m_yellow": ("Slow. It waits for the owner or a review. Or there is no news for 2 hours.", "chậm hoặc đang chờ: chờ owner, chờ review, hoặc im quá 2 giờ"),
    "m_blue": ("In progress. Work is normal. The task is not done.", "đang làm bình thường (chưa xong)"),
    "m_gray": ("Not started. The task is in the backlog or in the queue.", "chưa bắt đầu (backlog, xếp hàng)"),
    "m_green": ("DONE. The task is live. Only this color means done.", "XONG: đã lên Live. Chỉ màu này mới là xong"),
    "cont": ("continued", "tiếp"),
    # lý do (judge): vì sao thẻ có màu đó
    "r_dead": ("Agent {name} {h}. Reopen with: {reopen}.", "{name} {h}, mở lại: {reopen}"),
    "h_dead": ("is dead", "đã chết"), "h_exited": ("has exited", "đã thoát"), "h_hung": ("does not answer", "bị treo"),
    "h_other": ("is down", "gặp sự cố"), "h_idle_long": ("is idle for a long time", "rảnh quá lâu"), "h_limited": ("has no usage left", "hết hạn mức"),
    # chuỗi «blocking» do server sinh (Vietnamese): ba mẫu đã biết + mẫu chung; bản EN KHÔNG được lọt chữ Việt
    "b_wave": ("A later wave of the Epic waits for this wave.", "Epic còn wave sau chờ wave trước"),
    "b_parent": ("The parent {kind} waits for this thread.", "{kind} cha còn mở và đang chờ thread này xong"),
    "b_other": ("{name} has other work waiting.", "{name} còn việc khác chờ"),
    "b_generic": ("Another task depends on this task.", "việc khác đang chờ việc này"),
    "r_noreopen": ("no reopen request", "chưa có yêu cầu mở lại"),
    "r_stage": ("The stage code is {st}.", "giai đoạn {st}"),
    "r_stale": ("Work is in progress, but no news for {dur}.", "đang làm mà im {dur}"),
    "r_owner": ("The task waits for the owner.", "chờ owner trả lời"),
    "r_wait": ("{text}", "chờ: {text}"),
    "r_review": ("The task waits for a review. Work is not done.", "chờ review, việc chưa xong"),
    "r_live": ("The task is live.", "đã lên Live"),
    "r_queue": ("Not started. The task waits in the queue.", "chưa bắt đầu, việc đang chờ trong hàng"),
    "r_ok": ("Work is in progress and normal. Last news {when}.", "đang làm, tin cuối {when}"),
    "r_other": ("The stage code is {st}.", "giai đoạn {st}"),
    "r_more": ("Plus {n} more.", "Còn {n} lý do nữa."),
    # thẻ
    "s_status": ("**Status:** {x}", "**Tình trạng:** {x}"),   # nhãn đầu dòng in đậm (owner 1/11: «Status và Workers đã in bold đâu?»)
    "s_who": ("**Workers:** {x}.", "**Người làm:** {x}."),
    "s_nobody": ("none yet", "chưa có"),
    "s_more": ("{n} more", "{n} người nữa"),
    "s_idle": ("**Quiet for:** {dur}.", "**Im:** {dur}."),
    "s_branch": ("**Branch:** {b}.", "**Nhánh:** {b}."),
    "s_thread": ("**Thread:** {room}", "**Thread:** {room}"),
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
    "nm_smoke": ("**Latest smoke result of Live:** not measured. This report has no source for smoke.", "**Kết quả smoke mới nhất của Live:** chưa đo (báo cáo này không có nguồn đọc smoke)."),
    "nm_sha": ("**Sha of each branch in review:** not measured. Hang gives the branch name, not the sha.", "**Sha từng nhánh đang review:** chưa đo (hang_open_work chỉ cho tên nhánh, không cho sha)."),
    "nm_done": ("Done comes from the deployed flag. A thread without the flag is never green.", "«Xong» lấy từ cờ deployed của thread. Thread chưa có cờ thì không bao giờ ra xanh lá."),
    "nm_stage": ("The color follows the work list stage. The review log is not read.", "Màu theo giai đoạn của danh sách việc, chưa đọc sổ review."),
    "nm_pass": ("A task with a pass can still show yellow.", "Việc đã ĐẠT trong sổ vẫn có thể hiện vàng hoặc xám."),
    "nm_closed": ("Closed threads are not in this report.", "Thread đã đóng không có trong báo cáo."),
    "nm_room": ("Tasks outside room {room} are not in this report.", "Việc ngoài phòng {room} cũng không có."),
    "nm_src": ("The room of the source file: not measured.", "Phạm vi phòng của tệp nguồn: chưa đo."),
    # giao diện của trang (nút); nút ngắn tiếng Anh, giải thích tiếng Việt (luật UI Hang)
    "btn_vi": ("VI", "EN"),
    "btn_vi_title": ("Chuyển báo cáo sang tiếng Việt, không gọi mạng", "Switch the report to English"),
    "btn_tr": ("Translate task names", "Translate task names"),
    "btn_tr_title": ("Dịch tên việc sang tiếng Anh ngay trên máy bằng Translator của trình duyệt, không gửi chữ ra ngoài", "Dịch tên việc sang tiếng Anh ngay trên máy bằng Translator của trình duyệt, không gửi chữ ra ngoài"),
}
STE_ABBR = {"DONE", "ID", "UTC"}   # chữ HOA ≥ 2 ký tự được phép trong câu EN
STE_BANNED = {"should", "may", "might", "shall", "get", "gets", "got", "make", "makes"}   # vài từ STE cấm hay gặp; không phải từ điển STE đầy đủ (bản quyền ASD)


# KIỂU CHIP lấy từ trang mẫu của owner https://uiux.giatbh.io.vn/components/chip.html (Hình 1 «Vỏ chip», lớp .cx.fill; đo bằng Playwright 1/11): viên thuốc bo 999 px,
# nền pastel PHÂN NHÓM, viền 1 px đậm hơn nền ~15 %, chữ tối cố định #1a1d21 (đủ tương phản ở cả hai chế độ), padding ngang 14 px (ở đây 12 px vì chip nằm giữa dòng chữ).
# Nhóm mã dùng ba pastel của trang mẫu (CHIP_WHAT): Pink, Teal, Peach. Pink (hue ~333°) vừa dưới ngưỡng tông đỏ 335° của luật kiểm; Teal ~170° (ngoài dải xanh lá 75–150°).
CHIP_KINDS = {"pink": ("#f7c1d9", "#d3a5b9"), "teal": ("#b2ece2", "#97c8c0"), "peach": ("#fae3c8", "#d5c1aa")}   # (nền, viền) đúng các giá trị đo ở trang mẫu: Pink, Teal, Peach (viền = nền × 0,855). KHÔNG tím (Violet, Periwinkle: owner chê «lạc quẻ»), không xám
CHIP_INK = "#1a1d21"


CHIP_WHAT = {"sha": "pink", "room": "teal", "open": "teal", "branch": "teal", "reopen": "peach"}   # loại mã → nhóm màu: sha hồng phấn, mã mở lại đào, nơi chốn (room:, hang_open_work, nhánh) mòng két. Không tím (owner m1a1932949ed7b2d, Klau m1a1933d34ca6dd5), không xám (m1a19339fed71243), không đỏ/xanh lá (Kanade), không vàng/xanh dương (màu tình trạng)


def chip(text, what="sha"):
    """Mã máy đóng chip viên thuốc pastel theo nhóm, chữ Lexend Deca 300. what ∈ sha, room, open, reopen, branch (loại mã, do NGƯỜI GỌI khai: nhánh toàn chữ hex như «deadbee» vẫn là nhánh, không bị đoán nhầm thành sha)."""
    return f"{CHB}{CHIP_WHAT[what]}.{what}{CS}{text}{CHE}"


def clr(k, text):
    return f"{CB}{k}{CS}{text}{CE}"


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
    md = re.sub(re.escape(CB) + r"\w+" + re.escape(CS) + r"(.*?)" + re.escape(CE), r"\1", md, flags=re.S)
    md = re.sub(re.escape(CHB) + r"[\w.]+" + re.escape(CS), "", md).replace(CHB, "").replace(CHE, "")
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


def block_text(b, lang):
    """Một chuỗi «blocking» của server → câu theo ngôn ngữ. EN dịch bằng bảng (không để chữ Việt lọt vào), VI giữ gần nguyên bản (cắt ngắn)."""
    b = str(b)
    m = re.match(r"^(.+?) còn việc khác chờ", b)
    if m:
        return L("b_other", lang, name=m.group(1)) if lang == "en" else short(b.split(" («")[0], 50)
    m = re.match(r"^(Epic|Issue|Manual) cha «", b)
    if m:
        return L("b_parent", lang, kind=m.group(1)) if lang == "en" else L("b_parent", "vi", kind=m.group(1))
    if b.startswith("Epic còn wave sau"):
        return L("b_wave", lang)
    return L("b_generic", lang)   # mẫu lạ: câu chung, không đoán nghĩa


def judge(t):
    """(màu, [(EN, VI) lý do]) của một thread, chỉ từ dữ liệu của chính thread. Xanh lá cần bằng chứng «xong» (deployed); không có bằng chứng thì không bao giờ xanh lá."""
    idle, st = t.get("idle") or 0, t.get("status")
    red, yel = [], []
    for d in t.get("down") or []:
        hv = str(d.get("health"))
        red.append(pair("r_dead", name=d.get("name") or "agent", h=lambda lg, hv=hv: L("h_" + hv if "h_" + hv in TX else "h_other", lg), reopen=chip(d.get("reopen"), "reopen") if d.get("reopen") else (lambda lg: L("r_noreopen", lg))))
    if st in ("blocked", "failed"):
        red.append(pair("r_stage", st=st))
    if st == "in_progress" and idle > STALE:
        red.append(pair("r_stale", dur=lambda lg: dur(idle, lg)))
    if t.get("owner_wait"):
        yel.append(pair("r_owner"))
    for b in t.get("blocking") or []:
        yel.append(pair("r_wait", text=lambda lg, b=b: block_text(b, lg)))   # bỏ phần liệt kê tên việc trong ngoặc: dài và đã có ở thread kia
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
    br = lambda lg: chip(t.get("branch"), "branch") if t.get("branch") else L("s_nobranch", lg)
    seg4 = tuple(L("s_branch", lg, b=br) for lg in ("en", "vi"))
    seg5 = tuple(L("s_thread", lg, room=chip("room:" + str(t.get("room")), "room")) for lg in ("en", "vi"))
    segs = [x for x in (seg1, seg2, seg3, seg4, seg5) if x]
    return [f"> {DOT[color]} {NO}{short(t.get('name'), 60)}{NC}"] + [mark(e, v) for e, v in segs]   # MỖI Ý MỘT DÒNG (owner 31/10 m1a192af76ee1bb0): không gộp nhiều ý vào một khối chữ


def cover_svg(n, lang_en=True):
    """Hình bìa: thanh ngang số việc theo màu (thay tranh núi xanh lá mặc định của book-layout: xanh lá ở bìa đọc như «ổn»/«xong»). Thanh dài theo số việc; 0 việc thì chỉ còn khung rỗng.
    Nhãn viết bằng EN: ảnh SVG nhúng không đổi theo nút ngôn ngữ."""
    top, mx, rows = 42, max(max(n.values()), 1), []
    for i, (k, _) in enumerate(COLORS):
        y, w = top + i * 40, round(n[k] / mx * 170)
        rows.append(f'<text x="14" y="{y + 19}" font-size="17" fill="{TXT[k]}">{L("c_" + k, "en")}</text>'
                    f'<rect x="136" y="{y}" width="206" height="26" rx="4" fill="none" stroke="#c9c9c2"/>'
                    + (f'<rect data-c="{k}" x="136" y="{y}" width="{max(w + 36, 36)}" height="26" rx="4" fill="{HEX[k]}"/>' if n[k] else "")
                    + f'<text x="356" y="{y + 20}" font-size="20" font-weight="300" fill="#111">{n[k]}</text>')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 260" font-family="Lexend Deca, Helvetica Neue, Segoe UI Light, system-ui, sans-serif" font-weight="300">'   # ảnh SVG nhúng không dùng được font của trang: lùi về sans hệ thống ở độ đậm 300 (chữ trong hình không phải Lexend; ghi trong task.md)
           '<rect width="400" height="260" fill="#fbfaf6"/><text x="14" y="26" font-size="15" fill="#4a4a45">' + L("cover_alt", "en") + "</text>" + "".join(rows) + "</svg>")
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
         "=== page", f"@ {bi('summary')}", f"# {bi('summary')}", "---",
          f"! {n['green']} | {bi('summary_stat', n=len(ts))} | " + (f"{chip('room:' + room, 'room')} {chip('hang_open_work', 'open')}" if room else chip("hang_open_work", "open"))]
    o += [f"{DOT[k]} " + mark(*(L("sum_row", lg, label=clr(k, L("c_" + k, lg)), n=n[k]) for lg in ("en", "vi"))) for k, _ in COLORS if n[k]]
    o += [mark(L("sum_sha", "en", sha=chip(sha) if running else sha), L("sum_sha", "vi", sha=chip(sha_vi) if running else sha_vi)), "---"]
    o += [f"{DOT[k]} " + mark(*(f"**{clr(k, L('c_' + k, lg))}:** {L('m_' + k, lg)}" for lg in ("en", "vi"))) for k, _ in COLORS] + [""]   # chú giải ngay dưới tóm tắt: bìa và trang này cao gần bằng nhau
    for k, dot in COLORS:
        grp = [(t, w) for t, c, w in rows if c == k]
        for i in range(0, len(grp), PER_PAGE):
            o += ["=== page", f"@ {bi('c_' + k)}", f"# {clr(k, bi('c_' + k) + (' ' + bi('cont') if i else ''))}", "---"]
            o += [x for j, (t, w) in enumerate(grp[i:i + PER_PAGE]) for x in (["---"] if j else []) + card(t, k, w)] + [""]   # thanh ngắn giữa hai thẻ cho thấy ranh giới
    o += ["=== page", f"@ {bi('nm')}", f"# {bi('nm')}", "---", bi("nm_smoke"), bi("nm_sha"), bi("nm_done"), bi("nm_stage"), bi("nm_pass"),
          (mark(L("nm_closed", "en") + " " + L("nm_room", "en", room=room), L("nm_closed", "vi") + " " + L("nm_room", "vi", room=room)) if room
           else mark(L("nm_closed", "en") + " " + L("nm_src", "en"), L("nm_closed", "vi") + " " + L("nm_src", "vi"))),
          ""]   # không còn dòng chữ viết tay «chưa đo thì ghi chưa đo»: cao ~60 px làm tờ «Not measured» cao hơn tờ thẻ kề nó, quyển tập lệch chiều cao
    return "\n".join(o)


# --- phần HTML sau book.py: đổi dấu đánh dấu thành span EN/VI + nút ngôn ngữ (không gọi mạng) ---
FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FONT_FACES = (("LexendDeca-vietnamese.woff2", "U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB"),
              ("LexendDeca-latin.woff2", "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"))   # unicode-range của Google Fonts; font biến thiên wght 100–900, OFL (assets/fonts/OFL-Lexend.txt)


def font_css():
    """@font-face Lexend Deca tự phục vụ (base64 trong HTML, 0 request ngoài; owner D-c2-001). Chỉ vietnamese + latin: ký tự ngoài (vd →, ≤) rơi về font dự phòng, vẫn độ đậm 300."""
    out = []
    for name, rng in FONT_FACES:
        b = base64.b64encode((FONT_DIR / name).read_bytes()).decode()
        out.append('@font-face{font-family:"Lexend Deca";font-style:normal;font-weight:100 900;font-display:swap;src:url(data:font/woff2;base64,' + b + ') format("woff2");unicode-range:' + rng + "}")
    return "".join(out)


# Độ đậm (owner m1a192fa92c41dfb + Kanade DUYỆT): thân và h2/h3 300 («Lexend Deca light thôi», cấm 400 và bold: luật D-c2-002); tiêu đề và số lớn tối thiểu 200; 100 CHỈ khi cỡ ≥ 48 px và khổ ≥ 1100 px.
# Chữ mảnh (≤ 200) dùng màu gần đen #111: WCAG không tính độ mảnh của nét, bù bằng màu. Nút cũng 300.
CSS = ("html[data-lang=en] .vi,html[data-lang=vi] .en{display:none}"
       ':root{--sans:"Lexend Deca",system-ui,-apple-system,"Segoe UI",sans-serif;--hand:var(--sans);--page-pad:clamp(24px,4.8vw,60px);--ink3:#5c5c56}'   # tên font ở MỘT chỗ; lề rộng hơn kiểu tạp chí; --ink3 (chữ phụ nhỏ) từ #8a8a82 (3,3:1) lên #5c5c56 (≥ 6:1) vì chữ Light mỏng cần tương phản cao hơn
       "html body,html body *{font-weight:300!important}html body b,html body strong{font-weight:600!important}" + "".join(f".c-{k}{{color:{v}}}" for k, v in TXT.items()) + 'html body h2 [class^="c-"]{font-weight:300!important}html body b [class^="c-"]{font-weight:600!important}'
       + ".chip{display:inline;-webkit-box-decoration-break:clone;box-decoration-break:clone;overflow-wrap:anywhere;font-family:var(--sans);font-weight:300;font-size:.9em;line-height:inherit;letter-spacing:.01em;color:" + CHIP_INK + ";border:1px solid;border-radius:999px;padding:1px 12px}"   # INLINE + box-decoration-break:clone: chip xuống dòng thì mỗi dòng là một viên ôm sát chữ như highlight, không thành khối chữ nhật thừa chỗ (owner m1a19338db452775)
       + "".join(f".chip-{k}{{background:{bg};border-color:{bd}}}" for k, (bg, bd) in CHIP_KINDS.items()) + "p:has(.chip),cite:has(.chip){padding-right:26px}"   # chip inline + clone: trình duyệt không tính đệm của mảnh giữa khi ngắt dòng nên dòng đầy có thể thò ra 2 × (đệm + viền); chừa chỗ để không tràn   # tên màu tô màu tương ứng (trong h2 mảnh 200 phải #111, nên dùng 300) · NGOẠI LỆ DUY NHẤT (owner 1/11 thắng luật «chỉ 300»): nhãn đầu dòng trước «:» đậm 600; chữ sau «:» giữ Light   # kể cả <b>, h1–h3, nhãn; font dự phòng cũng nhẹ
       + "body{font-size:16px;line-height:1.7}"
       "html body h1,html body h2,html body .stat .big{font-weight:200!important;color:#111;letter-spacing:-.015em}html body h3{color:#111;letter-spacing:-.015em}"
       "h1,h2{line-height:1.2}.cover h1{font-size:clamp(44px,6.4vw,84px);line-height:1.2}h2{font-size:clamp(34px,4vw,52px)}"   # tiêu đề lớn mỏng canh trái như trang chủ lexend.com; line-height ≥ 1.2 để không cắt dấu Việt (check.mjs clip)
       "@media (min-width:1100px){html body .cover h1,html body .stat .big{font-weight:100!important}}"
       ".stat{margin:28px 0;background:#f1efe8}.lead{margin-bottom:12px}.page{min-height:0}@media (min-width:821px){.page{padding-bottom:calc(var(--page-pad) - 6px)}}"   # book-layout: .stat có margin-top:auto (đẩy xuống đáy trang cao 760 px → khoảng trống lớn, owner m1a192b837fe75fa) và không có margin dưới (m1a192add91168b0); đệm đáy khổ rộng bớt 34 px (còn --page-pad − 6; chân trang tuyệt đối cách nội dung ≥ 18 px) để hai tờ của quyển lệch chiều cao ít hơn
       "#rp-bar{display:flex;gap:8px;justify-content:flex-end;padding:10px 16px;font:300 13px/1.2 var(--sans)}"
       "#rp-bar button{font:inherit;color:#111;background:#fbfaf6;border:1px solid #c9c9c2;border-radius:6px;padding:8px 12px;min-height:36px;cursor:pointer}"
       "#rp-bar button:focus-visible{outline:2px solid #1d1d1b;outline-offset:2px}"
       "html[data-lang=vi] #rp-tr{display:none}")
JS = """(function(){var h=document.documentElement,b=document.getElementById('rp-lang'),t=document.getElementById('rp-tr'),K='rp-lang',T=%(T)s;
function eq(){var ps=[].slice.call(document.querySelectorAll('.page'));ps.forEach(function(p){p.style.minHeight=''});if(innerWidth<=820)return;var m=0;ps.forEach(function(p){m=Math.max(m,p.offsetHeight)});ps.forEach(function(p){p.style.minHeight=m+'px'})}
function set(l){h.setAttribute('data-lang',l);h.lang=l;b.textContent=T[l].t;b.title=T[l].h;try{localStorage.setItem(K,l)}catch(e){}eq()}
var rt=null;addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(eq,120)});addEventListener('load',eq);if(document.fonts){if(document.fonts.ready)document.fonts.ready.then(eq);if(document.fonts.addEventListener)document.fonts.addEventListener('loadingdone',eq)}setTimeout(eq,400);
var q=(location.search.match(/[?&]lang=(en|vi)/)||[])[1],s=null;try{s=localStorage.getItem(K)}catch(e){}
set(q||(s==='en'||s==='vi'?s:null)||h.getAttribute('data-lang')||'en');
b.onclick=function(){set(h.getAttribute('data-lang')==='en'?'vi':'en')};
if('Translator' in self){t.hidden=false;var tr=null,on=false;t.onclick=async function(){var ns=document.querySelectorAll('.tn');
if(on){ns.forEach(function(n){if(n.dataset.o)n.textContent=n.dataset.o});on=false;t.setAttribute('aria-pressed','false');eq();return}
t.disabled=true;var old=t.textContent;t.textContent='Đang tải bộ dịch trên máy…';
try{tr=tr||await Translator.create({sourceLanguage:'vi',targetLanguage:'en'});
for(var i=0;i<ns.length;i++){var n=ns[i];if(!n.dataset.o)n.dataset.o=n.textContent;n.textContent=await tr.translate(n.dataset.o)}
on=true;t.setAttribute('aria-pressed','true')}catch(e){t.title='Không dịch được trên máy này'}
t.textContent=old;t.disabled=false;eq()}}})();"""


def finish(page):
    """HTML của book.py → HTML song ngữ. Ngoài <title> và thuộc tính (chỉ lấy EN) mọi «⟦en¦vi⟧» thành hai span; «⟪tên⟫» thành span.tn; thêm thanh nút đầu trang."""
    pat = re.compile(re.escape(OPEN) + r"(.*?)" + re.escape(SEP) + r"(.*?)" + re.escape(CLOSE), re.S)
    colp = re.compile(re.escape(CB) + r"(\w+)" + re.escape(CS) + r"(.*?)" + re.escape(CE), re.S)
    page = re.sub(r"<title>.*?</title>", lambda m: colp.sub(lambda c: c.group(2), pat.sub(lambda x: x.group(1), m.group(0))), page, flags=re.S)
    page = re.sub(r'(\b(?:alt|aria-label|title)=")([^"]*)(")', lambda m: m.group(1) + re.sub(re.escape(CHB) + r"[\w.]+" + re.escape(CS), "", m.group(2)).replace(CHE, "") + m.group(3), page)
    page = re.sub(r'(\b(?:alt|aria-label|title)=")([^"]*)(")', lambda m: m.group(1) + pat.sub(lambda x: x.group(1), m.group(2)) + m.group(3), page)
    page = pat.sub(lambda m: f'<span class="en" lang="en">{m.group(1)}</span><span class="vi" lang="vi">{m.group(2)}</span>', page)
    page = re.sub(re.escape(NO) + r"(.*?)" + re.escape(NC), r'<span class="tn">\1</span>', page)
    page = colp.sub(lambda c: f'<span class="c-{c.group(1)}">{c.group(2)}</span>', page)
    page = re.sub(re.escape(CHB) + r"([\w.]+)" + re.escape(CS) + r"(.*?)" + re.escape(CHE), lambda c: f'<code class="chip chip-{c.group(1).split(".")[0]}" data-what="{c.group(1).split(".")[-1]}">{c.group(2)}</code>', page, flags=re.S)
    T = {"en": {"t": L("btn_vi", "en"), "h": L("btn_vi_title", "en")}, "vi": {"t": L("btn_vi", "vi"), "h": L("btn_vi_title", "vi")}}
    bar = ('<div id="rp-bar"><button type="button" id="rp-tr" hidden aria-pressed="false" title="' + htmllib.escape(L("btn_tr_title", "en")) + '">' + L("btn_tr", "en") + "</button>"
           '<button type="button" id="rp-lang" title="' + htmllib.escape(L("btn_vi_title", "en")) + '">' + L("btn_vi", "en") + "</button></div>")
    page = re.sub(r"<html([^>]*)>", lambda m: "<html" + re.sub(r'\s(lang|data-lang)="[^"]*"', "", m.group(1)) + ' lang="en" data-lang="en">', page, count=1)
    page = re.sub(r"<link[^>]*fonts\.(?:googleapis|gstatic)\.com[^>]*>\s*", "", page)   # font của book-layout (Be Vietnam Pro, Patrick Hand) không còn dùng: bỏ link, 0 request ngoài
    page = page.replace("</head>", f"<style>{font_css()}{CSS}</style></head>", 1) if "</head>" in page else CSS and page
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
    cases = (("agent chết", T("a", "in_progress", down=[{"name": "Kai", "health": "dead", "reopen": "s123"}]), "red", "Kai đã chết, mở lại: ⟮peach.reopen‖s123⟯", "Agent Kai is dead. Reopen with: ⟮peach.reopen‖s123⟯."),
             ("bị chặn", T("b", "blocked"), "red", "giai đoạn blocked", "The stage code is blocked."),
             ("im quá 12 giờ", T("c", "in_progress", idle=13 * 3600), "red", "đang làm mà im 13 giờ", "no news for 13 hours"),
             ("im quá 2 giờ", T("d", "in_progress", idle=3 * 3600), "yellow", "đang làm mà im 3 giờ", "no news for 3 hours"),
             ("chờ owner", T("e", "in_progress", owner_wait=True), "yellow", "chờ owner trả lời", "waits for the owner"),
             ("chờ review", T("f", "review"), "yellow", "chờ review", "waits for a review"),
             ("đợi việc khác", T("g", "in_progress", blocking=["Kai còn việc khác chờ («Việc x»)"]), "yellow", "chờ: Kai còn việc khác chờ", "Kai has other work waiting."),
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
        assert "*" not in re.sub(r"\*\*[^*\n]+:\*\*", "", x), "còn chữ nhấn «*…*» (book-layout tô xanh lá); chỉ cho phép nhãn đậm «**Nhãn:**» (owner 1/11)"
        assert all(ln.startswith(("> ", "!")) or not ln.count("**") % 2 for ln in x.splitlines()), "«**» phải đi theo cặp"
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

    # 2b. bản EN không lọt chữ Việt từ dữ liệu của server (blocking, health), trừ tên việc (dòng tiêu đề thẻ) và tên người/nhánh
    VN = re.compile(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ]", re.I)
    BL = ["Kai còn việc khác chờ («Việc x», «Việc y»)", "Epic cha «Tên Epic tiếng Việt» còn mở và đang chờ thread này xong (cha không chặn con)", "Epic còn wave sau chờ wave trước", "một câu lạ do server thêm sau này"]
    HL = ("dead", "exited", "hung", "idle_long", "limited", "mới_lạ")
    srv = {"running": "c031e23", "open": [T("b%d" % i, "in_progress", blocking=[b]) for i, b in enumerate(BL)] + [T("h%d" % i, "in_progress", down=[{"name": "Kai", "health": h, "reopen": None}]) for i, h in enumerate(HL)]}
    en2 = [ln for ln in expand(build_md(srv, now), "en").splitlines() if not ln.startswith(("> 🔴", "> 🟡", "> 🔵", "> ⚪", "> 🟢", "!["))]
    assert not [ln for ln in en2 if VN.search(ln)], ("chữ Việt lọt vào bản EN", [ln for ln in en2 if VN.search(ln)])
    assert "(dead)" not in expand(build_md(srv, now), "en") and "(dead)" not in expand(build_md(srv, now), "vi"), "health trùng chữ trong ngoặc"
    for want in ("Agent Kai is dead.", "Agent Kai has exited.", "The parent Epic waits for this thread.", "A later wave of the Epic waits for this wave.", "Another task depends on this task."):
        assert any(want in ln for ln in en2), want

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
    for k in ("room:a", "room:h", "**Sha on Live:** c031e2312e03", "not measured"):
        assert k in ex, k
    for k in ("**Sha đang chạy trên Live:** c031e2312e03", "chưa đo"):
        assert k in vx, k
    assert "brand: Hang · vinh-hong" in md and "room=vinh-hong" in ex and "outside room vinh-hong" in ex and "ngoài phòng vinh-hong" in vx
    mt = expand(build_md(fx, now, None), "en")   # --src: không biết phòng
    assert "brand: Hang\n" in mt and "outside room" not in mt and "not measured" in mt and "vinh-hong" not in mt
    md2 = build_md(fx, now, "phong-khac")
    assert "brand: Hang · phong-khac" in md2 and "vinh-hong" not in md2   # tên phòng đi theo tham số, không gõ cứng
    e = expand(build_md({"open": [], "running": ""}, now), "en")
    assert "0 done." in e and e.count("=== page") >= 2 and "0 xong." in expand(build_md({"open": [], "running": ""}, now), "vi")
    assert "*" not in short("a *b* c") and OPEN not in short("x⟦y")

    # 3b. tên màu tô màu tương ứng (owner 1/11): chú giải, dòng tóm tắt, tiêu đề trang; màu chữ đủ tương phản trên giấy #fbfaf6
    def _lum(h):
        v = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        v = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in v]
        return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]
    for k, hx in TXT.items():
        a, b = _lum(hx), _lum("#fbfaf6")
        assert (max(a, b) + .05) / (min(a, b) + .05) >= 4.5, ("màu chữ thiếu tương phản", k, hx)
    assert set(TXT) == {k for k, _ in COLORS}
    assert "gray" not in CHIP_KINDS and set(CHIP_WHAT.values()) <= set(CHIP_KINDS) and len(set(CHIP_WHAT.values())) >= 3 and not ({"violet", "periwinkle", "gray"} & set(CHIP_KINDS)), "chip không dùng xám hay tím, có ≥ 3 nhóm pastel"
    for k, _ in COLORS:
        assert f"**{CB}{k}{CS}" in md, ("chú giải thiếu màu", k)                      # chú giải
    assert md.count(f"# {CB}red{CS}") >= 1 and md.count(f"# {CB}yellow{CS}") >= 1, "tiêu đề trang màu phải tô màu"   # fx có đỏ và vàng
    assert all(CB not in x and CE not in x for x in (expand(md, "en"), expand(md, "vi"))), "marker màu không được sót ở bản chữ thuần"

    # 3c. mã máy đóng chip (owner 1/11): sha, mã mở lại, nhánh, thread, mã trong tóm tắt
    assert f"{CHB}pink.sha{CS}c031e2312e03{CHE}" in md and f"{CHB}peach.reopen{CS}s123{CHE}" in md, "sha (hồng phấn) và mã mở lại (đào) phải là chip"
    assert md.count(f"**Thread:** {CHB}teal.room{CS}room:") >= len(cases) and f"{CHB}teal.room{CS}room:vinh-hong{CHE} {CHB}teal.open{CS}hang_open_work{CHE}" in md, "tên room: và hang_open_work là chip mòng két"
    assert "none" not in "".join(re.findall(re.escape(CHB) + r"[\w.]+" + re.escape(CS) + r"(.*?)" + re.escape(CHE), md)) and "chưa có" not in "".join(re.findall(re.escape(CHB) + r"[\w.]+" + re.escape(CS) + r"(.*?)" + re.escape(CHE), md)), "«none»/«chưa có» không phải mã, không đóng chip"
    assert CHB not in expand(md, "en") and CHE not in expand(md, "vi"), "marker chip không được sót ở bản chữ thuần"

    # 4. finish(): span EN/VI, nút, tên việc, không URL ngoài, localStorage bọc try/catch, Translator chỉ khi 'Translator' in self và chỉ sau khi bấm
    fake = '<!doctype html><html lang="vi"><head><title>⟬red‖⟦Task¦Việc⟧⟭</title></head><body><p>⟬red‖⟦Red¦Đỏ⟧⟭ ⟪Tên *việc*⟫ ⟮pink.sha‖sf98721ecbfeb⟯ ⟮teal.branch‖deadbeef⟯</p><img alt="⟦A¦B⟧"></body></html>'
    out = finish(fake)
    assert "<title>Task</title>" in out and 'alt="A"' in out, out
    assert '<span class="c-red"><span class="en" lang="en">Red</span><span class="vi" lang="vi">Đỏ</span></span>' in out, "marker màu thành span.c-red"
    assert '<span class="en" lang="en">Red</span><span class="vi" lang="vi">Đỏ</span>' in out and '<span class="tn">Tên *việc*</span>' in out
    assert '.stat{margin:28px 0' in out and '.page{min-height:0}' in out, "khối số lớn không bị đẩy xuống đáy trang (margin-top:auto của book-layout) và trang không kéo cao 760 px"
    assert '.spread{align-items:start' not in out, "quyển tập hai tờ cao bằng nhau (giấy chung của book-layout), không tờ riêng lệch chiều cao"
    assert 'lang="en" data-lang="en"' in out and 'id="rp-lang"' in out and 'id="rp-tr" hidden' in out
    assert '<code class="chip chip-pink" data-what="sha">sf98721ecbfeb</code>' in out and '<code class="chip chip-teal" data-what="branch">deadbeef</code>' in out and CHB not in out and CHE not in out, "marker chip thành <code class=chip chip-nhóm data-what=loại>; nhánh toàn hex vẫn là branch"
    assert OPEN not in out and SEP not in out and NO not in out
    assert not re.search(r"https?://|src=\"http|@import|fetch\(|XMLHttpRequest|translate\.google", out), "trang song ngữ không được gọi ra ngoài"
    # font tự phục vụ (owner D-c2-001/002): @font-face base64 woff2, không link Google Fonts, độ đậm ≤ 300, sàn mỏng
    fake2 = fake.replace("</head>", '<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro" rel="stylesheet"></head>')
    o2 = finish(fake2)
    assert "fonts.googleapis" not in o2 and "fonts.gstatic" not in o2, "gỡ link Google Fonts của book-layout"
    assert o2.count("@font-face") == 2 and o2.count("data:font/woff2;base64,d09GMg") == 2, "hai @font-face (vietnamese, latin) nhúng base64 woff2"
    assert 'font-family:"Lexend Deca"' in o2 and '--sans:"Lexend Deca"' in o2, "họ font Lexend Deca ở một chỗ (--sans)"
    css = CSS
    css_no_b = css.replace("html body b,html body strong{font-weight:600!important}", "").replace('html body b [class^="c-"]{font-weight:600!important}', "")   # ngoại lệ DUY NHẤT: nhãn đầu dòng <b> 600 (owner 1/11)
    assert "html body b,html body strong{font-weight:600!important}" in css and 'html body b [class^="c-"]{font-weight:600!important}' in css and css.count("600") == 2, "chỉ nhãn <b> và chữ màu trong nhãn được 600"
    ws = sorted({int(w) for w in re.findall(r"font-weight:(\d+)", css_no_b) + re.findall(r"font:(\d+) ", css_no_b)})   # CSS còn lại ≤ 300
    assert ws and max(ws) <= 300 and min(ws) >= 100, ("độ đậm trong CSS phải trong 100–300", ws)
    assert "@media (min-width:1100px){html body .cover h1,html body .stat .big{font-weight:100!important}}" in css and "html body h1,html body h2,html body .stat .big{font-weight:200!important;color:#111" in css, "sàn mỏng: 100 chỉ ≥ 1100 px, mặc định 200 và màu gần đen"
    svg0 = base64.b64decode(cover_svg({"red": 1, "yellow": 0, "blue": 0, "gray": 0, "green": 0}).split(",", 1)[1]).decode()
    assert 'font-weight="700"' not in svg0 and 'font-weight="300"' in svg0, "hình bìa không còn chữ đậm"
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
