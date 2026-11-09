#!/usr/bin/env python3
"""Footer chi phí đo từ transcript. Không có transcript thì báo KHÔNG ĐO ĐƯỢC, không đoán.

  cost_footer.py --session <id>[,<id>] [--since ISO] [--rates rates.json] [--skill SKILL.md]
                 [--stamp <thư mục|tệp .md> ...] [--json onboard.json]

rates.json = kết quả hang_costs(op="rates"). Thiếu thì chỉ ghi token, không ghi tiền.
Token lần chạy là số đo; token để đọc một tệp là ước lượng ký tự/4 và được ghi rõ như vậy.
"""
import argparse, glob, json, os, re, sys, time
from pathlib import Path

LINE = "- **Chi phí:** "


def find(sid):
    home = Path.home()
    roots = [home / ".claude/projects", home / "Library/Application Support/orca/claude-profiles"]
    return next((p for r in roots for p in glob.glob(f"{glob.escape(str(r))}/**/{sid}.jsonl", recursive=True)), None)


def usage(lines, since=None):
    """Cộng usage theo message id: một message có thể ghi nhiều dòng trong transcript."""
    seen, by = set(), {}
    for l in lines:
        try:
            o = json.loads(l)
        except ValueError:
            continue
        m = o.get("message") or {}
        if m.get("role") != "assistant" or not m.get("usage") or (since and o.get("timestamp", "") < since):
            continue
        k = m.get("id") or o.get("requestId")
        if k in seen:
            continue
        seen.add(k)
        u, d = m["usage"], by.setdefault(m.get("model") or "?", dict(calls=0, input=0, cache_w=0, cache_r=0, out=0))
        d["calls"] += 1
        d["input"] += u.get("input_tokens", 0)
        d["cache_w"] += u.get("cache_creation_input_tokens", 0)
        d["cache_r"] += u.get("cache_read_input_tokens", 0)
        d["out"] += u.get("output_tokens", 0)
    return by


def money(by, rates):
    """USD theo bảng giá; None nếu thiếu bảng hoặc thiếu giá của một model."""
    total = 0.0
    for model, d in by.items():
        r = (rates or {}).get("models", {}).get(model)
        if not r:
            return None
        total += (d["input"] * r["in"] + d["cache_w"] * r["cache_w"] + d["cache_r"] * r["cache_r"] + d["out"] * r["out"]) / 1e6
    return total


def k(n):
    return f"{n / 1e6:.1f}M" if n >= 1e6 else f"{n / 1e3:.0f}k" if n >= 1e3 else str(n)


def est(path):
    return round(len(Path(path).read_text(errors="replace")) / 4)


def run_text(by, usd, rates):
    if not by:
        return "không đo được (không có transcript)"
    t = {x: sum(d[x] for d in by.values()) for x in ("calls", "input", "cache_w", "cache_r", "out")}
    s = f"{t['calls']} lượt gọi model ({', '.join(by)}): vào {k(t['input'])}, ghi cache {k(t['cache_w'])}, đọc cache {k(t['cache_r'])}, ra {k(t['out'])}"
    if usd is not None:
        s += f"; ≈ ${usd:.2f} " + ("quy đổi giá API, không phải hoá đơn" if (rates or {}).get("subscription") else "theo giá API")
    return s


def stamp(path, run, skill):
    """Ghi hoặc thay đúng một dòng chi phí, trong ## Origin nếu có. Chạy lại không nhân dòng."""
    t = Path(path).read_text()
    t = re.sub(rf"^{re.escape(LINE)}.*\n?", "", t, flags=re.M)
    size = est(path) if not t else round(len(t) / 4)
    row = f"{LINE}lần chạy: {run}. {skill}Tệp này ≈ {k(size)} token để đọc (ước lượng ký tự/4).\n"
    if "## Origin\n" in t:
        t = t.replace("## Origin\n", "## Origin\n" + row, 1)
    else:
        t = t.rstrip() + "\n\n" + row
    Path(path).write_text(t)


def demo():
    a = {"role": "assistant", "id": "m1", "model": "x", "usage": {"input_tokens": 1000000, "output_tokens": 1000000}}
    rows = [json.dumps({"message": a, "timestamp": "2026-01-02"})] * 2 + ["bad json"]
    by = usage(rows)
    assert by["x"]["calls"] == 1 and by["x"]["out"] == 1000000, by
    assert usage(rows, since="2026-01-03") == {}
    assert money(by, {"models": {"x": {"in": 1, "cache_w": 1, "cache_r": 1, "out": 2}}}) == 3.0
    assert money(by, {"models": {}}) is None and money(by, None) is None
    assert "$" not in run_text(by, None, None) and "không đo được" in run_text({}, None, None)
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "a.md"
        p.write_text("# a\n\n## Origin\n- x\n")
        stamp(p, "R", "")
        stamp(p, "R", "")
        assert p.read_text().count(LINE) == 1 and p.read_text().index(LINE) > p.read_text().index("## Origin")


def main():
    if "--demo" in sys.argv:
        demo()
        print("demo ok")
        return
    a = argparse.ArgumentParser()
    a.add_argument("--session", required=True)
    a.add_argument("--since")
    a.add_argument("--rates")
    a.add_argument("--skill")
    a.add_argument("--stamp", nargs="*", default=[])
    a.add_argument("--json")
    o = a.parse_args()
    by, missing = {}, []
    for sid in o.session.split(","):
        f = find(sid)
        if not f:
            missing.append(sid)
            continue
        for m, d in usage(open(f, errors="replace"), o.since).items():
            cur = by.setdefault(m, dict.fromkeys(d, 0))
            for x in d:
                cur[x] += d[x]
    rates = json.load(open(o.rates)) if o.rates and os.path.exists(o.rates) else None
    usd = money(by, rates)
    run = run_text(by, usd, rates) + f", tính tới {time.strftime('%Y-%m-%d %H:%M')}"
    if missing:
        run += f", thiếu transcript {len(missing)} phiên"
    skill = f"Skill: {Path(o.skill).resolve().parent.name} ≈ {k(est(o.skill))} token mỗi lần nạp (ước lượng). " if o.skill else ""
    files = [m for s in o.stamp for m in (glob.glob(f"{s}/**/*.md", recursive=True) if os.path.isdir(s) else [s])]
    for f in files:
        stamp(f, run, skill)
    if o.json:
        d = json.load(open(o.json))
        d["cost"] = {"run": run, "skill": skill.strip(), "page": f"Dữ liệu trang ≈ {k(est(o.json))} token (ước lượng ký tự/4)."}
        json.dump(d, open(o.json, "w"), ensure_ascii=False, indent=1)
    print(f"Chi phí: lần chạy: {run}. {skill}".strip())


if __name__ == "__main__":
    main()
