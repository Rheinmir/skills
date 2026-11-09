#!/usr/bin/env python3
"""Cổng tất định cho output hang-onboard. Chạy từ gốc dự án: rc 0 đạt, rc 1 có lỗi.
Không tin lời worker báo xong: wiki (Origin, wikilink, file:line) và onboard.json (actors, tour, block)."""
import glob, json, os, re, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gloss  # noqa: E402


def line_ok(ref, root="."):
    f, l = ref
    hits = [f] if os.path.exists(os.path.join(root, f)) else glob.glob(os.path.join(root, "**", f), recursive=True)
    return bool(hits) and int(l) <= len(open(os.path.join(root, hits[0]) if hits[0] == f else hits[0], errors="replace").read().splitlines())


def check_json(d, root="."):
    errs = []
    a = d.get("architecture") or {}
    for i, s in enumerate(a.get("sequences") or []):
        actors = set(s.get("actors") or [])
        for j, st in enumerate(s.get("steps") or []):
            for side in ("from", "to"):
                if st.get(side) not in actors:
                    errs.append(f"sequence {i} step {j}: {side}={st.get(side)!r} không có trong actors")
    if len(a.get("sequences") or []) > 3:
        errs.append("quá 3 sơ đồ trình tự")
    if a.get("block") and not (a["block"].get("rows")):
        errs.append("block không có rows")
    for r in (a.get("block") or {}).get("rows") or []:
        for g in r:
            if not g.get("name") or not g.get("blocks"):
                errs.append(f"block group thiếu name hoặc blocks: {g}")
    for l in a.get("layers") or []:
        if not l.get("plain"):
            errs.append(f"layer {l.get('name')!r} thiếu plain (lời thường)")
    if not (d.get("cost") or {}).get("run"):
        errs.append("thiếu cost: chạy scripts/cost_footer.py --json")
    tour = d.get("tour") or []
    if not 5 <= len(tour) <= 15:
        errs.append(f"tour có {len(tour)} bước, cần 5-15")
    seen, prev = set(), None
    for i, s in enumerate(tour):
        g = s.get("group")
        if not g:
            errs.append(f"tour bước {i + 1} thiếu group")
        elif g != prev and g in seen:
            errs.append(f"tour bước {i + 1}: chặng {g!r} bị tách rời")
        seen.add(g)
        prev = g
        if s.get("file") and not line_ok((s["file"], s.get("line") or 1), root):
            errs.append(f"tour bước {i + 1}: sai {s['file']}:{s.get('line')}")
    return errs


def check_wiki(wiki="llmwiki/wiki", root="."):
    errs = []
    pages = glob.glob(f"{wiki}/concepts/*.md") + glob.glob(f"{wiki}/entities/*.md")
    names = {Path(p).stem for p in pages}
    index = open(f"{wiki}/index.md").read() if os.path.exists(f"{wiki}/index.md") else ""
    for p in pages:
        t = open(p).read()
        if "## Origin" not in t:
            errs.append(f"{p}: thiếu ## Origin")
        if gloss.missing(t):
            errs.append(f"{p}: còn thuật ngữ chưa ghi tiếng Anh, chạy scripts/gloss.py")
        if "- **Chi phí:** " not in t:
            errs.append(f"{p}: thiếu dòng chi phí")
        if f"{Path(p).parent.name}/{Path(p).name}" not in index:
            errs.append(f"{p}: thiếu dòng trong index.md")
        errs += [f"{p}: link hỏng [[{w}]]" for w in re.findall(r"\[\[([^\]|#]+)", t) if w not in names]
        errs += [f"{p}: sai {f}:{l}" for f, l in re.findall(r"([\w./-]+\.\w{1,5}):(\d+)", t) if not line_ok((f, l), root)]
    if not pages:
        errs.append("wiki không có trang")
    return errs


def demo():
    good = {"cost": {"run": "x"}, "architecture": {"layers": [{"name": "A", "plain": "x"}], "block": {"rows": [[{"name": "g", "blocks": ["b"]}]]},
            "sequences": [{"actors": ["a", "b"], "steps": [{"from": "a", "to": "b", "label": "x"}]}]},
            "tour": [{"t": str(i), "group": "g"} for i in range(5)]}
    assert check_json(good) == []
    bad = json.loads(json.dumps(good))
    bad["architecture"]["sequences"][0]["steps"][0]["to"] = "z"
    bad["architecture"]["layers"][0]["plain"] = ""
    bad["tour"][1]["group"] = "h"
    bad["tour"] = bad["tour"][:4]
    bad["tour"][0]["file"] = "khong-co.py"
    bad.pop("cost")
    errs = check_json(bad)
    for word in ("không có trong actors", "thiếu plain", "cần 5-15", "khong-co.py", "thiếu cost"):
        assert any(word in e for e in errs), (word, errs)


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
        print("demo ok")
        sys.exit(0)
    jp = sys.argv[1] if len(sys.argv) > 1 else ".overstack/onboard/tmp/onboard.json"
    errs = check_wiki()
    if os.path.exists(jp):
        errs += check_json(json.load(open(jp)))
    print("\n".join(errs) or "check_output: đạt")
    sys.exit(1 if errs else 0)
