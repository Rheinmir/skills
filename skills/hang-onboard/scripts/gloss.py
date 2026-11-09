#!/usr/bin/env python3
"""Ghi thuật ngữ tiếng Anh ngay cạnh thuật ngữ tiếng Việt: bề mặt (surface).

  gloss.py <tệp .md hoặc .json> ...     ghi đè tại chỗ, chạy lại không nhân đôi
  gloss.py --demo

Mỗi thuật ngữ chỉ ghi ở lần xuất hiện đầu của một trang .md, hoặc của một chuỗi JSON.
Bỏ qua frontmatter, khối mã, `mã`, liên kết, [[wikilink]] và khoá JSON kỹ thuật.
Gặp thuật ngữ mới thì thêm vào TERMS, thuật ngữ dài đặt trước.
"""
import json, re, sys

TERMS = [
    ("lớp ngữ nghĩa", "semantic layer"), ("sơ đồ khối", "block diagram"), ("sơ đồ trình tự", "sequence diagram"),
    ("sơ đồ quan hệ", "relationship diagram"), ("cơ sở dữ liệu", "database"), ("CSDL", "database"),
    ("kho tri thức", "knowledge store"), ("đoạn trích", "passage"), ("bản gốc", "original"),
    ("khoá ngoại|khóa ngoại", "foreign key"), ("khoá chính|khóa chính", "primary key"), ("khoá|khóa", "key"),
    ("bảng cầu", "bridge table"), ("đường join", "join path"), ("tìm đường", "path finding"),
    ("tìm toàn văn", "full-text search"), ("toàn văn", "full-text"), ("chỉ mục", "index"),
    ("mô hình hoá|mô hình hóa", "modeling"), ("lấy mẫu", "sampling"), ("suy luận", "inference"),
    ("thuộc tính", "attribute"), ("thực thể", "entity"), ("quan hệ", "relationship"), ("truy vấn", "query"),
    ("bề mặt", "surface"), ("mã nguồn", "source code"), ("lớp", "layer"), ("lõi", "core"), ("luồng", "flow"), ("miền", "domain"),
    ("nền tảng", "foundation"), ("chặng", "stage"), ("độ phủ", "coverage"), ("nhật ký", "log"),
    ("chỉ đọc", "read-only"), ("xác thực", "authentication"), ("quét", "scan"), ("công cụ", "tool"),
    ("nguồn(?! gốc)", "source"), ("đồng bộ", "sync"), ("chuẩn hoá|chuẩn hóa", "normalize"), ("thực thi", "execute"),
]
ALL = re.compile("|".join(f"(?<![\\w-])(?:{v})(?![\\w-])" for v, _ in TERMS), re.I)
EN = [(re.compile(f"^(?:{v})$", re.I), e) for v, e in TERMS]
SKIP_KEYS = {"file", "color", "line", "img", "x", "y", "w", "h", "cost", "ver"}
PROTECT = re.compile(r"```.*?```|`[^`\n]*`|\[\[[^\]]*\]\]|\]\([^)]*\)|https?://\S+|^---\n.*?\n---\n", re.S | re.M)


def _sub(text, done):
    def one(m):
        w = m.group(0)
        en = next(e for r, e in EN if r.match(w))
        key = en
        after = text[m.end():m.end() + len(en) + 3].lower()
        if after.startswith(f" ({en.lower()}") or after.startswith(" ("):
            done.add(key)
            return w
        if key in done:
            return w
        done.add(key)
        return f"{w} ({en})"
    return ALL.sub(one, text)


def gloss_text(text, done=None):
    """Gloss phần văn xuôi, giữ nguyên phần được bảo vệ. done dùng chung cả trang."""
    done = set() if done is None else done
    out, pos = [], 0
    for m in PROTECT.finditer(text):
        out.append(_sub(text[pos:m.start()], done))
        out.append(m.group(0))
        pos = m.end()
    out.append(_sub(text[pos:], done))
    return "".join(out)


def gloss_json(o, key=None):
    if isinstance(o, str):
        return o if key in SKIP_KEYS else gloss_text(o)
    if isinstance(o, list):
        return [gloss_json(x, key) for x in o]
    if isinstance(o, dict):
        return {k: gloss_json(v, k) for k, v in o.items()}
    return o


def missing(md):
    """Trang .md còn thuật ngữ chưa gloss không."""
    return gloss_text(md) != md


def demo():
    assert gloss_text("Bề mặt và bề mặt") == "Bề mặt (surface) và bề mặt"
    assert gloss_text(gloss_text("Lớp ngữ nghĩa, lớp")) == "Lớp ngữ nghĩa (semantic layer), lớp (layer)"
    assert gloss_text("`bề mặt` [[lớp]] bề mặt") == "`bề mặt` [[lớp]] bề mặt (surface)"
    assert gloss_text("nguồn gốc") == "nguồn gốc" and gloss_text("nguồn") == "nguồn (source)"
    assert gloss_text("khoá ngoại") == "khoá ngoại (foreign key)"
    assert gloss_text("bề mặt (surface) rồi lớp") == "bề mặt (surface) rồi lớp (layer)"
    d = gloss_json({"file": "lớp.py", "t": "Lớp", "actors": ["CSDL của bạn"], "steps": [{"from": "CSDL của bạn"}]})
    assert d["file"] == "lớp.py" and d["t"] == "Lớp (layer)" and d["actors"][0] == d["steps"][0]["from"]
    assert not missing(gloss_text("bề mặt, lớp, luồng")) and missing("bề mặt")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
        print("demo ok")
        sys.exit(0)
    for f in sys.argv[1:]:
        raw = open(f).read()
        new = json.dumps(gloss_json(json.loads(raw)), ensure_ascii=False, indent=1) if f.endswith(".json") else gloss_text(raw)
        open(f, "w").write(new)
