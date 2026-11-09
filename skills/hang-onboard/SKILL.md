---
name: hang-onboard
description: "Onboard một codebase và giao việc qua Hang, không cần skill Orca hay opencode. Dựng graph (scan + git history + phân tích tĩnh + layers/tour), domain graph, wiki, trang HTML có sơ đồ khối, sơ đồ trình tự và bản đồ tour. Gọi khi user nói hang-onboard, onboard qua hang, onboard dự án trong phòng Hang, /hang-onboard."
metadata:
  design-standard: "solid-what-how/1"
  contract-version: "1.0.0"
  loop: orchestrate
  requires:
    harness: ">=1.3.127"
    bin: [python3]
    scripts: [fdk/tools/build-wiki-graph.py, fdk/tools/frontend-antipattern.py, fdk/tools/surface-coverage.py, harness/scripts/dep-health.py]
---

# hang-onboard

> Bản của `orca-onboard` giao việc qua **Hang**. Không dùng `orca-dispatch-reference`, `opencode`, `agy`, `kiro-cli`. Pipeline, đầu ra và cổng kiểm giữ nguyên; khác biệt nằm ở mục **Khác `orca-onboard`** cuối tệp.

Onboard codebase via distilled understand-anything pipeline (graph + git history, no plugin), then domain enrichment + wiki + HTML. Mọi việc giao đi đều qua Hang.

## WHAT

### Purpose và context
- **Purpose:** onboard một codebase bất kỳ thành tri thức dùng được: knowledge graph (scan + git history + batch analyze + layers/tour, không plugin), domain graph (domain → flow → step), wiki `llmwiki/wiki/` và trang HTML docs — phần reasoning ở phiên chính, phần cơ học giao một worker Hang hoặc phiên chính tự làm.
- **Trigger (when to use):** "onboard codebase", "analyze codebase", "knowledge graph", "guided tour", `/hang-onboard`, "onboard qua hang".
- **Non-goals:** không cài plugin Understand-Anything; không giao reasoning (domain, architecture, layers/tour) cho worker; không tự viết HTML thô (luôn qua skeleton v2); không bịa file path hay file:line; không nhân bản cú pháp Hang ngoài mục **Giao việc qua Hang**.

### Mental model
`Phase 0 pre-flight/bootstrap → Phase 0.5 GATE (draft + dispatch board → user duyệt) → Phase 1 graph (scan → git history → analyze → merge → layers+tour → validate → [code-graph index]) → Phase 2 domain graph → Phase 3 wiki → Phase 4 HTML (JSON → skeleton v2 → wiki-graph vector) → output report`. Draft `llmwiki/wiki/draft/hang/<DATE>-onboard-<slug>.md` là sổ trạng thái: mỗi phase `pending → in-progress → done`, resume đọc lại từ đó.

### Input và output contract
| | Field | Required? | Ý nghĩa |
|---|---|---|---|
| In | `<path>` | không (mặc định `.`) | thư mục dự án đích; `@<draft>` = resume từ draft có sẵn |
| In | `--full` | không | xoá `.overstack/graph/` rồi rebuild |
| In | `--update` | không | chỉ phân tích lại file đổi từ lần chạy trước (cần graph + `meta.json` có sẵn) |
| In | `--language <lang>` | không | ngôn ngữ output (vi, en, zh, ...) |
| In | `--skip-wiki` | không | bỏ sinh wiki |
| In | duyệt của user ở Phase 0.5 | có | sau khi dispatch board + nội dung propose đã in ra terminal |
| In | Hang (MCP `hang` hoặc `~/.hang/bin/hang-room-hook`), `assets/docs-site-skeleton.html` | Hang: không; skeleton: có | không có Hang thì phiên chính tự làm hết; thiếu skeleton → Phase 4 exit 1 |
| In | `room` | không | phòng Hang để báo tiến độ, hỏi cổng duyệt và giao worker; mặc định là phòng phiên đang ở |
| Out | `.overstack/graph/knowledge-graph.json`, `ONBOARDING.md`, `meta.json` | có | Phase 1 (gate cuối Phase 1 kiểm 2 file đầu) |
| Out | `.overstack/onboard/intermediate/domain-graph.json` | có | Phase 2 |
| Out | `.overstack/onboard/intermediate/surface.json` + `coverage.json` | có | Phase 2 — bề mặt thật @commit + sổ phủ; output report in `N/M mục bề mặt được phủ` (skill `surface-coverage`) |
| Out | `llmwiki/wiki/` (index, concepts, entities) | có trừ `--skip-wiki` | Phase 3; mọi trang có `## Origin` + dòng index |
| Out | `llmwiki/html/onboarding-<slug>.html` + `llmwiki/html/wiki-graph.html` | có (vector fail-open) | Phase 4 |
| Out | draft trạng thái + dòng index/log | có | cập nhật sau MỖI phase |

"Xong" = 4 phase `done` trong draft, HTML tồn tại, output report ghi.

### Rules và capabilities
- RULE-01 (MUST): **DO NOT run Phase 0.5 or Phases 1–4 until Phase 0 completes.** Thứ tự cứng không đảo: Phase 0 (verify `llmwiki/` tồn tại) → Phase 0.5 (tạo draft TRƯỚC rồi mới hỏi user) → Phases 1–4.
- RULE-02 (MUST): `llmwiki/` thiếu → bootstrap ở Phase 0, NEVER defer; bootstrap fail → STOP hoàn toàn, báo lỗi.
- RULE-03 (MUST): Sau MỖI phase → cập nhật status draft NGAY, không dồn tới cuối.
- RULE-04 (MUST): Dispatch board + nội dung propose PHẢI in qua bash (thấy trong terminal) trước câu hỏi gate; dòng Agent Task Assignment trong draft phải khớp board.
- RULE-05 (MUST): **Reasoning ở lại phiên chính, không giao worker.** Worker Hang chỉ điền template wiki và ghép JSON. Render tất định thì dùng script, không giao ai.
- RULE-06 (MUST): **READ BEFORE ACT** — each phase reads all inputs in `READ FIRST` block before any action. Never ask user about something already in a file.
- RULE-07 (MUST): **NO full `knowledge-graph.json` reads after Phase 1** — use `ONBOARDING.md` instead.
- RULE-08 (MUST): Real file paths only — never fabricate; domain graph only references real file:line, verify against code.
- RULE-12 (MUST): Độ phủ của domain graph báo bằng diff với bề mặt thật (`surface-coverage.py check`), dạng `N/M mục`; không bao giờ báo số flow/bài như thể đã giải thích hết app.
- RULE-09 (MUST): Wiki: wikilink format `[[page-name]]`; tour: 5-15 steps, start with project overview.
- RULE-10 (MUST): Phase 4 KHÔNG bao giờ tự viết HTML thô — luôn qua skeleton v2.
- RULE-11 (MUST): code-graph chỉ index khi `dep-health.py --json` báo `status == "ok"` — khai báo trong config ≠ server sống.
- RULE-13 (MUST): **Mọi lệnh có thể treo phải có hạn thời gian cứng** (`perl -e 'alarm N; exec @ARGV' ...`), gồm trình duyệt, worker và mạng. Xong sản phẩm thì báo phòng ngay; bước kiểm tra chậm không được giữ báo cáo lại.
- RULE-14 (MUST): **Không tin lời worker báo xong.** Chạy `scripts/check_output.py`; rc khác 0 thì sửa hoặc tự làm phần đó.
- RULE-15 (MUST): **Sơ đồ do máy xếp.** Sơ đồ khối và sơ đồ trình tự chỉ khai dữ liệu; model không khai toạ độ. Mỗi hình trả lời một câu hỏi, tiêu đề là kết luận. Riêng `architecture.diagram` vẫn khai toạ độ và phải xếp để mũi tên không cắt qua ô.
- RULE-16 (MUST): **Viết cho người mới.** Mỗi layer có `plain` (lời thường), `example` và `files`. Mỗi bước tour có `group` để hiện trên bản đồ.
- RULE-17 (MUST): **Luôn ghi chi phí như footer** trên trang HTML, mọi trang wiki, draft và tin báo phòng. Số do `scripts/cost_footer.py` đo từ transcript, gồm cả phiên worker; không tự gõ, không đoán. Tiền chỉ ghi khi có bảng giá, và ghi rõ là quy đổi khi chạy gói tháng.
- RULE-18 (MUST): **Thuật ngữ có tiếng Anh ngay cạnh:** bề mặt (surface), lớp (layer). Dev Việt không nói các từ này thuần Việt. `scripts/gloss.py` ghi tự động trên trang wiki, `ONBOARDING.md` và `onboard.json`; `check_output.py` đỏ nếu còn sót. Gặp thuật ngữ mới thì thêm vào `TERMS`. Viết SPEC cho worker cũng theo luật này.
- Capabilities: đọc repo đích + lịch sử VCS; chạy script cục bộ (bash/python); giao worker Hang cho việc cơ học; ghi `.overstack/`, `llmwiki/`; mạng để bootstrap/cài phụ thuộc.

### Failure boundaries
- Project root không tồn tại hoặc thiếu skeleton → **blocked** (exit 1).
- Worker không báo xong trong 15 phút, spawn bị từ chối, hoặc `check_output.py` đỏ → phiên chính tự làm phần đó, ghi vào draft.
- `--update` mà chưa có graph/`meta.json` → **blocked**, bảo chạy không `--update` trước.
- Bootstrap fail → **failed**, STOP hoàn toàn.
- User không duyệt ở gate → **cancelled**, chỉ còn draft.
- Batch analyze fail 2 lần → bỏ batch, ghi PHASE_WARNINGS → **partial** graph (partial graph > no graph).
- Phase 1 gate thiếu `knowledge-graph.json`/`ONBOARDING.md` → **failed** Phase 1.
- Không có entry point HTTP/CLI/event → domains rỗng (succeeded hẹp).
- Vẽ `wiki-graph.html` lỗi → fail-open, không chặn onboard.

## HOW

### Main workflow
| Step | Type | Inputs | Action | Outputs/exit | Failure/next |
|---|---|---|---|---|---|
| W01 | deterministic | args, máy | **Phase 0** — dependency check, resume/root, update mode, bootstrap llmwiki+harness, tạo dirs, đếm file, probe agent | biến môi trường + `files.txt` | thiếu dep/root → exit 1 |
| W02 | effect | kết quả W01 | **Phase 0.5 Gate** — tạo draft TRƯỚC, index+log, in dispatch board + propose, hỏi user | draft `pending`, duyệt | không duyệt → cancelled |
| W03 | deterministic | repo | **Phase 1** 1.1 SCAN + 1.2 GIT HISTORY (bash) + 1.3 ANALYZE (static parse; worker Hang chỉ enrich) + 1.4 MERGE (python) | `assembled-graph.json` | batch fail → retry 1 → bỏ, PHASE_WARNINGS |
| W04 | judgment | assembled graph, dir tree, README | 1.5 LAYERS + TOUR (phiên chính) | layers + tour 5-15 bước | — |
| W05 | deterministic | graph | 1.6 VALIDATE + SAVE + gate cuối Phase 1 | `knowledge-graph.json`, `meta.json`, `ONBOARDING.md` | thiếu file → exit 1 |
| W06 | judgment | `ONBOARDING.md`, layers, `surface.json` | **Phase 2** bề mặt thật (`surface-coverage.py scan`) → domain enrichment (Claude) → gate `check` | `domain-graph.json` + `coverage.json`, dòng `N/M mục` | không entry point → domains rỗng; `check` đỏ sau 3 vòng → partial kèm danh sách CHƯA PHỦ |
| W07 | effect | ONBOARDING + domain graph | **Phase 3** wiki (phiên chính hoặc worker Hang, template fill) | `llmwiki/wiki/` | worker lỗi → phiên chính tự làm |
| W08 | effect | ONBOARDING + domain graph + skeleton | **Phase 4** STEP A JSON → STEP B fill skeleton (python) → STEP C vector | HTML + `wiki-graph.html` | skeleton thiếu → exit 1; vector lỗi → fail-open |
| W09 | effect | kết quả | Output Report + cập nhật status + báo phòng Hang | draft cuối, index/log | — |

Chi tiết từng bước (nguồn chân lý cho W01–W09):

#### Triggers
- "onboard codebase", "analyze codebase", "knowledge graph", "guided tour"

#### Options
- `--full` — Delete `.overstack/graph/` and rebuild
- `--update` — Incremental: re-analyze only changed files since last run
- `--language <lang>` — Output language (vi, en, zh, ...)
- `--skip-wiki` — Skip wiki generation
- `<path>` — Target directory (default: `.`)

#### Progress
```
[Phase 1/4] Graph generation (scan + git history + batch analyze + layers/tour)...
[Phase 2/4] Domain enrichment (Claude)...
[Phase 3/4] Wiki generation (script + worker Hang)...
[Phase 4/4] HTML docs (JSON + skeleton v3)...
```

---

#### ⚠️ HARD RULES

⛔ **DO NOT run Phase 0.5 or Phases 1–4 until Phase 0 completes.**

**Strict order — no reversal:**
1. **Phase 0** → complete, verify `llmwiki/` exists ✅
2. **Phase 0.5 (Gate)** → create draft file FIRST, then ask user
3. **Phases 1–4** → execute, update status after EACH phase immediately

- `llmwiki/` missing → bootstrap in Phase 0, NEVER defer
- Bootstrap fail → STOP completely, report error
- After EACH phase → update draft status NOW, never at end

---

#### Dispatch Rules

```
TASK TYPE          → AI LÀM
──────────────────────────────────────────────────────
Scan + git history → bash/python, không LLM
Batch file analyze → python static parse, không LLM
Merge + validate   → python, không LLM
Layers / tour      → phiên chính (không giao)
Domain reasoning   → phiên chính (không giao)
Trang wiki theo flow → script render từ domain-graph.json, không LLM
Wiki còn lại, JSON → phiên chính, hoặc một worker Hang nếu repo lớn
```

Repo dưới khoảng 200 tệp: phiên chính tự làm, không mở worker. Mở worker tốn hơn phần nó tiết kiệm.

#### Giao việc qua Hang

Máy có thể nối nhiều Hang. Chỉ dùng MCP của Hang chứa phòng hiện tại, không nhắn phòng trùng tên ở Hang khác.

```text
hang_spawn(dev=<máy này>, agent="claude", dir=<PROJECT_ROOT tuyệt đối>, room=<phòng>,
           nick=<tên>, role="worker", task_type="tai_lieu", session=<id phiên của bạn>,
           why="onboard: giao phần template fill", prompt=<SPEC>)
```

- Để trống `model` và `effort`: Hang điền theo bảng luật của `task_type`.
- Dự án còn agent khác đang sống thì `why` là bắt buộc (≥ 10 ký tự).
- MCP hỏng: `sh ~/.hang/bin/hang-room-hook spawn '<JSON tham số trên>' --from <phiên>`.
- `SPEC` phải tự đủ: đường dẫn nguồn, danh sách tệp đích, schema, luật R2/R3/R5, và câu cuối "Báo XONG trong phòng kèm danh sách tệp".
- Chờ tin trong phòng, không poll. Hook báo tin mới. Quá 15 phút không có tin: dừng worker bằng `hang_session_stop` rồi tự làm (RULE-13).
- Worker báo xong: chạy `scripts/check_output.py` (RULE-14).

Không có Hang (không MCP, không `~/.hang/bin/hang-room-hook`): phiên chính tự làm và in báo cáo ra terminal.

> **Không cần plugin Understand-Anything.** Phase 1 dùng phương pháp đã distill, chạy bằng bash/python và phiên chính.

---

#### Status Update Helper

```bash
update_phase_status() {
  local keyword="$1"
  local status="$2"
  [ -z "$DRAFT_FILE" ] && echo "[WARN] DRAFT_FILE unset" && return 0
  local f=$(echo "$DRAFT_FILE" | tr '\\' '/')
  [ ! -f "$f" ] && echo "[WARN] DRAFT_FILE not found: $f" && return 0
  perl -i -pe "s/(\Q$keyword\E.*?)\| (?:pending|in-progress|done)/\$1| $status/g if /\Q$keyword\E/" "$f" \
    || sed -i "s/\(.*$(echo "$keyword" | sed 's/[^^]/[&]/g').*\)| [a-z-]*/\1| $status/" "$f" \
    || echo "[WARN] status update failed for: $keyword"
}
```

---

#### Phase 0 — Pre-flight & Setup

```bash
# --- 1. Dependency check: Hang không bắt buộc, thiếu thì phiên chính tự làm ---
SKILL_DIR=$(ls -d ~/.agents/skills/hang-onboard ~/.claude/skills/hang-onboard 2>/dev/null | head -1)
[ -f "$SKILL_DIR/assets/docs-site-skeleton.html" ] || { echo "❌ Missing skeleton in $SKILL_DIR/assets"; exit 1; }
HANG_OK=no; [ -x "$(command -v sh)" ] && [ -f "$HOME/.hang/bin/hang-room-hook" ] && HANG_OK=yes

# --- 2. Resume Mode check & Project Root resolution ---
if [[ "$1" == @* ]]; then
  DRAFT_FILE="${1#@}"
  DRAFT_FILE=$(echo "$DRAFT_FILE" | tr '\\' '/')
  RESUME_MODE=true
  PROJECT_ROOT=$(grep "Project root:" "$DRAFT_FILE" | grep -oP '(?<=`)[^`]+(?=`)' | head -1)
  PROJECT_ROOT=$(echo "$PROJECT_ROOT" | tr '\\' '/')
else
  RESUME_MODE=false
  PROJECT_ROOT=${1:-.}
  PROJECT_ROOT=$(echo "$PROJECT_ROOT" | tr '\\' '/')
fi

test -d "$PROJECT_ROOT" || { echo "❌ Project root directory not found: $PROJECT_ROOT"; exit 1; }
PROJECT_ROOT=$(cd "$PROJECT_ROOT" && pwd)  # "." phải thành tên thư mục thật, slug mới đúng

# --- 3. Update Mode check ---
UPDATE_MODE=false
for arg in "$@"; do
  [ "$arg" = "--update" ] && UPDATE_MODE=true
done

if [ "$UPDATE_MODE" = "true" ]; then
  [ ! -f "$PROJECT_ROOT/.overstack/graph/knowledge-graph.json" ] \
    && echo "❌ --update requires existing graph. Run without --update first." && exit 1
  [ ! -f "$PROJECT_ROOT/.overstack/graph/meta.json" ] \
    && echo "❌ --update requires meta.json. Run without --update first." && exit 1
  echo "[update] Incremental mode — reading changed files from meta.json"
  
  CHANGED_FILES=$(python3 -c "
import json, sys
meta = json.load(open('$PROJECT_ROOT/.overstack/graph/meta.json'))
changed = meta.get('changedFiles', meta.get('changed', []))
print('\n'.join(changed))
" 2>/dev/null || echo "")

  if [ -z "$CHANGED_FILES" ]; then
    echo "[update] no changedFiles in meta.json — falling back to full rebuild"
    UPDATE_MODE=false
  else
    echo "[update] Changed files:"; echo "$CHANGED_FILES"
  fi
fi

# --- 4. Bootstrap llmwiki + harness if missing ---
# Harness có 2 mode: GLOBAL (~/.claude/harness + hooks trong ~/.claude/settings.json,
# bảo vệ mọi project llmwiki trên máy này) và PER-PROJECT (harness/ commit vào repo,
# bảo vệ teammate). Global đủ cho máy dev cá nhân — chỉ WARN per-project khi cả 2 thiếu.
GLOBAL_HARNESS=false
[ -f "$HOME/.claude/harness/hooks/pre_tool_use.py" ] \
  && grep -q 'harness/hooks/pre_tool_use.py' "$HOME/.claude/settings.json" 2>/dev/null \
  && GLOBAL_HARNESS=true
echo "[harness] global=$GLOBAL_HARNESS project=$([ -d "$PROJECT_ROOT/harness" ] && echo yes || echo no)"

if [ -f "$PROJECT_ROOT/.llmwiki/.harness-stamp" ]; then
  # Dự án layout DOT (cài bằng bootstrap v4): wiki ở .llmwiki/, engine ở GLOBAL — KHÔNG chép llmwiki/ trần, KHÔNG gọi đường per-project
  # (install-harness.sh sẽ tự dừng rc 5). Thiếu/cũ thì cập nhật bằng: curl -fsSL …/harness/poc-vendor-neutral/bootstrap.sh | bash
  echo "[hang-onboard] dự án dot-layout đã có overstack (.llmwiki/.harness-stamp), bỏ qua bootstrap"
elif [ ! -d "$PROJECT_ROOT/llmwiki" ] || { [ "$GLOBAL_HARNESS" = "false" ] && [ ! -d "$PROJECT_ROOT/harness" ]; }; then
  echo "[hang-onboard] bootstrapping llmwiki + harness..."
  # Ưu tiên bản local (344 KB), chỉ clone repo 50 MB khi máy chưa có.
  if [ ! -d "$PROJECT_ROOT/llmwiki" ] && [ -d "$HOME/.claude/harness/llmwiki" ]; then
    cp -R "$HOME/.claude/harness/llmwiki" "$PROJECT_ROOT/llmwiki"
  fi
  if [ ! -d "$PROJECT_ROOT/llmwiki" ] || { [ "$GLOBAL_HARNESS" = "false" ] && [ ! -d "$PROJECT_ROOT/harness" ]; }; then
    BOOT=$(mktemp -d)/setup
    git clone https://github.com/rheinmir/setup.git "$BOOT" --depth 1 -b orca -q
    [ ! -d "$PROJECT_ROOT/llmwiki" ] && cp -r "$BOOT/llmwiki" "$PROJECT_ROOT/llmwiki"
    if [ "$GLOBAL_HARNESS" = "false" ] && [ ! -d "$PROJECT_ROOT/harness" ]; then
      bash "$BOOT/harness/scripts/install-harness.sh" "$PROJECT_ROOT" \
        && echo "[hang-onboard] harness installed OK" \
        || echo "[WARN] harness install failed: dùng install-harness.sh --global"
    fi
    rm -rf "$BOOT"
  fi
  echo "[hang-onboard] bootstrap done"
fi

# --- 5. Create dirs ---
mkdir -p $PROJECT_ROOT/.overstack/onboard/{intermediate,tmp}
mkdir -p $PROJECT_ROOT/llmwiki/wiki/draft/{cave,uiux,hang} $PROJECT_ROOT/llmwiki/wiki/concepts $PROJECT_ROOT/llmwiki/wiki/entities

# --- 6. File count & availability check ---
git rev-parse HEAD 2>/dev/null > $PROJECT_ROOT/.overstack/onboard/tmp/commit.txt
git ls-files > $PROJECT_ROOT/.overstack/onboard/tmp/files.txt 2>/dev/null \
  || find $PROJECT_ROOT -type f \
       ! -path "*/.overstack/onboard/*" ! -path "*/llmwiki/*" ! -path "*/.git/*" \
     > $PROJECT_ROOT/.overstack/onboard/tmp/files.txt
FILE_COUNT=$(wc -l < $PROJECT_ROOT/.overstack/onboard/tmp/files.txt | tr -d ' ')

echo "[pre-flight] $FILE_COUNT files | hang=$HANG_OK"

# Parse statuses if in resume mode
parse_status() {
  local keyword="$1"
  awk '/## Agent Task Assignment/{p=1} p && /^## [^A]/{p=0} p' "$DRAFT_FILE" \
    | grep "$keyword" | grep -oE 'pending|in-progress|done' | head -1
}

if [ "$RESUME_MODE" = true ]; then
  PHASE1_STATUS=$(parse_status "Phase 1 —")
  PHASE2_STATUS=$(parse_status "Phase 2 —")
  PHASE3_STATUS=$(parse_status "Phase 3 —")
  PHASE4_STATUS=$(parse_status "Phase 4 —")
  echo "[Resume] P1=$PHASE1_STATUS P2=$PHASE2_STATUS P3=$PHASE3_STATUS P4=$PHASE4_STATUS"
fi
```

---

#### Phase 0.5 — Gate

**Required: create draft file FIRST, then ask user. Never reverse this order.**

```bash
DATE=$(date +%d%m%y)
PROJECT_SLUG=$(basename "$PROJECT_ROOT" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
DRAFT_FILE="$PROJECT_ROOT/llmwiki/wiki/draft/hang/${DATE}-onboard-${PROJECT_SLUG}.md"

AGENT_GRAPH="bash + python static parse + phiên chính (layers/tour)"

cat > "$DRAFT_FILE" << EOF
---
type: draft
title: ${DATE}-onboard-${PROJECT_SLUG}
status: proposed
tags: [hang-onboard, output-report]
timestamp: $(date +%Y-%m-%d)
---

# ${DATE}-onboard-${PROJECT_SLUG}

**Status:** proposed

## Hang
|---|---|
| Hang khả dụng | $HANG_OK |

## Agent Task Assignment
| Task | Agent | Model | Status |
|------|-------|-------|--------|
| Phase 1 — Graph generation ($FILE_COUNT files) | $AGENT_GRAPH | phiên chính | pending |
| Phase 2 — Domain enrichment | phiên chính | phiên chính | pending |
| Phase 3 — Wiki generation | script + phiên chính hoặc worker Hang | theo task_type tai_lieu | pending |
| Phase 4 — HTML docs | JSON + skeleton v3 | theo task_type tai_lieu | pending |

## What
Onboard \`$PROJECT_ROOT\` — understand-anything graph, domain enrichment, wiki, HTML.

## Output
- \`.overstack/graph/knowledge-graph.json\` (tree-sitter + Louvain)
- \`.overstack/graph/ONBOARDING.md\` (~20k tokens distilled)
- \`.overstack/onboard/intermediate/domain-graph.json\`
- \`llmwiki/wiki/\` (index, concepts, entities, architecture, tours)
- \`llmwiki/html/onboarding-${PROJECT_SLUG}.html\`
- \`llmwiki/html/wiki-graph.html\` (vector quan hệ concept↔code — STEP C)

## Files
| File | Action |
|------|--------|
| \`.overstack/graph/knowledge-graph.json\` | created by Phase 1 pipeline |
| \`.overstack/graph/ONBOARDING.md\` | created by Phase 1 pipeline |
| \`.overstack/onboard/intermediate/domain-graph.json\` | created by Claude |
| \`llmwiki/wiki/index.md\` | created/modified |
| \`llmwiki/wiki/concepts/architecture.md\` | created |
| \`llmwiki/wiki/concepts/*.md\` | created |
| \`llmwiki/wiki/entities/*.md\` | created |
| \`llmwiki/wiki/concepts/onboarding-tour.md\` | created |
| \`llmwiki/html/onboarding-${PROJECT_SLUG}.html\` | created |
| \`llmwiki/html/wiki-graph.html\` | created by STEP C (vector) |

## Notes
- Invoked via: \`/hang-onboard\` skill
- Project root: \`$PROJECT_ROOT\`
- Files tracked: $FILE_COUNT
- Reasoning phases stay in the main session
- Mechanical phases: scripts, then the main session or one Hang worker

## Origin
- **Draft:** \`wiki/draft/hang/${DATE}-onboard-${PROJECT_SLUG}.md\`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
EOF

# Update wiki index + log
echo "| [${DATE}-onboard-${PROJECT_SLUG}](draft/hang/${DATE}-onboard-${PROJECT_SLUG}.md) | draft | $(date +%Y-%m-%d) |" >> "$PROJECT_ROOT/llmwiki/wiki/index.md"
echo "## $(date +%Y-%m-%d) — hang-onboard — onboard-${PROJECT_SLUG}" >> "$PROJECT_ROOT/llmwiki/wiki/log.md"

echo "DRAFT_FILE=$DRAFT_FILE"

# --- Terminal dispatch board (REQUIRED — must print in terminal BEFORE the gate question) ---
echo ""
echo "==================== HANG-ONBOARD DISPATCH BOARD ===================="
echo " Project : $PROJECT_SLUG"
echo " Files   : $FILE_COUNT"
echo " Hang    : $HANG_OK"
echo " Draft   : $DRAFT_FILE"
echo "----------------------------------------------------------------------"
printf " %-7s %-22s %s\n" "PHASE" "TASK" "AI LÀM"
printf " %-7s %-22s %s\n" "1" "Graph generation" "bash + python + phiên chính"
printf " %-7s %-22s %s\n" "2" "Domain enrichment" "phiên chính"
printf " %-7s %-22s %s\n" "3" "Wiki generation" "script + phiên chính hoặc worker Hang"
printf " %-7s %-22s %s\n" "4" "HTML docs" "JSON + skeleton v3"
echo "======================================================================"

echo ""
echo "PROPOSE FILE: $DRAFT_FILE"
echo "----------------------------------------------------------------------"
cat "$DRAFT_FILE"
```

⛔ The dispatch board AND the propose file content above MUST be printed via bash (visible in terminal) — restating them only in chat or only in the draft file is NOT sufficient. The user gates orchestration based on this board + propose. The draft's Agent Task Assignment rows must match the board (giao worker thì draft phải ghi worker).

Hỏi duyệt trước khi tiếp tục. Trong phòng Hang: dùng `hang_ask`, thẻ có bấm chọn; không có Hang: hỏi ở terminal. Sau đó dừng, chờ câu trả lời.

---

#### Phase 1 — Graph Generation (distilled understand-anything — KHÔNG cần plugin)

**Pipeline:** scan (bash) → git history (bash) → phân tích tĩnh (python) → merge (python) → layers + tour (phiên chính) → validate + save (python + Claude). Phương pháp distill từ Understand-Anything; mọi prompt/schema nằm ngay dưới đây — không dispatch `/understand`, không cài plugin.

**Required output:**
- `.overstack/graph/knowledge-graph.json` (nodes, edges, layers, tour)
- `.overstack/graph/ONBOARDING.md` (~20k tokens distilled)
- `.overstack/graph/meta.json`

**Skip check:** `RESUME_MODE=true` + `PHASE1_STATUS=done` → skip to Phase 2.

**Decision table:**

| Graph exists | Flag | Action |
|-------------|------|--------|
| No | (none) | full pipeline |
| Yes | (none) | skip Phase 1, use existing graph |
| Yes | `--update` | re-analyze only `git diff <meta.gitCommitHash>..HEAD --name-only` files, merge into existing graph |
| Yes | `--full` | delete `.overstack/graph/`, full pipeline |

##### 1.1 SCAN (bash — no LLM)

```bash
mkdir -p "$PROJECT_ROOT/.overstack/graph" "$PROJECT_ROOT/.overstack/onboard/tmp"
git -C "$PROJECT_ROOT" ls-files > "$PROJECT_ROOT/.overstack/onboard/tmp/files.txt"
# Loại file nhị phân/lock/vendor; phân loại theo extension: code/config/docs/infra/data/script
# Đọc context: README (3000 chars đầu), manifest (package.json/pyproject.toml/Cargo.toml/go.mod), dir tree 2 cấp
# Detect entry point: src/index.ts, main.py, app.py, main.go, src/main.rs, cmd/*/main.go, manage.py, __main__.py...
```

##### 1.2 GIT HISTORY (bash — no LLM)

Tín hiệu lịch sử git làm giàu graph — thứ phân tích tĩnh không có:

```bash
# Churn — file nóng (hay sửa nhất, 365 ngày)
git -C "$PROJECT_ROOT" log --since="365 days ago" --name-only --pretty=format: \
  | grep -v '^$' | sort | uniq -c | sort -rn | head -40 > "$PROJECT_ROOT/.overstack/onboard/tmp/churn.txt"
# Recent — file vừa đổi (30 ngày)
git -C "$PROJECT_ROOT" log --since="30 days ago" --name-only --pretty=format: | grep -v '^$' | sort -u \
  > "$PROJECT_ROOT/.overstack/onboard/tmp/recent.txt"
# Commit subjects gần nhất — chủ đề đang phát triển
git -C "$PROJECT_ROOT" log --since="90 days ago" --pretty=format:'%s' | head -50 \
  > "$PROJECT_ROOT/.overstack/onboard/tmp/recent-subjects.txt"
# Co-change — python đọc `git log --name-only` theo commit, đếm cặp file đổi cùng nhau, ngưỡng ≥3
```

Áp dụng: top churn → tag node `hot`; trong recent.txt → tag `recent`; cặp co-change ≥3 → edge `related` (weight 0.5); tour + ONBOARDING ưu tiên file `hot`; recent-subjects cho mục "What's being worked on".

##### 1.3 ANALYZE: static parse (0 token)

Dùng python static parse: `ast` cho Python; regex `import/export ... from` và `require()` cho JS/TS, resolve đường dẫn tương đối → edges `imports`. Test → `tested_by`; summary = comment đầu tệp hoặc docstring, danh sách export, heading md; type theo extension. Imports là việc cơ học, LLM không chính xác hơn. Cần summary giàu ngữ nghĩa cho tệp phức tạp thì phiên chính đọc tệp đó.

Repo trên khoảng 200 tệp và thật sự cần: chia batch ~25 tệp rồi giao một worker Hang theo mục **Giao việc qua Hang**, ghi `.overstack/onboard/tmp/batch-<i>.json` dạng `{"nodes":[...],"edges":[...]}`. Batch hỏng: thử lại 1 lần, rồi bỏ qua và ghi PHASE_WARNINGS (partial graph > no graph).

##### 1.4 MERGE + NORMALIZE (python inline — no LLM)

Claude viết script `.overstack/onboard/tmp/merge.py` (logic distill từ merge-batch-graphs.py của Understand-Anything): đọc mọi `batch-*.json` → gộp nodes/edges → chuẩn hoá ID prefix (bỏ double-prefix, thêm prefix thiếu) → dedupe node theo id (giữ bản cuối), edge theo (source,target,type) → drop edge dangling (log stderr) → thêm edges `related` từ co-change (1.2) → ghi `assembled-graph.json`.

##### 1.5 LAYERS + TOUR (phiên chính — REASONING, không giao)

Từ assembled-graph + dir tree + README:
- **Layers:** `[{id: "layer:<kebab>", name, description, nodeIds[]}]` — mỗi file-level node thuộc ĐÚNG MỘT layer; cấu trúc thư mục là bằng chứng mạnh nhất. Tên layer nói việc nó làm, không dùng từ chung như "core".
- **Tour:** 5-15 bước `[{order, title, group, description, nodeIds[]}]`; các bước liền nhau cùng `group` thành một chặng trên bản đồ tour — bước 1 luôn là project overview (README), theo entry point, ưu tiên file `hot`; kể cùng câu chuyện README kể nhưng qua code thật.

##### 1.6 VALIDATE + SAVE (python + Claude)

Validate deterministic (script): không duplicate node ID, không dangling edge, mọi file node trong đúng 1 layer, tour nodeIds tồn tại, đếm orphan. Sửa tự động được thì sửa (drop dangling, fill default), còn lại ghi warning — partial graph vẫn save.

Ghi:
- `knowledge-graph.json`: `{version, project: {name, languages, frameworks, description, analyzedAt, gitCommitHash}, nodes, edges, layers, tour}`
- `meta.json`: `{lastAnalyzedAt, gitCommitHash, analyzedFiles}`
- `ONBOARDING.md` (Claude distill, ~20k tokens): overview, layers + mô tả, key flows, hot files + lý do (churn), "What's being worked on" (recent-subjects), tour narrative, stats.

Cuối: xoá `batch-*.json`, báo summary (files analyzed, nodes/edges by type, layers, tour steps, warnings).

##### Schema (distill từ Understand-Anything)

- **Node types:** `file, function, class, module, concept, config, document, service, table, endpoint, pipeline, schema, resource` — ID: `<type>:<relpath>[:<name>]`
- **Edge types chính:** imports, exports, contains, inherits, implements, calls, reads_from, writes_to, depends_on, tested_by, configures, related, documents, deploys, triggers, routes, defines_schema
- **Weights:** contains 1.0 · inherits/implements 0.9 · calls/exports 0.8 · imports 0.7 · depends_on/configures 0.6 · còn lại 0.5

```bash
# Gate cuối Phase 1
[ ! -f "$PROJECT_ROOT/.overstack/graph/knowledge-graph.json" ] \
  && echo "❌ Phase 1 FAIL: knowledge-graph.json missing" && exit 1
[ ! -f "$PROJECT_ROOT/.overstack/graph/ONBOARDING.md" ] \
  && echo "❌ Phase 1 FAIL: ONBOARDING.md missing" && exit 1
echo "✅ Phase 1 done"
# update_phase_status "Phase 1 —" "done"
```

##### 1.7 CODE-GRAPH MCP INDEX (optional — chỉ khi server `code-graph` có trong mcpServers)

Tầng truy vấn quan hệ code **chính xác theo line** bổ sung cho graph distill ở trên: `search_symbols`, `get_callers/callees` cho impact-check tức thì. Server `code-graph` (`~/.claude.json → mcpServers`) ghi 1 db SQLite mỗi repo tại `<repo>/.graph-agent/index.db`.

**Khi nào chạy:** project có submodule/repo code thật (Go/TS/Py…) **và code-graph THẬT SỰ dùng được** — kiểm bằng `python3 harness/scripts/dep-health.py --json` và đòi `status == "ok"`, ĐỪNG chỉ xem nó có được khai báo trong `~/.claude.json` hay không. Khai báo trong config ≠ server sống: DB 0 byte, DB thiếu bảng `symbols`, hay server đã chết đều vẫn "đang khai báo" (bài học 2026-07-20 — code-graph hỏng nhiều tuần mà mọi phiên vẫn bị lùa vào nó). `degraded`/`absent` thì bỏ qua bước này.

```bash
# 1. Index từng repo code (auto-detect root từ .git/go.mod/package.json).
#    Gọi MCP tool reindex_repo(<abs path repo>, force=true) cho MỖI repo code.
#    Lưu ý: code có thể nằm ở SUBDIR của submodule (vd <sub>/<svc>/go.mod chứ không phải <sub>/).
#    → trỏ vào thư mục chứa go.mod/package.json, không phải submodule root rỗng.
# 2. reindex_repo tự thêm repo vào registry ~/.graph-agent/repos.txt
#    → server --watch re-watch sau restart (durability).
# 3. Verify: get_stats() phải thấy symbols thật (>0), không phải stub.
echo "[1.7] code-graph: gọi reindex_repo cho mỗi repo code có manifest"
```

**Durability harness:** hook SessionStart `code_graph_keeper.py` (cài kèm install-harness.sh) tự re-register repo nếu rớt registry + cảnh báo repo chưa index. Fail-open, **no-op nếu project không dùng code-graph** — điều kiện là có `.graph-agent/index.db` **dùng được** (mở được + có bảng `symbols`/`files`), không phải chỉ có file: DB rỗng từng khiến keeper ghi nhầm registry và dập tắt luôn cảnh báo "chưa index". KHÔNG reindex per-edit (watcher đã lo, debounce 2s). Sau đó ghi 1 wiki concept page `concepts/code-graph-nav.md` (cách dùng tool + ví dụ caller trace) để team biết dùng.

> Freshness sau đó tự động: edit file → watcher reindex ~2s. Không cần reindex tay trừ khi clone mới hoặc đổi hàng loạt lúc server tắt.

---

#### Phase 2 — Domain Enrichment

**Agent:** phiên chính (không giao)

> **READ FIRST** (in order, before writing anything):
> 1. `.overstack/graph/ONBOARDING.md` — full read (~20k tokens)
> 2. `.overstack/graph/knowledge-graph.json` — read `layers` array + `entry-point` tagged nodes ONLY (⛔ NOT full file — context overflow)
> 3. If `UPDATE_MODE=true`: read existing `.overstack/onboard/intermediate/domain-graph.json` (merge, don't overwrite)

**DO:**
0. **Bề mặt thật TRƯỚC khi chọn flow** (skill `surface-coverage`, GH#191 — 18 flow từng bị báo như phủ hết một app 62 trang + 37 module):
   `python3 "$FDK_TOOLS/surface-coverage.py" scan "$PROJECT_ROOT" [--modules '<thư mục module API>/*'] --out .overstack/onboard/intermediate/surface.json`
   với `FDK_TOOLS=$([ -f fdk/tools/surface-coverage.py ] && echo fdk/tools || echo "$HOME/.claude/harness/fdk/tools")` (repo framework → bản trong repo; máy khách → engine global). Khung không file-based → `scan` chỉ nhận route Next.js nên viết script liệt kê bề mặt thật rồi ghi cùng định dạng `{commit, root, items}`. Ví dụ MCP/CLI Python: dùng `ast` đọc decorator `@tool`, `@mcp.prompt`, `@mcp.resource`, `custom_route` và `add_parser` thành `tool:x`, `prompt:x`, `cli:x`. Tính số dòng bước từ tên symbol hoặc chuỗi có thật, thiếu thì dừng, không gõ tay số dòng.
1. From entry points → identify HTTP endpoints / CLI commands / events / cron jobs — mỗi mục trong `surface.json` phải được một flow phủ hoặc loại trừ có lý do
2. Reverse-engineer: entry point → flow (process) → steps (actions @ file:line)
3. Build `domain → flow → step` hierarchy
4. Write `.overstack/onboard/intermediate/domain-graph.json` + sổ phủ `.overstack/onboard/intermediate/coverage.json` (`{"commit", "items": {"page:/x": {"by": ["flow:…"]} | {"exclude": "lý do"}}}`)
5. **Gate:** `python3 "$FDK_TOOLS/surface-coverage.py" check surface.json coverage.json --flows domain-graph.json --root "$PROJECT_ROOT"` — rc 1 (mục CHƯA PHỦ, flow id sai, `file:line` sai) → lần code lấp tiếp, tối đa 3 vòng; vẫn đỏ thì Phase 2 = **partial**. Báo cáo cuối (W09) in nguyên dòng `N/M mục bề mặt được phủ, K loại trừ` + danh sách CHƯA PHỦ — KHÔNG bao giờ báo số flow trơn như thể đã đủ.

**Domain graph schema:**
```json
{
  "domains": [
    {
      "id": "domain:order-management",
      "name": "Order Management",
      "flows": [
        {
          "id": "flow:create-order",
          "name": "Create Order",
          "steps": [
            { "order": 0.1, "id": "step:validate-input", "file": "src/orders/validator.ts", "line": 42 },
            { "order": 0.2, "id": "step:check-inventory", "file": "src/inventory/checker.ts", "line": 15 }
          ]
        }
      ]
    }
  ]
}
```

**Output:** `.overstack/onboard/intermediate/domain-graph.json`

**Skip check:** `RESUME_MODE=true` + `PHASE2_STATUS=done` → skip to Phase 3.

```bash
if [ "$RESUME_MODE" != "true" ] || [ "$PHASE2_STATUS" != "done" ]; then
  update_phase_status "Phase 2 —" "in-progress"
  # phiên chính, không giao
  if [ "$UPDATE_MODE" = "true" ] && [ -n "$CHANGED_FILES" ]; then
    echo "[Phase 2] Update mode: re-enrich domain steps for changed files only"
    # Read existing domain-graph.json
    # Filter steps with filePath in CHANGED_FILES
    # Re-analyze those steps from ONBOARDING.md
    # Merge back into domain-graph.json (keep unchanged steps)
  else
    echo "[Phase 2] Full domain enrichment from ONBOARDING.md"
    # Read ONBOARDING.md + layers from knowledge-graph.json, write new domain-graph.json
  fi
  update_phase_status "Phase 2 —" "done"
fi
```

---

#### Phase 3 — Wiki Generation

**Agent:** script cho trang flow; phiên chính hoặc worker Hang cho phần còn lại

> **READ FIRST** (worker chỉ biết những gì SPEC nêu, nên ghi rõ đường dẫn):
> 1. `.overstack/graph/ONBOARDING.md` — full read
> 2. `.overstack/onboard/intermediate/domain-graph.json` — full read
> 3. If `UPDATE_MODE=true`: grep `llmwiki/wiki/` for refs to `CHANGED_FILES` → identify stale pages
> - ⛔ DO NOT read `.overstack/graph/knowledge-graph.json` — too large, context overflow

**DO:** Fill wiki templates from distilled content. No reasoning — mechanical template fill.

**Output structure:**
```
llmwiki/wiki/
├── index.md
├── concepts/          ← architecture.md, message-sync/flows, onboarding-tour.md (R5: KHÔNG tạo folder architecture/ hay tours/ — validator folder_structure chặn)
└── entities/          ← domain entities + project-structure.md
# Mọi trang PHẢI có '## Origin' (R2) và row trong index.md (R3)
```

**Skip check:** `RESUME_MODE=true` + `PHASE3_STATUS=done` → skip to Phase 4.

```bash
if [ "$RESUME_MODE" != "true" ] || [ "$PHASE3_STATUS" != "done" ]; then
  update_phase_status "Phase 3 —" "in-progress"

  if [ "$UPDATE_MODE" = "true" ] && [ -n "$CHANGED_FILES" ]; then
    STALE_PAGES=$(grep -rl "$CHANGED_FILES" "$PROJECT_ROOT/llmwiki/wiki/" 2>/dev/null | tr '\n' ' ')
    if [ -n "$STALE_PAGES" ]; then
      echo "[Phase 3] Stale wiki pages: $STALE_PAGES"
      SPEC="Update these wiki pages based on changes in ONBOARDING.md: $STALE_PAGES
Changed source files: $CHANGED_FILES
Do NOT regenerate unchanged pages. Preserve existing content in unchanged pages."
    else
      echo "[Phase 3] No stale wiki pages — skipping"
      update_phase_status "Phase 3 —" "done"
    fi
  else
    SPEC="Generate wiki pages from .overstack/graph/ONBOARDING.md and .overstack/onboard/intermediate/domain-graph.json.
Create: llmwiki/wiki/index.md, llmwiki/wiki/concepts/*.md (architecture.md + flow pages + onboarding-tour.md),
llmwiki/wiki/entities/*.md (domain entities + project-structure.md).
R5: chỉ được ghi vào concepts/ hoặc entities/. R2: mọi trang có '## Origin'. R3: cập nhật index.md.
Use wikilink format [[page-name]]. Do NOT read knowledge-graph.json directly."
  fi

  # Trang flow: render bằng script từ domain-graph.json (mỗi domain một trang concepts/flow-*.md), 0 token.
  # Phần còn lại ($SPEC): phiên chính tự viết, hoặc repo lớn thì giao một worker theo "Giao việc qua Hang".
  python3 "$SKILL_DIR/scripts/check_output.py" || echo "[Phase 3] check_output đỏ: sửa trước khi đánh dấu done"

  update_phase_status "Phase 3 —" "done"
fi
```

---

#### Phase 4 — HTML Docs (skeleton v2 + JSON island)

**Agent:** ghép JSON = phiên chính hoặc worker Hang · **fill skeleton = python (no LLM)**

**Cách hoạt động (KHÁC bản cũ — chống sơ sài + đứt UX):** KHÔNG để model sinh HTML thô
(model tự chế CSS/JS → mất giao diện chuẩn, bấm không ăn, kết quả không ổn định).
Thay vào đó: model CHỈ phát **một object JSON** theo schema; UI do **skeleton v2 frozen**
(`assets/docs-site-skeleton.html` của skill này, đã áp đúng design-system `/docs-site-macos`) render.
Skeleton v3 = nav CỐ ĐỊNH (Overview/What & How/Architecture/Guided Tour/Modules/Docker; What & How ẩn khi JSON thiếu cả `what` lẫn `how`) + sidebar
fixed + collapse + scroll-spy + bản đồ tour kèm chi tiết bên dưới + sơ đồ khối, sơ đồ trình tự, draggable diagram; **Modules/Docker tự
ẩn khi mono**. Nội dung con (layer/tour/module/docker) DATA-DRIVEN từ JSON.

> **READ FIRST** (nguồn GIÀU):
> 1. `.overstack/graph/ONBOARDING.md` — full (overview, hot files, flows, tour narrative)
> 2. `.overstack/onboard/intermediate/domain-graph.json` — domain→flow→step (tour + lifecycle)
> 3. `knowledge-graph.json` **chỉ** `layers` + `tour` + node entry-point (⛔ KHÔNG full — overflow)
> ⛔ KHÔNG dùng wiki md mỏng làm nguồn chính (đó là lý do bản cũ sơ sài).

**Skip check:** `RESUME_MODE=true` + `PHASE4_STATUS=done` → skip.

```bash
if [ "$RESUME_MODE" != "true" ] || [ "$PHASE4_STATUS" != "done" ]; then
  update_phase_status "Phase 4 —" "in-progress"

  # --- locate skeleton v2 ---
  SKELETON="$SKILL_DIR/assets/docs-site-skeleton.html"; [ -f "$SKELETON" ] || SKELETON=""
  [ -z "$SKELETON" ] && echo "❌ Phase 4: skeleton v2 not found" && exit 1

  # --- detect Docker (multi-service → tab Docker; mono → docker:null, Modules:[]) ---
  DKFILE=$(ls "$PROJECT_ROOT"/docker-compose.y*ml "$PROJECT_ROOT"/compose.y*ml 2>/dev/null | head -1)
  N_SVC=0; [ -n "$DKFILE" ] && N_SVC=$(grep -cE '^  [a-zA-Z0-9_-]+:' "$DKFILE" 2>/dev/null || echo 0)
  echo "[Phase 4] skeleton=$SKELETON | compose=$DKFILE | services=$N_SVC"

  # --- STEP A: assemble ONBOARD_JSON (model emit JSON ONLY → file) ---
  JSON_OUT="$PROJECT_ROOT/.overstack/onboard/tmp/onboard.json"
  # Phiên chính tự viết $JSON_OUT, hoặc giao worker với SPEC dưới (repo lớn).
  SPEC="Đọc .overstack/graph/ONBOARDING.md + .overstack/onboard/intermediate/domain-graph.json.
Phát ra MỘT object JSON (KHÔNG markdown, KHÔNG giải thích) theo ĐÚNG schema trong header của
$SKELETON, ghi vào $JSON_OUT. Yêu cầu chất lượng:
- project: name/subtitle/about thật; stack[] + versions[] từ manifest; stats[] (files, services, layers, tour steps).
- project.what = 2–4 câu LỜI THƯỜNG: dự án làm gì, cho ai, giải quyết vấn đề gì (không thuật ngữ nội bộ); project.how[] = 3–7 bước {t,d} kể luồng chạy đầu→cuối bằng lời người.
- architecture.layers[] = layers thật, mỗi layer có plain (1 câu lời thường), example (1 việc cụ thể), files[], uses[] (layer nó gọi).
- architecture.block = sơ đồ khối: title là kết luận; rows[] từ trên xuống, mỗi row có 1–3 nhóm {name,color,blocks[]}. Hai row liền nhau: một bên phải có 1 nhóm, hoặc hai bên cùng số nhóm. KHÔNG khai toạ độ.
- architecture.sequences[] = 1–3 sơ đồ trình tự của luồng chính; title là kết luận; actors[]; steps[] {from,to,label,reply}. from/to phải nằm trong actors; đúng thứ tự gọi trong mã.
- architecture.diagram = sơ đồ quan hệ: nodes[] (toạ độ trong ~760 rộng, rect≥70×30), edges[]. Xếp cột để mũi tên không cắt qua ô.
- tour[] 5–15 bước, MỖI bước GIÀU: group (chặng), role(1-2 câu), file+line THẬT, in[]/out[], hot(churn), narr — KHÔNG 1–2 dòng. Các bước cùng group phải liền nhau.
- modules[] = mỗi container/image (đọc $DKFILE): name,img,meta(port/env/volume),life[[read|proc|write,desc]],arch. Repo mono ($N_SVC≤1) → modules:[].
- docker = {strategy, cmd[[text,c|p|]], table[[svc,img,cmd/port,deps]], order[]} nếu có compose; mono → docker:null."
  python3 "$SKILL_DIR/scripts/check_output.py" "$JSON_OUT" || echo "[Phase 4] check_output đỏ: sửa JSON trước khi fill"

  # Footer chi phí: chạy cost_footer.py (mục Output Report) trước bước này.
  # --- STEP B: fill skeleton (python, no LLM) — thay {{TITLE}} + {{ONBOARD_JSON}} ---
  OUT="$PROJECT_ROOT/llmwiki/html/onboarding-${PROJECT_SLUG}.html"
  mkdir -p "$PROJECT_ROOT/llmwiki/html"
  python3 - "$SKELETON" "$JSON_OUT" "$OUT" <<'PY'
import json,sys,html
sk=open(sys.argv[1]).read(); data=json.load(open(sys.argv[2]))
name=(data.get("project") or {}).get("name","Project")
out=sk.replace("{{TITLE}}",html.escape(name)).replace("{{ONBOARD_JSON}}",json.dumps(data,ensure_ascii=False).replace("</","<\\/"))
assert "{{TITLE}}" not in out.split("</head>",1)[1].split('id="ob-data"')[0], "token chưa thay hết"
open(sys.argv[3],"w").write(out); print("✅ filled →",sys.argv[3],len(out),"bytes")
PY

  ls "$OUT" && echo "✅ Phase 4 done" || echo "❌ Phase 4 FAIL: HTML not found"
  update_phase_status "Phase 4 —" "done"
fi
```

> **Fallback:** worker hỏng hoặc treo → phiên chính đọc `ONBOARDING.md` + `domain-graph.json`, viết `$JSON_OUT` theo schema rồi chạy STEP B. KHÔNG bao giờ tự viết HTML thô, luôn qua skeleton.

**Kiểm trên trình duyệt thật (có hạn thời gian, RULE-13):** dùng Playwright nếu có; bấm một bước tour, đọc lỗi console, đo tràn ngang ở 1280 và 390. Chrome headless không có `--timeout` có thể treo vô hạn, đừng chạy trần. Không có trình duyệt thì ghi BỎ QUA, không báo đạt.

**STEP C — vẽ vector `wiki-graph.html` (wiki vừa sinh ở Phase 3 → giờ CÓ concept để vẽ):**

Onboard đẻ wiki nhưng KHÔNG tự vẽ vector quan hệ — vẽ NGAY tại đây để dự án code-only kết thúc
onboard là có luôn vector (đúng nút thắt: `build-wiki-graph.py` đọc `llmwiki/wiki/*.md` + code, không
đọc thẳng code để đẻ concept). Fail-open, không chặn onboard.

```bash
# engine: repo-local → global (cùng thứ tự hook Stop resolve)
WG=$(ls "$PROJECT_ROOT/fdk/tools/build-wiki-graph.py" \
        "$HOME/.claude/harness/fdk/tools/build-wiki-graph.py" 2>/dev/null | head -1)
if [ -n "$WG" ] && [ -d "$PROJECT_ROOT/llmwiki/wiki" ]; then
  ALSO=""; [ -d "$PROJECT_ROOT/fdk/wiki" ] && ALSO="--also fdk/wiki"
  ( cd "$PROJECT_ROOT" && python3 "$WG" llmwiki/wiki $ALSO --code-root . ) \
    && echo "✅ vector: llmwiki/html/wiki-graph.html (concept↔code)" \
    || echo "⚠️ wiki-graph vẽ lỗi — không chặn onboard (Stop hook sẽ vẽ khi wiki/code đổi)"
else
  echo "⚠️ bỏ vẽ vector — thiếu engine build-wiki-graph.py (cài harness global) hoặc chưa có llmwiki/wiki"
fi
```

**After completion:**
```bash
# Trong phòng Hang: gửi trang cho người xem qua link Hang.
sh ~/.hang/bin/hang-room-hook send "room:<phòng>" "<tóm tắt>" --from <phiên> --agent claude-code --file "$OUT"
# Không có Hang: host local.
python3 -m http.server 8765 --bind 127.0.0.1 --directory "$PROJECT_ROOT/llmwiki/html" &
```

---

#### Rules

- **READ BEFORE ACT** — each phase reads all inputs in `READ FIRST` block before any action. Never ask user about something already in a file.
- **NO full `knowledge-graph.json` reads after Phase 1** — use `ONBOARDING.md` instead
- Real file paths only — never fabricate
- Domain graph: only reference real file:line, verify against code
- Wiki: wikilink format `[[page-name]]`
- Tour: 5-15 steps, start with project overview
- Reasoning tasks (domain, architecture): phiên chính

#### Errors

- Phase 1 batch fail → thử lại 1 lần, rồi phiên chính tự phân tích batch đó; ghi PHASE_WARNINGS
- Phase 1 fail (no graph) → đọc stderr của script, sửa, chạy lại
- Phase 2 domain empty → no HTTP/CLI/event entry points found; write empty domains array
- Phase 3 fail → phiên chính tự làm phần worker chưa xong
- Phase 4 fail → fallback: invoke docs-site-macos skill directly in Claude

---

#### Output Report

**Thuật ngữ (RULE-18), chạy trước bước chi phí:**
```bash
python3 "$SKILL_DIR/scripts/gloss.py" llmwiki/wiki/concepts/*.md llmwiki/wiki/entities/*.md .overstack/graph/ONBOARDING.md .overstack/onboard/tmp/onboard.json
```

**Chi phí (RULE-17), chạy NGAY TRƯỚC STEP B và trước khi báo:** lưu kết quả `hang_costs(op="rates")` vào `.overstack/onboard/tmp/rates.json` (không có Hang thì bỏ, footer chỉ ghi token), rồi:
```bash
python3 "$SKILL_DIR/scripts/cost_footer.py" --session "<phiên này>,<phiên worker>" --rates .overstack/onboard/tmp/rates.json \
  --skill "$SKILL_DIR/SKILL.md" --stamp llmwiki/wiki/concepts llmwiki/wiki/entities "$DRAFT_FILE" --json .overstack/onboard/tmp/onboard.json
```
Dán dòng `Chi phí: ...` nó in vào cuối tin báo phòng. Số trong trang là số tại lúc ghi; lượt báo cáo cuối chưa nằm trong đó.

Sau khi xong, cập nhật draft `llmwiki/wiki/draft/hang/<DATE>-onboard-<slug>.md`: cột Status đúng với lần chạy thật, ai đã làm phần nào, phần nào fallback, phần nào chưa kiểm. Thêm `| [<tên>](draft/hang/<tên>.md) | draft | YYYY-MM-DD |` vào `index.md` và `## YYYY-MM-DD — hang-onboard — <tên>` vào `log.md`.

Báo trong phòng Hang, đính kèm HTML: dòng `N/M mục bề mặt được phủ, K loại trừ` kèm danh sách CHƯA PHỦ; danh sách đã kiểm và **chưa kiểm** (test suite, trình duyệt). Giả thuyết đọc mã chưa chạy phải ghi rõ là chưa xác nhận.

Skill không commit, không push repo đích hay repo skill, trừ khi người dùng yêu cầu riêng.

### Branches
| ID | Kind | Guard | Hành vi | Skip / failure | Rejoin |
|---|---|---|---|---|---|
| B01 | user_optional | `@<draft>` (RESUME_MODE) | đọc status từng phase từ draft, phase `done` thì skip | draft thiếu `Project root:` → root rỗng → exit 1 | phase đầu tiên chưa `done` |
| B02 | user_optional | `--update` + graph có sẵn | chỉ re-analyze file đổi, merge vào graph/domain/wiki cũ | chưa có graph/`meta.json` → exit 1; `changedFiles` rỗng → full rebuild | W03 |
| B03 | user_optional | `--full` | xoá `.overstack/graph/`, full pipeline | — | W03 |
| B04 | conditional_required | graph có sẵn, không cờ | skip Phase 1, dùng graph cũ | — | W06 |
| B05 | capability_optional | code-graph `dep-health.py --json` báo `status == "ok"` | 1.7 CODE-GRAPH MCP INDEX: `reindex_repo` mỗi repo code, verify `get_stats()` >0, ghi `concepts/code-graph-nav.md` | `degraded`/`absent` → skip | W06 |
| B06 | recovery | worker Hang lỗi, treo quá 15 phút, hoặc `check_output.py` đỏ ở 1.3, Phase 3, Phase 4 STEP A | phiên chính tự làm (analyze batch / wiki / assemble JSON), Phase 4 vẫn qua skeleton | Phase 4 fail hẳn → invoke `docs-site-macos` trực tiếp | bước kế tiếp của phase đó |
| B07 | user_optional | `--skip-wiki` | bỏ Phase 3 | — | W08 |
| B08 | conditional_required | repo mono (`N_SVC ≤ 1`) | `modules:[]`, `docker:null` → skeleton tự ẩn tab Modules/Docker | multi-service → có tab Docker | W08 |

### Validation và stopping
Kiểm tất định bằng script: gate cuối Phase 1 (2 file bắt buộc), validate graph 1.6 (không duplicate ID, không dangling edge, mỗi file node đúng 1 layer, tour nodeIds tồn tại), assert thay hết token ở STEP B, `ls "$OUT"` ở cuối Phase 4, `scripts/check_output.py`, `frontend-antipattern.py` trên skeleton. Cần review: layers/tour, domain graph (đối chiếu file:line thật), chất lượng wiki. Dừng khi 4 phase `done` trong draft; retry batch tối đa 1 lần.

### Examples
- **Positive:** `/hang-onboard ~/code/zca-bridge` trong phòng Hang, repo 180 file → draft + dispatch board → thẻ `hang_ask` được duyệt → graph 180 node + 7 layer + tour 9 bước → `domain-graph.json` 3 domain → wiki concepts/entities → `llmwiki/html/onboarding-zca-bridge.html` + `wiki-graph.html`; draft 4 phase `done`.
- **Boundary/failure:** `/hang-onboard --update` trên repo chưa từng onboard → Phase 0 in "❌ --update requires existing graph. Run without --update first." và exit 1, không tạo draft.
- **Boundary:** worker Hang im quá 15 phút ở Phase 4 STEP A → dừng worker, phiên chính tự viết `onboard.json` rồi chạy STEP B; không viết HTML thô.

## Khác `orca-onboard`

| Mục | `orca-onboard` | `hang-onboard` |
|---|---|---|
| Giao việc | opencode, agy, kiro | phiên chính hoặc `hang_spawn` |
| Duyệt và báo cáo | terminal | thẻ `hang_ask`, báo trong phòng kèm HTML |
| Bootstrap | clone repo 50 MB | bản local trước, clone khi thiếu |
| Sync push cuối | đẩy `SKILL.md` vào `rheinmir/setup` (đường dẫn đã bỏ từ `23e53d2c`) | bỏ |
| Layer | tên + mô tả | giải thích layer là gì, lời thường, ví dụ, tệp, layer nó gọi |
| Sơ đồ | một sơ đồ quan hệ | thêm sơ đồ khối và sơ đồ trình tự do máy xếp |
| Tour | danh sách trái, chi tiết phải | bản đồ thứ tự theo chặng, chi tiết bên dưới |
| Thuật ngữ | thuần Việt | tiếng Anh ngay cạnh, `scripts/gloss.py` |
| Chi phí | ước tính cố định | footer đo từ transcript, `scripts/cost_footer.py` |
| Cổng thêm | | `scripts/check_output.py`, hạn thời gian cho lệnh có thể treo |
