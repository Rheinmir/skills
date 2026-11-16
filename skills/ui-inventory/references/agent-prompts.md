# Agent prompts

Fill the `<…>` slots. Every agent writes straight to its own file and returns only a short
summary, so the orchestrator's context stays small. Give each agent its own scratch folder.

## 1. Catalogue audit (one agent per ≤16 catalogue items)

```text
You are auditing the UI of the repo at <repo> (<stack: e.g. React 19 + Tailwind 4 + lucide-react>;
frontend in <src dirs>, global CSS/tokens in <css>, design rules in <design doc> — read it first; it
names the shared primitives: <list>). READ ONLY: do not edit any source file.

The reference catalogue is docs/ui-inventory/parts/_catalogue.md. YOUR ASSIGNMENT: items <a> through <b>.

For EACH item, search the whole source tree (and native shells such as electron/ where relevant) to decide
whether the app implements that pattern, under whatever name. Think about synonyms (<hints for this range>).
Verify every claim by reading the code — no guessing. Count call sites with grep.

Write docs/ui-inventory/parts/<X>-<a>-<b>.md (<language> prose, English identifiers), one section per item:

### <n>. <Catalogue Name> — `<slug>`
- **Trạng thái:** ✅ Có | 🟡 Một phần | ❌ Không có
- **Tên trong <App>:** component(s)/class(es)/hook(s)
- **Định nghĩa:** `path:line` of each primary implementation
- **Nơi dùng:** <N> chỗ — up to 6 representative `path:line`
- **Biến thể:** variants/sizes/states
- **Kiểm chứng:** exact grep pattern(s) and hit counts
- **Code mẫu:** VERBATIM excerpt (≤ 30 lines) in a fenced block, preceded by `path:startLine-endLine`.
  If ❌, a short sketch labelled "Đề xuất (chưa có trong repo)" using the app's tokens.
- **Ghi chú refactor:** duplicates, one-offs bypassing shared primitives, inconsistencies, a11y gaps,
  each with `path:line`.

End the file with a fenced ```json array of
{"n":..,"slug":"..","name":"..","status":"yes|partial|no","omb":["..."],"def":["path:line"],"uses":N}.
Return only a 5-line summary: counts of ✅/🟡/❌ and any surprising finding.
```

## 2. File map (one agent per ≈150 files)

```text
You are building a complete UI-component map of <repo>. READ ONLY. Read <design doc> (shared primitives)
and skim docs/ui-inventory/parts/_catalogue.md (the naming vocabulary).

Your file list is in <path to list> (<N> files). Open and read EVERY file.
For each file record the components it DEFINES and classify each: the closest catalogue item(s) by number,
OR — if not covered — a precise industry-standard name marked NEW (e.g. "Composer / Message Input",
"Mention Autocomplete", "Approval Card", "Code Block", "Usage Meter", "Settings Row"), OR "non-visual".

Write docs/ui-inventory/parts/M-<k>.md:
1. Table: File | Component(s) (`Name:line`) | Catalogue # or NEW: <Name> | Primitive used (or "tự vẽ") | purpose.
2. "Thành phần mới (ngoài danh mục)": each NEW name with definition `path:line`, 1–2 sentences, variants,
   and a VERBATIM excerpt (≤ 25 lines) preceded by `path:start-end`.
3. "Trùng lặp / tự vẽ": places that hand-roll what a shared primitive provides, with `path:line`.
End with a fenced ```json array: [{"file":"..","component":"..","line":N,"catalogue":[n],"new":"Name or null"}].
Return a 5-line summary: files read, components, NEW names introduced.
```

## 3. Foundation (one agent)

```text
Audit the visual foundation of <repo> (tokens in <css>, rules in <design doc>). READ ONLY.
Catalogue items <styles range> (styles) and <vs range> (comparisons) plus a full foundation inventory.
Write docs/ui-inventory/parts/G-foundation.md with: 1 visual styles used (✅/🟡/❌ + evidence);
2 comparison pairs — which side the app uses and whether correctly; 3 every design token grouped, per skin;
4 every reusable CSS class (`path:line`); 5 class-string recipes in code; 6 motion (keyframes, easing,
durations, reduced-motion gates); 7 typography and icons (counts); 8 rule violations with the exact grep
pattern and hit count each (raw colours, palette classes, arbitrary radius/spacing, physical direction
classes, native controls the rules ban, icon stroke overrides). Return a 5-line summary.
```

## 4. Demos (one agent per ≤45 components)

```text
Repo: <repo>. First read docs/ui-inventory/demos/README.md — the binding spec. Then read <the part file
for your items, or docs/ui-inventory/README.md section of components outside the catalogue + canon.json
for your names>; it gives the definition `path:line` and verbatim samples for each.

TASK: for EACH of <items / names>, write docs/ui-inventory/demos/<file name per spec>. The demo must look like
the representative implementation: open the real source, copy the real className strings and structure,
resolve conditionals to one realistic state (menus open with 4–6 rows, dialogs open on their scrim inside the
box, variants side by side where they exist). Native/OS-drawn parts: a faithful small mock with data-source
pointing at the shell file. ❌ items: a proposal with data-proposal="true".

Do NOT edit any file outside docs/ui-inventory/demos/. Use your own scratch folder <path>.
Return a 3-line summary: files written, where fidelity is weak and why.
```
