# 02 · Design System

## Status
The repo ships a **formal token-driven design system** in CSS custom properties — there is no Tailwind, no shadcn/ui, no component library. Confirmed from code: [site/colors_and_type.css](../site/colors_and_type.css), [site/style.css](../site/style.css), [site/site.css](../site/site.css).

## Aesthetic and direction
- **Mood:** soft beauty-editorial. Cream canvas, petal accents, calm motion. The README calls it "a skincare studio, in software." Confirmed from code: [site/colors_and_type.css:1-4](../site/colors_and_type.css), [README.md](../README.md), [site/README.md:1-7](../site/README.md).
- **Tone of voice:** "may fit your preferences" / "the model is more / less confident" — no medical, dermatology, allergy, or condition-treatment claims. Confirmed from code: [site/Recommendations.jsx:5-7](../site/Recommendations.jsx), [site/ModelTransparency.jsx:60](../site/ModelTransparency.jsx).
- **Decorative motifs:** hand-drawn SVGs (`petal.svg`, `drop.svg`, `branch.svg`, `bottle.svg`) used as `aria-hidden` accents. Confirmed from code: [site/Welcome.jsx:7-9](../site/Welcome.jsx), [site/States.jsx:7](../site/States.jsx).

## Color tokens (OKLCH)
Defined as CSS variables on `:root`. Confirmed from code: [site/colors_and_type.css:8-50](../site/colors_and_type.css).

| Group | Tokens |
|---|---|
| Canvas / neutrals | `--cream`, `--cream-deep`, `--warm-white`, `--shell` |
| Brand romantic | `--petal`, `--petal-deep`, `--blush`, `--rose`, `--rose-deep`, `--berry` |
| Supporting | `--sage`, `--sage-deep`, `--honey` |
| Text | `--aubergine`, `--aubergine-soft`, `--text-primary`, `--text-secondary`, `--text-muted`, `--text-on-rose` |
| Lines | `--line-faint`, `--line`, `--line-strong` |
| Confidence | `--conf-high-bg/fg` (sage), `--conf-med-bg/fg` (honey), `--conf-low-bg/fg` (dusty blush) |

Confidence colors map 1-to-1 to the backend's `confidence_bucket` strings. Confirmed from code: [site/style.css:84-87](../site/style.css), [upskin_api/model.py:81-86](../upskin_api/model.py).

## Typography
- **Display:** Fraunces (`@import` from Google Fonts, weights 300–700, opsz axis 9–144). Used for h1–h5, `.welcome-title`, `.results-title`. Confirmed from code: [site/colors_and_type.css:6](../site/colors_and_type.css).
- **Text:** Inter (400, 500, 600, 700). Used for body, eyebrow, buttons.
- **Mono:** system ui-monospace stack (SF Mono / Menlo / Consolas), via `.mono` and `<code>`. Used for `author_id`, run/RMSE stamps, elapsed timers.
- **Type scale (px):** `--fs-eyebrow: 11`, `--fs-caption: 12`, `--fs-meta: 13`, `--fs-body: 16`, `--fs-body-lg: 18`, h6–h1 from 18 → 64, `--fs-display: 88`. Confirmed from code: [site/colors_and_type.css:56-69](../site/colors_and_type.css).
- **Tracking:** `--tracking-tight: -0.02em` (large headings), `--tracking-snug: -0.01em` (h3+), `--tracking-eyebrow: 0.14em` (uppercase eyebrows).

## Spacing, radii, shadows
- **Spacing scale (4 px base):** `--sp-1: 4` → `--sp-28: 112`. Confirmed from code: [site/colors_and_type.css:80-92](../site/colors_and_type.css).
- **Radii:** `--r-xs: 4`, `--r-sm: 8`, `--r-md: 12`, `--r-lg: 16`, `--r-xl: 24`, `--r-pill: 999`.
- **Shadows (warm tinted):** `--shadow-soft`, `--shadow-lift`, `--shadow-modal`, plus a `--focus-ring` two-layer outline.
- **Container:** `--container-max: 1120px`, `--gutter: 24px`.

## Motion
- **Easing:** `--ease-calm: cubic-bezier(0.22, 0.61, 0.36, 1)` (a custom calm-out curve).
- **Durations:** micro `160ms` · default `240ms` · step `420ms` · stagger `600ms`.
- **Where it's used:**
  - View-stack `fadeUp` transitions between welcome → flow → results. Confirmed from code: [site/style.css:46-50](../site/style.css).
  - Recommendation card staggered reveal — `style={{ animationDelay: idx * 60 + "ms" }}`. Confirmed from code: [site/Recommendations.jsx:42](../site/Recommendations.jsx).
  - Shimmer skeletons (`shimmer` keyframe at 1.6 s linear infinite). Confirmed from code: [site/site.css:46-53](../site/site.css).
  - Boot spinner (`bootspin`). Confirmed from code: [site/index.html:25-30](../site/index.html), [site/site.css:11-16](../site/site.css).
  - Sheet enter/leave (scrim + slide). Confirmed from code: [site/site.css:74-80](../site/site.css).
- **Reduced-motion:** a global `@media (prefers-reduced-motion: reduce)` block collapses every `animation-duration`/`transition-duration` to `0.01ms`. This is a hard rule per [site/README.md:117](../site/README.md). Confirmed from code: [site/colors_and_type.css:211-217](../site/colors_and_type.css).

## Component primitives
All in plain JSX (no shadcn/ui, no Radix, no Headless UI). Confirmed from code: [site/components.jsx](../site/components.jsx).
- Buttons: `PrimaryBtn`, `SecondaryBtn`, `GhostBtn`, `LinkBtn` — pill-shaped (`--r-pill`), 1 px border, calm hover lift.
- Form: `SearchInput` with inline lucide-style SVG icon.
- Chips: `<span>`-based `Chip` (note: this is the accessibility gap flagged in [issues.md M10](../issues.md)).
- Card primitives: `ProductTile`, `RecCard`, `profile-card`.
- Status: `Eyebrow`, `StepHeader`, `LoadingState`, `ErrorState`, `EmptyState`.
- Icons: inline `<svg>` with a small `ICONS` map (lucide stroke style, `strokeWidth=1.5`).

## Confidence visualization
- **Interval bar:** track + band + center mark, linearly mapped over the 1.0–5.0 range. Confirmed from code: [site/Recommendations.jsx:12-32](../site/Recommendations.jsx).
- **Tone classes:** `rec-tone-high`, `rec-tone-med`, `rec-tone-low` drive the eyebrow color (`--conf-*-fg`).
- **Copy:** "Confident pick" / "Good lead" / "Soft suggestion." Confirmed from code: [site/Recommendations.jsx:4-7](../site/Recommendations.jsx).

## Consistency notes
- Tokens are loaded twice: `style.css` `@imports` `colors_and_type.css`, and `site.css` `@imports` `style.css`. The component-level CSS files mostly use tokens, but a handful of inline OKLCH literals appear in `site.css` (e.g., status pip "down"/"checking" colors at [site/site.css:23-25](../site/site.css)) — `Strongly inferred` these were chosen for one-offs that didn't fit existing confidence tokens.
- Two icon strategies coexist: inline `ICONS` map in [site/components.jsx](../site/components.jsx), and SVG file motifs in `site/assets/motifs/`. `Strongly inferred` consistent intent: lucide-style strokes for chrome icons, hand-drawn motifs for "art."
- The skel/loader CSS lives in `site.css`, but the boot splash is inlined in `index.html`. `Strongly inferred` this is to make the splash visible *before* the `style.css` request resolves.

## Where the design system breaks down
- No formal design system **doc** in the repo (Storybook, Figma export). The token list in `colors_and_type.css` is the source of truth.
- No dark-mode tokens. `Not found in repository`.
- No utility classes (Tailwind etc.). Layout/spacing is hand-rolled in `style.css` and `site.css`.
- No `tabindex`/aria-pressed strategy on category-filter chips (rendered as clickable `span`). Confirmed from code: [site/components.jsx:53-67](../site/components.jsx), [issues.md M10](../issues.md).
