#!/usr/bin/env python3
"""catalog.py — sinh `catalog.json` + đóng dấu `version.json` của repo Rheinmir/skills (đọc từ đĩa, không chép tay).

    python3 tools/catalog.py            # ghi catalog.json (version lấy từ version.json)
    python3 tools/catalog.py --check    # rc 2 nếu catalog.json lệch đĩa HOẶC bề mặt đổi mà version chưa bump
    python3 tools/catalog.py --update   # bề mặt đổi → bump patch version.json + ghi catalog.json

Bề mặt (catalog_sha) = sha256 của danh sách (tên · loop · description · requires · sha mọi file của skill). Đổi một
dòng SKILL.md là bề mặt đổi → CI bắt bump version, để máy người dùng và MCP (`/healthz`) so được "bản skill mình đang
dùng" với "bản chuẩn". Frontmatter đọc bằng parser của harness/scripts/skill-requires.py (repo setup, hoặc bản global
~/.claude/harness) — không chép parser sang đây để khỏi lệch.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CATALOG = ROOT / "catalog.json"
VERSION = ROOT / "version.json"


def load_skill_requires():
    cands = []
    for base in (os.environ.get("OVERSTACK_SETUP"), os.environ.get("HARNESS_HOME"), str(Path.home() / ".claude" / "harness")):
        if base:
            cands.append(Path(base).expanduser() / "harness" / "scripts" / "skill-requires.py")
    for c in cands:
        if c.is_file():
            spec = importlib.util.spec_from_file_location("skill_requires", c)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m
    sys.exit("[catalog] không tìm thấy harness/scripts/skill-requires.py — đặt OVERSTACK_SETUP=<checkout Rheinmir/setup> "
             "hoặc cài harness global (~/.claude/harness)")


def skill_sha(d: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(x for x in d.rglob("*") if x.is_file()):
        h.update(str(p.relative_to(d)).encode()); h.update(b"\0"); h.update(p.read_bytes()); h.update(b"\0")
    return h.hexdigest()[:16]


def build(sr, ver: dict) -> dict:
    skills = []
    for d in sr.iter_skills(SKILLS):
        text = (d / "SKILL.md").read_text(encoding="utf-8", errors="ignore")
        fm = sr.frontmatter(text)
        req = sr.parse_requires(text)
        meta = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
        skills.append({
            "name": str(fm.get("name") or d.name),
            "dir": str(d.relative_to(ROOT)),
            "external": d.parent.name == "external",
            "loop": meta.get("loop") or "utils",
            "description": " ".join(str(fm.get("description") or "").split()),
            "model_invocable": not bool(fm.get("disable-model-invocation")),
            "requires": {k: v for k, v in req.items() if k != "loop" and v},
            "sha": skill_sha(d),
        })
    surface = "\n".join(f"{s['name']}|{s['loop']}|{s['description']}|{json.dumps(s['requires'], sort_keys=True)}|{s['sha']}" for s in skills)
    return {"schema": 1, "version": ver.get("version", "1.0.0"), "harness_floor": ver.get("harness_floor"),
            "catalog_sha": hashlib.sha256(surface.encode()).hexdigest()[:16], "count": len(skills), "skills": skills}


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def bump_patch(v: str) -> str:
    a = [int(x) for x in v.split(".")[:3]] + [0, 0, 0]
    return f"{a[0]}.{a[1]}.{a[2] + 1}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--update", action="store_true")
    a = ap.parse_args(argv)
    sr = load_skill_requires()
    first = not VERSION.is_file()
    ver = {"schema": 1, "version": "1.0.0", "harness_floor": "1.3.127"} if first else json.loads(VERSION.read_text(encoding="utf-8"))
    cat = build(sr, ver)
    if a.check:
        probs = []
        if ver.get("catalog_sha") != cat["catalog_sha"]:
            probs.append(f"bề mặt skill đổi (catalog_sha {ver.get('catalog_sha')} → {cat['catalog_sha']}) mà version.json chưa bump")
        if not CATALOG.is_file():
            probs.append("catalog.json chưa có")
        else:
            cur = json.loads(CATALOG.read_text(encoding="utf-8"))
            if {k: v for k, v in cur.items() if k != "generated_at"} != {k: v for k, v in cat.items() if k != "generated_at"}:
                probs.append("catalog.json lệch đĩa")
        if probs:
            print("[catalog] LỆCH: " + " · ".join(probs) + "\n  → python3 tools/catalog.py --update", file=sys.stderr)
            return 2
        print(f"[catalog] ✓ {cat['count']} skill · v{cat['version']} · catalog_sha {cat['catalog_sha']}")
        return 0
    if a.update and not first and ver.get("catalog_sha") != cat["catalog_sha"]:
        ver["version"] = bump_patch(ver.get("version", "1.0.0"))
        cat["version"] = ver["version"]
    ver.update({"schema": 1, "catalog_sha": cat["catalog_sha"], "count": cat["count"],
                "generated_at": datetime.date.today().isoformat(), "generated_commit": git_commit()})
    VERSION.write_text(json.dumps(ver, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cat["generated_at"] = ver["generated_at"]
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[catalog] ghi catalog.json ({cat['count']} skill) · version.json v{ver['version']} · catalog_sha {cat['catalog_sha']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
