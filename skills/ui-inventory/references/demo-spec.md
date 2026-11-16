# Demo fragments

Each `.html` file in `docs/ui-inventory/demos/` is a static, representative render of
one UI component as the app draws it. `build-page.mjs` compiles them with the app's own
stylesheet, so they use the app's real utilities, component classes and skin tokens, and
shows each one as A (old skin) next to B (new skin).

Names:

- a catalogue entry: `<n>-<last part of slug>.html` (e.g. `11-popup-pulldown-combo.html`);
- a component outside the catalogue: `x-<kebab of its canonical name>.html`, kebab =
  lowercase, every run of non-alphanumerics → `-`, trimmed
  (`Composer (Message Input)` → `x-composer-message-input.html`).

Rules for a fragment:

- One root element: `<div class="demo-root" data-source="src/…:line">…</div>`, where
  `data-source` names the code the markup was copied from (several refs may be separated
  by spaces).
- Copy the real `className` strings from that code (`className=` becomes `class=`;
  `cn(...)` and template strings resolved to one realistic state). Use only the app's
  token utilities and the shared classes it already has. No new CSS; `style` only for
  values the code itself sets inline.
- No `<script>`. Interaction, if any, is CSS-only (`<details>`, `:hover`, `:focus`).
- Use `relative`/`absolute` instead of `fixed` so the demo stays in its box; the frame
  has a `transform`, so anything `fixed` is clipped to it anyway.
- Icons are inline SVGs copied from the icon library the app imports (for Lucide:
  `node_modules/lucide-react/dist/esm/icons/<name>.js`), with `class="lucide"`.
  Use the real icon names (`loader-circle`, not the alias `loader-2`).
- Copy is the app's English copy from its locale files, or plausible sample data.
- Fits in 560 × 360 px. No external URLs, no images except inline SVG. Images, avatars
  and live surfaces (video, canvas, iframes) become token-coloured placeholders.
- SVG `id`s get a per-file prefix so two demos on one page cannot clash.
- A component the app does not have gets a proposal built from the same tokens and
  classes, with `data-proposal="true"` on the root.
