# Iconography

## Source: Lucide (CDN)

We use Lucide via CDN (`https://unpkg.com/lucide@latest`) at stroke width **1.5**.

```html
<script src="https://unpkg.com/lucide@latest"></script>
<i data-lucide="search"></i>
<script>lucide.createIcons();</script>
```

This is a **flagged substitution**. Up Skin's backend codebase contains no icon system — Lucide was chosen for its thin even strokes that match the editorial softness. If a different set is preferred (Phosphor Thin, Iconoir, hand-drawn custom), please flag.

## Inventory (UI roles)

| Role | Lucide name |
|---|---|
| Search | `search` |
| Filter / sliders | `sliders-horizontal` |
| Add / liked | `plus`, `heart` |
| Remove chip | `x` |
| Confidence high | `sparkles` |
| Confidence medium | `circle-dot` |
| Confidence low | `circle-dashed` |
| Price | `tag` |
| Model notes / info | `info` |
| Back / next | `arrow-left`, `arrow-right` |
| Demo profile avatar | `user-round` |
| External / docs | `arrow-up-right` |

## Sizing

- `--icon-sm` 14px — inline with body
- `--icon-md` 18px — default UI
- `--icon-lg` 24px — section headers, hero affordances

## Color

Always inherits `currentColor`. Never use a branded color unless paired with the rose CTA on a primary button.

## Botanical motifs (custom, in `assets/motifs/`)

Lucide is not used for the brand's decorative botanicals. The hand-drawn motifs are SVGs:

- `petal.svg` — single petal
- `drop.svg` — serum drop
- `bottle.svg` — outline bottle (also used in product placeholder)
- `branch.svg` — herbal sprig divider

These appear as soft full-bleed background washes at 6–10% opacity, or as small inline ornaments around section eyebrows.

## Emoji

**Never** in product UI. Unicode glyphs (✦ · ◌ ❀) may appear sparingly in marketing surfaces only, as decorative dividers.
