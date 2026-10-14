#!/usr/bin/env python3
"""registry.py — bề mặt phát hành skill không được lệch nhau (kế thừa skill-registry.py của setup, bỏ phần AGENT/CLAUDE/LOOP_MAP).

    python3 tools/registry.py            # báo cáo
    python3 tools/registry.py --check    # rc 2 khi lệch

Kiểm:
  • mỗi `skills/<tên>/SKILL.md` và `skills/external/<tên>/SKILL.md` có frontmatter YAML parse được (CLI `skills` BỎ QUA im lặng
    skill có YAML hỏng → skill không bao giờ tới người dùng), có `name` == tên thư mục, có `description` không rỗng;
  • `metadata.loop` ∈ {wiki-loop, dev-loop, orchestrate, utils};
  • tên skill duy nhất giữa native và external;
  • `.claude-plugin/marketplace.json` liệt kê đúng tập thư mục (`./skills/<dir>`), không thừa, không thiếu (trừ allowlist);
  • `skills.provenance.json` có entry cho mọi skill (sổ nguồn gốc — kiểm checksum bằng fdk/tools/skill-provenance.py của setup).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
MARKET = ROOT / ".claude-plugin" / "marketplace.json"
PROV = ROOT / "skills.provenance.json"
LOOPS = {"wiki-loop", "dev-loop", "orchestrate", "utils"}
# cố ý không publish lên marketplace (skill của riêng framework)
MARKET_ALLOWLIST = {"fdk"}


def frontmatter_text(text: str):
    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---", text, re.S)
    return m.group(1) if m else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    try:
        import yaml
    except ImportError:
        yaml = None
    probs: list[str] = []
    dirs = sorted(p.parent for p in [*SKILLS.glob("*/SKILL.md"), *SKILLS.glob("external/*/SKILL.md")])
    names: dict[str, Path] = {}
    for d in dirs:
        text = (d / "SKILL.md").read_text(encoding="utf-8", errors="ignore")
        fm = frontmatter_text(text)
        if fm is None:
            probs.append(f"{d.name}: không có frontmatter"); continue
        data = None
        if yaml is not None:
            try:
                data = yaml.safe_load(fm)
            except Exception as e:
                probs.append(f"{d.name}: YAML hỏng ({type(e).__name__}) — CLI skills sẽ bỏ qua im lặng"); continue
        else:
            data = {k.strip(): v.strip() for k, v in (ln.split(":", 1) for ln in fm.splitlines() if ":" in ln and not ln.startswith(" "))}
        if not isinstance(data, dict):
            probs.append(f"{d.name}: frontmatter không phải map"); continue
        nm = str(data.get("name") or "")
        if nm != d.name:
            probs.append(f"{d.name}: name '{nm}' ≠ tên thư mục")
        if not str(data.get("description") or "").strip():
            probs.append(f"{d.name}: thiếu description")
        meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        loop = meta.get("loop")
        if loop not in LOOPS:
            probs.append(f"{d.name}: metadata.loop '{loop}' không hợp lệ (cần {sorted(LOOPS)})")
        if d.name in names:
            probs.append(f"{d.name}: trùng tên với {names[d.name].relative_to(ROOT)}")
        names[d.name] = d
    # marketplace
    try:
        mk = json.loads(MARKET.read_text(encoding="utf-8"))
        listed = set()
        for pl in mk.get("plugins", []):
            for s in pl.get("skills", []):
                listed.add(Path(str(s)).name)
        missing = sorted(n for n in names if n not in listed and n not in MARKET_ALLOWLIST)
        extra = sorted(n for n in listed if n not in names)
        if missing:
            probs.append(f"marketplace.json thiếu {len(missing)} skill: {', '.join(missing[:8])}")
        if extra:
            probs.append(f"marketplace.json liệt kê skill không có trên đĩa: {', '.join(extra[:8])}")
    except Exception as e:
        probs.append(f"marketplace.json không đọc được: {e}")
    # provenance entries
    try:
        pv = json.loads(PROV.read_text(encoding="utf-8")).get("skills", {})
        unrec = sorted(n for n in names if n not in pv)
        if unrec:
            probs.append(f"skills.provenance.json chưa có entry: {', '.join(unrec[:8])} — record bằng fdk/tools/skill-provenance.py")
    except Exception as e:
        probs.append(f"skills.provenance.json không đọc được: {e}")
    print(f"[registry] {len(dirs)} skill dir · {sum(1 for d in dirs if d.parent.name == 'external')} external · "
          f"{len(names)} tên duy nhất · {len(probs)} vấn đề")
    for p in probs:
        print("  ✗ " + p)
    if a.check and probs:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
