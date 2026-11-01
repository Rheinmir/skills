#!/usr/bin/env python3
"""/rp doc: dựng báo cáo / tài liệu THƯỜNG (không phải tình trạng task) thành trang HTML kiểu /rp.

python3 doc_report.py <nguồn.md|nguồn.json> [--out DIR] [--lang vi|both] [--build] [--check] [--selftest]

Dùng chung đường ống với `task_report.py` (import, không sao chép): md → book-layout (book.py) → finish() → check.mjs + check_lang.mjs.
Mặc định `--lang vi`: MỘT ngôn ngữ, không kiểm STE, không nút EN/VI. `--lang both`: nguồn JSON mà mọi chuỗi là cặp {"en","vi"}; EN kiểm STE cơ học, trang có nút EN/VI.

Nguồn markdown (chỉ cho --lang vi), mỗi ý MỘT dòng, ≤ 20 chữ mỗi dòng:
    # Tiêu đề báo cáo
    kicker: Báo cáo công cụ              (tuỳ chọn, chữ nhỏ trên tiêu đề bìa)
    > Một dòng dẫn cho bìa               (tuỳ chọn, lặp được)
    stat: 3 | plugin đã cài | pm-toolkit pm-execution      (tuỳ chọn: số lớn | nhãn | mã đóng chip)
    ## Tên trang
    Nhãn: nội dung                       (nhãn trước «:» in đậm; dòng không có nhãn cũng được)
    footer: chữ chân trang               (tuỳ chọn)
Mã máy (sha, room:…, nhánh/đường dẫn có «/», mã tin m…, mã mở lại s…) tự được đóng chip; không cần viết dấu hiệu gì.
Không dùng danh sách «- », bảng «|», chữ nhấn «*…*»: book-layout tô dấu tích xanh / chữ xanh, owner đọc là «xong».

Nguồn JSON: {"title","kicker","lead":[…],"stat":{"n","label","codes":[…]},"pages":[{"title","lines":["Nhãn: nội dung" | {"label","text"}]}],"footer"};
chuỗi là str (--lang vi) hoặc {"en","vi"} (--lang both).
"""
from __future__ import annotations
import argparse, base64, html as htmllib, json, re, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import task_report as T   # nguồn duy nhất của dấu đánh dấu, chip, finish(), STE, CAP

CAP = T.CAP
CODE = re.compile(r"(\bs[0-9a-f]{11,12}\b|\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b|\bm[0-9a-f]{15}\b|\broom:[a-z0-9][a-z0-9-]*|\b[a-z0-9][a-z0-9_.-]*/[a-z0-9][a-z0-9_./-]*)")   # cùng mẫu với check_lang.mjs


def kind_of(code):
    """Loại mã → data-what (chọn nhóm màu chip): sha hồng; room/nhánh/đường dẫn/mã tin mòng két; mã mở lại đào."""
    if code.startswith("room:"):
        return "room"
    if "/" in code:
        return "branch"
    if re.fullmatch(r"s[0-9a-f]{11,12}", code):
        return "reopen"
    if re.fullmatch(r"m[0-9a-f]{15}", code):
        return "open"
    return "sha"


def chipify(text):
    """Đóng chip mọi mã máy trong một đoạn chữ thường (không đụng chữ đã nằm trong dấu chip)."""
    out, last = [], 0
    for m in CODE.finditer(text):
        out.append(text[last:m.start()]); out.append(T.chip(m.group(0), kind_of(m.group(0)))); last = m.end()
    return "".join(out) + text[last:]


def vis(text):
    """Chữ nhìn thấy của một dòng (bỏ nhấn đậm và dấu chip) để đếm chữ."""
    return re.sub(re.escape(T.CHB) + r"[\w.]+" + re.escape(T.CS), "", text.replace("**", "")).replace(T.CHE, "")


def pairof(v, path, lang, errs):
    """Chuỗi nguồn → (en, vi). lang=vi: str hoặc {vi}; lang=both: {en, vi} bắt buộc."""
    if isinstance(v, dict):
        en, vi = v.get("en"), v.get("vi")
    else:
        en, vi = None, v
    if lang == "both":
        if not (isinstance(en, str) and en.strip() and isinstance(vi, str) and vi.strip()):
            errs.append(f"{path}: --lang both cần cặp {{\"en\": \"…\", \"vi\": \"…\"}} đủ cả hai; sửa: thêm bản còn thiếu")
            return "", ""
        return en.strip(), vi.strip()
    if not (isinstance(vi, str) and vi.strip()):
        errs.append(f"{path}: chuỗi trống hoặc sai kiểu; sửa: viết một dòng chữ")
        return "", ""
    return None, vi.strip()


def parse_md(text):
    """Markdown đơn giản → cấu trúc nguồn (như JSON). Lỗi cú pháp trả kèm dòng số mấy."""
    doc = {"title": None, "kicker": None, "lead": [], "stat": None, "pages": [], "footer": None}; errs = []
    page = None
    for no, raw in enumerate(text.splitlines(), 1):
        ln = raw.strip()
        if not ln:
            continue
        if ln.startswith("## "):
            page = {"title": ln[3:].strip(), "lines": []}; doc["pages"].append(page)
        elif ln.startswith("# "):
            doc["title"] = ln[2:].strip()
        elif ln.startswith("> "):
            doc["lead"].append(ln[2:].strip())
        elif re.match(r"kicker\s*:", ln, re.I):
            doc["kicker"] = ln.split(":", 1)[1].strip()
        elif re.match(r"footer\s*:", ln, re.I):
            doc["footer"] = ln.split(":", 1)[1].strip()
        elif re.match(r"stat\s*:", ln, re.I):
            bits = [b.strip() for b in ln.split(":", 1)[1].split("|")]
            if len(bits) < 2 or not bits[0]:
                errs.append(f"dòng {no}: stat cần «số | nhãn | mã…»; sửa: stat: 3 | plugin đã cài | pm-toolkit")
            else:
                doc["stat"] = {"n": bits[0], "label": bits[1], "codes": bits[2].split() if len(bits) > 2 else []}
        elif page is None:
            errs.append(f"dòng {no}: «{ln[:40]}» nằm ngoài trang; sửa: đặt dưới một dòng «## Tên trang» (hoặc «> » nếu là dòng dẫn bìa)")
        else:
            page["lines"].append(ln)
    return doc, errs


def normalize(doc, lang):
    """Cấu trúc nguồn → mô hình chuẩn, kèm danh sách lỗi (mỗi lỗi nói dòng nào, sửa thế nào)."""
    errs = []
    M = {"title": pairof(doc.get("title") or "", "title", lang, errs) if doc.get("title") else None}
    if not M["title"]:
        errs.append("thiếu tiêu đề; sửa: thêm dòng «# Tiêu đề» (md) hoặc \"title\" (JSON)")
    M["kicker"] = pairof(doc["kicker"], "kicker", lang, errs) if doc.get("kicker") else None
    M["footer"] = pairof(doc["footer"], "footer", lang, errs) if doc.get("footer") else None
    M["lead"] = [pairof(x, f"lead[{i}]", lang, errs) for i, x in enumerate(doc.get("lead") or [])]
    st = doc.get("stat")
    M["stat"] = None
    if st:
        M["stat"] = (str(st["n"]), pairof(st["label"], "stat.label", lang, errs), [str(c) for c in st.get("codes") or []])
    M["pages"] = []
    if not doc.get("pages"):
        errs.append("không có trang nào; sửa: thêm ít nhất một «## Tên trang» kèm vài dòng")
    for pi, pg in enumerate(doc.get("pages") or [], 1):
        t = pairof(pg.get("title") or "", f"trang {pi} tiêu đề", lang, errs)
        lines = []
        for li, ln in enumerate(pg.get("lines") or [], 1):
            path = f"trang {pi} «{(pg.get('title') if isinstance(pg.get('title'), str) else '')[:20]}» dòng {li}"
            if isinstance(ln, dict) and "label" in ln:
                lab = pairof(ln["label"], path + " nhãn", lang, errs); txt = pairof(ln["text"], path + " chữ", lang, errs)
                lines.append(("lab", lab, txt, path))
            else:
                lines.append(("raw", pairof(ln, path, lang, errs), None, path))
        if not lines:
            errs.append(f"trang {pi} «{t[1][:20]}» không có dòng nào; sửa: thêm dòng «Nhãn: nội dung»")
        if len(lines) > 9:
            errs.append(f"trang {pi} «{t[1][:20]}» có {len(lines)} dòng (> 9): tờ quá dài so với bìa; sửa: tách thành hai trang")
        M["pages"].append((t, lines))
    return M, errs


def check_lines(M, lang):
    """Luật hình thức theo từng dòng; lỗi nói dòng nào và sửa thế nào (cho agent tự sửa vòng sau)."""
    errs = []
    def one(en_vi, path):
        for i, txt in enumerate(en_vi):
            if txt is None:
                continue
            tag = "EN" if (lang == "both" and i == 0) else "VI" if lang == "both" else ""
            if re.match(r"^\s*([-*+]\s|\d+[.)]\s|\|)", txt):
                errs.append(f"{path}{' ' + tag if tag else ''}: dòng mở đầu bằng «{txt[:3]}» (danh sách/bảng); sửa: bỏ dấu, viết mỗi ý một dòng riêng")
            if re.search(r"(^|[\s(])\*[^*\s][^*]*\*", txt) and "**" not in txt:
                errs.append(f"{path}{' ' + tag if tag else ''}: có chữ nhấn «*…*» (book-layout tô xanh lá, đọc là «xong»); sửa: bỏ dấu sao")
            n = len(vis(txt).split())
            if n > CAP:
                errs.append(f"{path}{' ' + tag if tag else ''}: {n} chữ (> {CAP}): «{txt[:50]}…»; sửa: tách thành hai dòng hoặc cắt ý phụ")
            if lang == "both" and i == 0:
                for pr in T.ste_problems(txt):
                    errs.append(f"{path} EN: {pr}: «{txt[:50]}»; sửa: viết câu EN ngắn hơn, bỏ từ cấm / viết tắt, một ý một câu")
    for t, lines in M["pages"]:
        one(t, "tiêu đề trang")
        for kind, a, b, path in lines:
            if kind == "lab":
                one((a[0], a[1]), path + " nhãn"); one((b[0], b[1]), path)
            else:
                one(a, path)
    return errs


def cover_svg(M):
    """Bìa phẳng trung tính (thay tranh núi xanh lá mặc định của book-layout): thanh ngang số dòng mỗi trang. Không xanh lá, không đỏ, không tranh."""
    top, rows = 44, []
    ps = [(t[1], len(l)) for t, l in M["pages"]][:7]; mx = max([n for _, n in ps] + [1])
    for i, (name, n) in enumerate(ps):
        y = top + i * 30
        rows.append(f'<text x="14" y="{y + 12}" font-size="13" fill="#111">{htmllib.escape(name[:34])}</text>'
                    f'<rect x="14" y="{y + 17}" width="{round(n / mx * 220) + 24}" height="7" rx="3" fill="#8b8579"/><text x="{round(n / mx * 220) + 46}" y="{y + 25}" font-size="12" fill="#111">{n}</text>')
    h = top + len(ps) * 30 + 6
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 {h}" font-family="Lexend Deca, Helvetica Neue, Segoe UI Light, system-ui, sans-serif" font-weight="300">'
           f'<rect width="400" height="{h}" fill="#fbfaf6"/><text x="14" y="26" font-size="14" fill="#4a4a45">{htmllib.escape(M["title"][1][:46])}</text>' + "".join(rows) + "</svg>")
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def build_md(M, lang, now=None):
    both = lang == "both"
    def S(pair, wrap=chipify):
        en, vi = pair
        return T.mark(wrap(en), wrap(vi)) if both else wrap(vi)
    stamp = time.strftime("%d/%m/%Y %H:%M", time.localtime(now or time.time()))
    title = M["title"]; vol = ("Report", "Báo cáo")
    foot = M["footer"] or ((f"Hang · {title[0]}", f"Hang · {title[1]}") if both else (None, f"Hang · {title[1]}"))
    o = ["---", f"title: {S(title, lambda x: x)}", "brand: Hang", f"date: {stamp}", f"vol: {S(vol, lambda x: x) if both else vol[1]}", "footer: " + S(foot, lambda x: x), "---",
         "=== cover"]
    if M["kicker"]:
        o.append(f"^ {S(M['kicker'], lambda x: x)}")
    o.append(f"# {S(title, lambda x: x)}")
    o += [f"> {S(x)}" for x in M["lead"]]
    o += ["---", f"![{htmllib.escape(title[1])}]({cover_svg(M)})", ""]
    first = True
    for t, lines in M["pages"]:
        o += ["=== page", f"@ {S(t, lambda x: x)}", f"# {S(t, lambda x: x)}", "---"]
        if first and M["stat"]:
            n, lab, codes = M["stat"]; cc = " ".join(T.chip(c, kind_of(c)) for c in codes)
            o.append(f"! {n} | {S(lab, lambda x: x)} | {cc}".rstrip(" |"))
        first = False
        for kind, a, b, path in lines:
            if kind == "lab":
                o.append(S(("**" + a[0] + ":** " + b[0], "**" + a[1] + ":** " + b[1]) if both else (None, "**" + a[1] + ":** " + b[1])))
            else:
                en, vi = a
                if not both and re.match(r"^[^\s:*][^:*]{0,30}:\s+\S", vi):
                    k, v = vi.split(":", 1); vi = f"**{k.strip()}:** {v.strip()}"
                    o.append(S((en, vi)))
                else:
                    o.append(S(a))
        o.append("")
    return "\n".join(o)


def book_py():
    here = Path(__file__).resolve()
    for c in (here.parents[2] / "book-layout" / "scripts" / "book.py", Path.home() / ".claude/skills/book-layout/scripts/book.py", Path.home() / ".agents/skills/book-layout/scripts/book.py"):
        if c.is_file():
            return c
    sys.exit("blocked: không thấy skill book-layout (cập nhật skills hoặc chạy từ checkout repo skills)")


def load(src, lang):
    p = Path(src)
    if not p.is_file():
        sys.exit(f"blocked: không thấy tệp nguồn {src}")
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        try:
            return json.loads(text), []
        except ValueError as e:
            sys.exit(f"nguồn JSON hỏng: {e}")
    if lang == "both":
        sys.exit("--lang both cần nguồn JSON với cặp {en, vi}; markdown chỉ dùng với --lang vi")
    return parse_md(text)


def selftest():
    SAMPLE = "# Báo cáo thử\nkicker: Thử\n> Một dòng dẫn.\nstat: 2 | mục | abc1234\n## Trang một\nNhãn: nội dung có mã phuryn/pm-skills và sha 2a12295.\nDòng không nhãn.\n## Trang hai\nMột: hai\n"
    d, e = parse_md(SAMPLE); assert not e, e
    M, e = normalize(d, "vi"); assert not e, e
    assert not check_lines(M, "vi")
    md = build_md(M, "vi", now=0)
    assert T.CHB in md and "⟦" not in md, "vi: có chip, không có cặp EN/VI"
    assert "**Nhãn:**" in md and "**Một:**" in md
    # lỗi phải nói dòng nào + sửa thế nào
    bad = "# X\n## P\n- một dòng danh sách\n" + " ".join(["chữ"] * 25) + "\n"
    d, e = parse_md(bad); M, e2 = normalize(d, "vi"); er = check_lines(M, "vi")
    assert any("danh sách" in x and "sửa:" in x for x in er) and any("25 chữ" in x for x in er), er
    d, e = parse_md("lẻ loi\n"); assert any("dòng 1" in x for x in e)
    # both: thiếu cặp
    M, e = normalize({"title": {"en": "T", "vi": "T"}, "pages": [{"title": "P", "lines": ["x"]}]}, "both"); assert e
    good = {"title": {"en": "A report", "vi": "Báo cáo"}, "pages": [{"title": {"en": "Page", "vi": "Trang"}, "lines": [{"label": {"en": "Scope", "vi": "Phạm vi"}, "text": {"en": "Mac mini only.", "vi": "Chỉ Mac mini."}}]}]}
    M, e = normalize(good, "both"); assert not e, e; assert not check_lines(M, "both")
    assert "⟦" in build_md(M, "both", now=0)
    badste = dict(good); badste["pages"] = [{"title": {"en": "P", "vi": "T"}, "lines": [{"label": {"en": "A", "vi": "A"}, "text": {"en": "Use the PM tool.", "vi": "Dùng."}}]}]
    M, e = normalize(badste, "both"); assert any("EN" in x and "sửa:" in x for x in check_lines(M, "both")), "STE phải bắt viết tắt PM"
    for code, k in (("2a12295", "sha"), ("room:vinh-hong", "room"), ("a/b", "branch"), ("s0123456789ab", "reopen")):
        assert kind_of(code) == k, code
    print("doc_report selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src", nargs="?", help="nguồn .md (chỉ --lang vi) hoặc .json")
    ap.add_argument("--out", default=".", help="thư mục ghi rp-doc-<giờ>.md / .html")
    ap.add_argument("--lang", choices=("vi", "both"), default="vi", help="vi (mặc định): một ngôn ngữ, không STE; both: JSON cặp {en, vi}, kiểm STE, có nút EN/VI")
    ap.add_argument("--build", action="store_true", help="chạy book.py của book-layout để ra .html")
    ap.add_argument("--check", action="store_true", help="chỉ kiểm nguồn, không ghi tệp")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.src:
        ap.error("thiếu nguồn")
    doc, errs = load(a.src, a.lang)
    M, e2 = normalize(doc, a.lang); errs += e2
    if not errs:
        errs += check_lines(M, a.lang)
    if errs:
        print(f"nguồn chưa đạt ({len(errs)} lỗi); sửa rồi chạy lại:", file=sys.stderr)
        for x in errs:
            print("  - " + x, file=sys.stderr)
        sys.exit(1)
    if a.check:
        print("nguồn đạt"); return
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    md = out / ("rp-doc-" + time.strftime("%Y%m%d-%H%M") + ".md")
    md.write_text(build_md(M, a.lang), encoding="utf-8"); print(md)
    if a.build:
        html = md.with_suffix(".html")
        subprocess.run([sys.executable, str(book_py()), str(md), "-o", str(html)], check=True)
        html.write_text(T.finish(html.read_text(encoding="utf-8"), lang="vi" if a.lang == "vi" else None, mode="doc"), encoding="utf-8"); print(html)
        print("tiếp theo: node <book-layout>/scripts/check.mjs " + str(html) + " ; node " + str(Path(__file__).with_name("check_lang.mjs")) + " " + str(html) + " <thư mục ảnh>  (macOS 13: PW_CHANNEL=chrome)")


if __name__ == "__main__":
    main()
