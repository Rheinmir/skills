# Rheinmir/skills — bộ skill của overstack, tách khỏi framework

106 skill (83 native + 23 vendored trong `skills/external/`) cho Claude Code · OpenCode · Antigravity · Cursor. Engine
(validator, hook, script) vẫn ở [Rheinmir/setup](https://github.com/Rheinmir/setup) và được cài global `~/.claude/harness`;
repo này chỉ chứa **văn bản skill** + hợp đồng phụ thuộc của từng skill.

## Cài / cập nhật

```bash
npx -y skills add rheinmir/skills#main --global --all      # chỉ skill (≈45 s), không đụng harness
curl -fsSL https://raw.githubusercontent.com/Rheinmir/setup/orca/harness/poc-vendor-neutral/bootstrap.sh | bash   # trọn bộ
python3 ~/.claude/harness/harness/scripts/skill-requires.py check --installed   # skill nào thiếu bin/script/harness floor
```

## Hợp đồng phụ thuộc (frontmatter mỗi SKILL.md)

```yaml
metadata:
  loop: dev-loop                      # wiki-loop | dev-loop | orchestrate | utils
  requires:
    harness: ">=1.3.127"              # sàn template_version của ~/.claude/harness/version.json
    bin: [python3, node]              # binary phải có trong PATH
    scripts: [fdk/tools/medic.py]     # phải có trong ~/.claude/harness (bản global)
    framework_scripts: [fdk/tools/new-skill.py]   # chỉ có trong checkout repo setup (skill lớp C)
```

`requires` được **sinh** bằng grep tất định (`skill-requires.py gen`), CI bắt lệch; `loop` khai tay.

## Sửa một skill

1. Sửa `skills/<tên>/SKILL.md` (skill mới: `python3 <setup>/fdk/tools/new-skill.py --skills-dir skills <tên>`).
2. `python3 <setup>/harness/scripts/skill-requires.py gen --write --skills-dir skills --repo-root <setup>` nếu đổi script/binary gọi.
3. `python3 tools/catalog.py --update` (bump version + catalog.json) · `python3 <setup>/fdk/tools/skill-provenance.py --skills-dir skills --store skills.provenance.json record <tên> --source local-authored` nếu đổi file.
4. `bash tools/check.sh <setup>` xanh → push `main`. Không medic, không harness.yml, không fdk-uat.

## Bố cục

| Đường dẫn | Là gì |
|---|---|
| `skills/<tên>/` · `skills/external/<tên>/` | skill (SKILL.md + references/assets/scripts) |
| `.claude-plugin/marketplace.json` | marketplace cho Claude Code plugin |
| `skills.provenance.json` | sổ nguồn gốc + checksum (external-pull → tamper là đỏ) |
| `evals/skill-resolve/` | golden cho router BM25 (`skill-resolve-eval.py`) |
| `catalog.json` · `version.json` | catalog sinh từ đĩa + dấu phiên bản (MCP `/healthz` công bố) |
| `tools/` | `registry.py` · `catalog.py` · `check.sh` |

## Origin
Tách ngày 2026-10-14 bằng `git subtree split --prefix=skills` từ Rheinmir/setup@5c5cca9 (PLAN `141026-skills-split-PLAN.md` trong setup).
