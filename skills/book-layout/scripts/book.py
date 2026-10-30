#!/usr/bin/env python3
"""book.py: markdown có vài dấu khối → MỘT trang HTML dạng sách / tạp chí (khuôn assets/book.css). Chỉ stdlib, Python 3.9.

Agent chỉ viết nội dung; layout lấy từ khuôn nên tốn 0 token đầu ra.
    python3 book.py in.md -o out.html
    python3 book.py --selftest

Cú pháp (mỗi dòng «=== <kiểu>» mở một trang; hai trang liền nhau thành một trải):
    ---                       đầu tệp: front matter  brand: / date: / vol: / footer:
    === cover | toc | page | cycle | image          kiểu trang (page = trang thường)
    ^ chữ                     dòng nhỏ in hoa trên tiêu đề (kicker)
    # Dòng một / *dòng hai*   tiêu đề; « / » xuống dòng, *…* tô màu nhấn
    ### Tiêu đề nhỏ           h3
    > chữ                     câu dẫn (lead)
    ---                       gạch vàng ngắn
    " câu trích -- nguồn      trích dẫn lớn
    ! 325 | chữ | nguồn       khối số liệu nổi bật
    - chữ                     danh sách tích xanh (khung «### …» ngay trên làm tiêu đề khung)
    1. chữ ; ghi chú          các bước đánh số
    * Tiêu đề :: mô tả        danh sách có icon (ở trang cycle: ba nút của vòng)
    01 | Tiêu đề | mô tả | 06 dòng mục lục (trang toc)
    ~ chữ / *gạch vàng*       chữ viết tay góc dưới phải
    ![mô tả](ảnh.jpg)         ảnh; ở trang image là ảnh tràn trang
    ![mô tả](thao-tac.gif "tinh.png")   GIF kèm ảnh tĩnh cho người tắt chuyển động (xem «Khi nào dùng GIF» trong SKILL.md)
    + 30,40 chữ               ghim chú thích số 1, 2… trên ảnh/GIF ngay trên, ở x=30 %, y=40 %; chữ hiện thành danh sách đánh số dưới khung
    @ chữ                     tiêu đề chạy góc phải trang (vd «Chương 2»)
    dòng khác                 đoạn văn (**đậm** được)
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;700;800&family=Patrick+Hand&display=swap&subset=vietnamese" rel="stylesheet">'
LEAF = '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="leaf" viewBox="0 0 24 24"><path d="M4 20C4 10 10 4 20 4c0 10-6 16-16 16z" fill="#5f8a3a"/><path d="M4 20C8 14 12 10 16 8" stroke="#f2c230" stroke-width="1.6" fill="none"/></symbol></svg>'
ICONS = [  # vòng lặp cho danh sách có icon và nút của vòng
    '<path d="M3 11l9-7 9 7v9H3z"/><path d="M9 20v-6h6v6"/>', '<path d="M4 6h16M4 12h10M4 18h7"/>',
    '<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>', '<path d="M4 5h16v11H9l-5 4z"/>',
    '<path d="M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.5 6.7 19.4l1.2-6L3.4 9.3l6-.7z"/>', '<path d="M5 12.5l4.5 4.5L19 7.5"/>']
NODE_BG = [("var(--sun)", "#1d1d1b"), ("var(--green)", "#fff"), ("var(--ink)", "#f2c230")]
NODE_POS = ["left:4%;top:4%", "right:0;top:34%", "left:8%;bottom:0"]
ART = {  # minh hoạ mặc định khi không có ảnh (SVG, không tải gì)
    "cover": '<svg viewBox="0 0 400 260"><rect width="400" height="260" fill="#eef0e6"/><circle cx="292" cy="78" r="38" fill="#f2c230"/><path d="M0 190 L70 120 L130 170 L200 92 L270 160 L330 118 L400 170 V260 H0z" fill="#b9c99a"/><path d="M0 220 L90 160 L170 210 L250 150 L330 205 L400 175 V260 H0z" fill="#7fa257"/><path d="M0 245 L120 205 L220 240 L320 210 L400 236 V260 H0z" fill="#4f7531"/></svg>',
    "image": '<svg viewBox="0 0 400 600" preserveAspectRatio="xMidYMid slice"><defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8fb4c9"/><stop offset=".45" stop-color="#f3d9a0"/><stop offset=".62" stop-color="#e9a65a"/></linearGradient></defs><rect width="400" height="600" fill="url(#sky)"/><circle cx="250" cy="300" r="30" fill="#fff4cf"/><path d="M0 330 L80 270 L150 310 L230 250 L310 300 L400 260 V600 H0z" fill="#6f8a6a"/><path d="M0 380 L100 320 L190 370 L290 320 L400 360 V600 H0z" fill="#4f6b45"/><path d="M0 440 L120 390 L240 430 L400 400 V600 H0z" fill="#3c5634"/></svg>',
}
DIM = '<div style="position:absolute;inset:0;background:linear-gradient(transparent 45%,#0000008c)"></div>'
KINDS = ("cover", "toc", "page", "cycle", "image")


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"\*(.+?)\*", r'<span class="accent">\1</span>', s)


def lines_br(s, u=False):
    out = "<br>".join(inline(x.strip()) for x in s.split(" / "))
    return out.replace('<span class="accent">', "<u>").replace("</span>", "</u>") if u else out


def icon(i, stroke="#5f8a3a"):
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICONS[i % len(ICONS)]}</svg>'


def img(src, alt, poster=""):
    """Ảnh hoặc GIF. GIF kèm poster (ảnh tĩnh): người bật «giảm chuyển động» thấy poster thay vì GIF chạy."""
    tag = f'<img src="{html.escape(src)}" alt="{html.escape(alt)}" loading="lazy" decoding="async" style="display:block;width:100%;height:100%;object-fit:cover">'
    if not poster:
        return tag
    return f'<picture style="display:block;width:100%;height:100%"><source media="(prefers-reduced-motion: reduce)" srcset="{html.escape(poster)}">{tag}</picture>'


def parse(text):
    meta, pages = {}, []
    t = text.lstrip("﻿")
    if t.startswith("---\n"):
        head, _, t = t[4:].partition("\n---\n")
        for ln in head.splitlines():
            k, _, v = ln.partition(":")
            if v.strip():
                meta[k.strip()] = v.strip()
    for ln in t.splitlines():
        m = re.match(r"^===\s*(\w+)?\s*$", ln)
        if m:
            kind = (m.group(1) or "page").lower()
            if kind not in KINDS:
                raise SystemExit(f"kiểu trang lạ: {kind} (có: {', '.join(KINDS)})")
            pages.append({"kind": kind, "lines": []})
        elif pages:
            pages[-1]["lines"].append(ln.rstrip())
        elif ln.strip():
            raise SystemExit("nội dung phải nằm sau một dòng «=== <kiểu>»")
    return meta, pages


def render_page(pg, no, meta):
    kind, L = pg["kind"], [x for x in pg["lines"]]
    brand = html.escape(meta.get("brand", "Tài liệu"))
    run_r, h_done, body, items, steps, checks, icons_, toc, hand, image, panel_t, figs = "", False, [], [], [], [], [], [], "", None, "", []

    def flush():
        nonlocal panel_t
        if checks:
            body.append(f'<div class="panel">{f"<h3>{panel_t}</h3>" if panel_t else ""}<ul class="checks">{"".join(f"<li>{c}</li>" for c in checks)}</ul></div>')
        if steps:
            body.append(f'<div class="panel">{f"<h3>{panel_t}</h3>" if panel_t else ""}<ol class="steps">{"".join(steps)}</ol></div>')
        if icons_ and kind != "cycle":
            body.append(f'{f"<h3 class=ihd>{panel_t}</h3>" if panel_t and not checks and not steps else ""}<ul class="ilist">{"".join(icons_)}</ul>')
        checks.clear(); steps.clear()
        if kind != "cycle":
            icons_.clear()
        panel_t = ""

    for ln in L:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("@ "):
            run_r = inline(s[2:])
        elif s.startswith("^ "):
            body.append(f'<p class="kick">{inline(s[2:])}</p>')
        elif s.startswith("### "):
            flush(); panel_t = inline(s[4:])
        elif s.startswith("# "):
            tag = "h1" if kind == "cover" else "h2"
            body.append(f"<{tag}>{lines_br(s[2:])}</{tag}>"); h_done = True
        elif s.startswith("> "):
            body.append(f'<p class="lead">{inline(s[2:])}</p>')
        elif s == "---":
            body.append('<div class="rule"></div>')
        elif s.startswith('" '):
            q, _, c = s[2:].partition(" -- ")
            body.append(f'<figure class="quote"><span class="mk">“</span><blockquote>{inline(q)}</blockquote>{f"<cite>{inline(c)}</cite>" if c else ""}</figure>')
        elif s.startswith("! "):
            p = [x.strip() for x in s[2:].split("|")] + ["", ""]
            body.append(f'<div class="stat"><div class="big">{inline(p[0])}</div><p>{inline(p[1])}</p>{f"<cite>{inline(p[2])}</cite>" if p[2] else ""}</div>')
        elif re.match(r"^\d+\.\s", s):
            t, _, n = re.sub(r"^\d+\.\s+", "", s).partition(" ; ")
            steps.append(f'<li><span>{inline(t)}{f"<small>{inline(n)}</small>" if n else ""}</span></li>')
        elif s.startswith("- "):
            checks.append(inline(s[2:]))
        elif s.startswith("* "):
            t, _, d = s[2:].partition(" :: ")
            i = len(icons_)
            if kind == "cycle":
                bg, st = NODE_BG[i % 3]
                icons_.append(f'<div class="node" style="{NODE_POS[i % 3]}"><i style="background:{bg}">{icon(i + 3, st)}</i><div><b>{inline(t)}</b><span>{inline(d)}</span></div></div>')
            else:
                icons_.append(f'<li><i>{icon(i)}</i><div><h3>{inline(t)}</h3><p>{inline(d)}</p></div></li>')
        elif kind == "toc" and re.match(r"^\d+\s*\|", s):
            p = [x.strip() for x in s.split("|")] + ["", "", ""]
            toc.append(f'<li><span class="n">{inline(p[0])}</span><div><h3>{inline(p[1])}</h3><p>{inline(p[2])}</p></div><span class="pg">{inline(p[3])}</span></li>')
        elif s.startswith("~ "):
            hand = f'<div class="two"><span></span><span class="hand">{lines_br(s[2:], u=True)}</span></div>'
        elif m := re.match(r'^!\[(.*?)\]\((\S+?)(?:\s+"(.*?)")?\)$', s):
            image = (m.group(2), m.group(1), m.group(3) or "")
            if kind not in ("image", "cover"):
                figs.append((image, [])); body.append(f"\x00{len(figs) - 1}\x00")
        elif (m := re.match(r"^\+\s*(\d{1,3})\s*,\s*(\d{1,3})\s+(.+)$", s)) and figs:
            figs[-1][1].append((min(int(m.group(1)), 100), min(int(m.group(2)), 100), m.group(3)))
        else:
            flush(); body.append(f"<p>{inline(s)}</p>")
    flush()
    for i, (im, pins) in enumerate(figs):   # khung ảnh / GIF + ghim chú thích đánh số (vị trí %, chữ giải thích bên dưới)
        dots = "".join(f'<b class="pin" style="left:{x}%;top:{y}%">{n}</b>' for n, (x, y, _) in enumerate(pins, 1))
        notes = f'<ol class="notes">{"".join(f"<li>{inline(t)}</li>" for _, _, t in pins)}</ol>' if pins else ""
        body = [f'<figure class="photo">{img(*im).replace("height:100%", "height:auto")}{dots}</figure>{notes}' if b == f"\x00{i}\x00" else b for b in body]
    if toc:
        body.append(f'<ol class="toc">{"".join(toc)}</ol>')
    if kind == "cycle":
        ring = ('<svg class="ring" viewBox="0 0 100 100" aria-hidden="true"><defs><marker id="ah" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10z" fill="#8a8a82"/></marker></defs>'
                '<circle cx="50" cy="52" r="15" fill="#edf1e2"/><use href="#leaf" x="41" y="43" width="18" height="18"/>'
                + "".join(f'<path d="{d}" fill="none" stroke="#8a8a82" stroke-width=".6" stroke-dasharray="1.6 1.6" marker-end="url(#ah)"/>' for d in ("M36 30 Q50 22 64 30", "M72 50 Q74 64 64 74", "M38 76 Q26 66 28 50")) + "</svg>")
        body.append(f'<div class="cycle">{ring}{"".join(icons_[:3])}</div>')
    foot = f'<div class="foot"><span>{html.escape(meta.get("footer", meta.get("brand", "")))}</span><span>{no:03d}</span></div>'
    left = f'<span class="brand"><svg><use href="#leaf"/></svg>{brand}</span>' if no % 2 or kind in ("cover", "image") else "<span></span>"
    right = f'{html.escape(meta.get("date", ""))}<br>{html.escape(meta.get("vol", ""))}' if kind == "cover" else (run_r or f"{no:03d}")
    run = f'<div class="run">{left}<span class="vol">{right}</span></div>'
    if kind == "image":
        scene = img(*image) if image else ART["image"]
        return f'<article class="page bleed"><div class="scene" aria-hidden="true">{scene}</div>{DIM}{run}<div class="over">{"".join(body)}</div>{foot}</article>'
    if kind == "cover":
        art = img(*image).replace("height:100%", "height:auto") if image else ART["cover"]
        body.append(f'<div class="art">{art}</div>')
    return f'<article class="page{" cover" if kind == "cover" else ""}">{run}{"".join(body)}{hand}{foot}</article>'


def build(text):
    meta, pages = parse(text)
    if not pages:
        raise SystemExit("chưa có trang nào (thêm dòng «=== cover»)")
    css = (HERE.parent / "assets" / "book.css").read_text(encoding="utf-8")
    arts = [render_page(p, i + 1, meta) for i, p in enumerate(pages)]
    spreads = "".join(f'<section class="spread">{"".join(arts[i:i + 2])}</section>' for i in range(0, len(arts), 2))
    title = html.escape(meta.get("title", meta.get("brand", "Tài liệu")))
    return (f'<!doctype html>\n<html lang="vi">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f"<title>{title}</title>\n{FONTS}\n<style>\n{css}</style>\n</head>\n<body>\n{LEAF}\n<main class=\"book\">{spreads}</main>\n</body>\n</html>\n")


def selftest():
    out = build("---\nbrand: Sổ tay\n---\n=== cover\n^ Kicker\n# Giữ lại / *mọi phiên.*\n> Dẫn\n---\n=== toc\n# Mục lục\n01 | Một | mô tả | 06\n=== cycle\n* A :: a\n* B :: b\n* C :: c\n"
                "=== page\n@ Chương 2\n\" Trích -- Nguồn\n! 325 | phiên | đo\n### Thử ngay\n- một\n- hai\n1. bước ; ghi chú\n### Nhóm icon\n* Icon :: mô tả\n~ Viết / *tay*\n=== image\n# Ảnh / tràn\n")
    for want in ('<h1>Giữ lại<br><span class="accent">mọi phiên.</span></h1>', 'class="toc"', 'class="cycle"', 'class="quote"', 'class="stat"',
                 "<h3>Thử ngay</h3>", 'class="checks"', 'class="steps"', "<small>ghi chú</small>", 'class="ilist"', "<u>tay</u>", 'page bleed', "Chương 2", ">005<"):
        assert want in out, want
    assert out.count('<section class="spread">') == 3, out.count('<section class="spread">')
    g = build('=== page\n![Bấm Save](save.gif "save.png")\n')
    assert 'srcset="save.png"' in g and 'src="save.gif"' in g and "prefers-reduced-motion" in g, "GIF + poster"
    a = build('=== page\n![Lưu](save.gif "save.png")\n+ 80,10 Bấm Save\n+ 50,90 Toast Đã lưu\n')
    assert '<b class="pin" style="left:80%;top:10%">1</b>' in a and "<li>Toast Đã lưu</li>" in a and a.count('class="pin"') == 2, "ghim chú thích"
    assert "<picture" not in build("=== page\n![a](a.gif)\n"), "GIF không poster: img trần"
    assert "<script" not in build("=== page\n<script>alert(1)</script>\n"), "phải escape HTML"
    print("book.py selftest: ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", nargs="?")
    ap.add_argument("-o", "--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest(); sys.exit(0)
    if not a.src:
        ap.error("cần tệp markdown")
    html_out = build(Path(a.src).read_text(encoding="utf-8"))
    out = Path(a.out or Path(a.src).with_suffix(".html"))
    out.write_text(html_out, encoding="utf-8")
    print(out)
