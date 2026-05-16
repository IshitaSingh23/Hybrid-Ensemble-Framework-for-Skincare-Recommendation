# 07 · User Flows

All flows are mediated by the single `Site` component in [site/site.jsx](../site/site.jsx), which holds the active `view` and the last `results`/`error`. The header status pip starts polling `/health` on mount. No auth.

## Flow 1 — Landing / discovery
1. Browser hits the static site; index.html shows the boot splash with a live "0s/1s/2s…" counter while Babel compiles. Confirmed from code: [site/index.html:40-56](../site/index.html).
2. In parallel, `index.html` fires a no-store `fetch(api + "/health")` to wake the Render dyno. Confirmed from code: [site/index.html:96-101](../site/index.html).
3. `site.jsx` mounts at `<div id="root">`, replacing the splash. `view = "welcome"`. The header status pip starts in "checking" tone until `/health` resolves. Confirmed from code: [site/site.jsx:39-48](../site/site.jsx).
4. The welcome view shows three motif SVGs (`petal`, `drop`, `branch`), the wordmark in the header, the headline "a soft start *for your shelf.*", and two CTAs: **Build my profile** and **Use a demo profile**. Confirmed from code: [site/Welcome.jsx](../site/Welcome.jsx).
5. Footer disclaimer: "Up Skin recommends based on rating patterns and product similarity. It does not provide medical, allergy, or dermatology advice." Confirmed from code: [site/site.jsx:94-97](../site/site.jsx).

## Flow 2 — Auth / onboarding
**Not applicable.** No accounts, no login, no onboarding. See [04_auth_and_roles.md](04_auth_and_roles.md).

## Flow 3 — Build my profile (primary task flow)
**Step 1 — search and pick likes:**
1. `BuildProfileFlow` mounts at `step = 1` with `query = ""`. On mount it immediately calls `searchProducts("")`, which returns the popularity-sorted top 20 from the catalog. Confirmed from code: [site/BuildProfileFlow.jsx:17-27](../site/BuildProfileFlow.jsx), [upskin_api/recommender.py:194-211](../upskin_api/recommender.py).
2. Each subsequent keystroke is debounced 220 ms before hitting `/products/search?q=`. Cancellation is via a `cancelled` ref + a `searchNonce` retry counter.
3. The user toggles likes via the `ProductTile` "+ Like" / "Remove" button. Selected products appear as chips in the right-side `likes-tray` (live region). Continue is disabled while the tray is empty. Confirmed from code: [site/BuildProfileFlow.jsx:170-203](../site/BuildProfileFlow.jsx).
4. Errors during search render an inline `ErrorState` with a "Try again" button that increments `searchNonce`.

**Step 2 — optional filters:**
1. **Max price** slider, $20–$200 in $5 steps, defaults to **$75** — but the page copy says "we'll keep it open." This is a flagged UX bug ([issues.md H7](../issues.md)). Confirmed from code: [site/BuildProfileFlow.jsx:13](../site/BuildProfileFlow.jsx).
2. **How many to show** segmented control: 5 / 10 / 20.
3. **Categories** chips derived from the top-level segment of `category` strings on the liked + currently-searched products (`p.category.split(" / ")[0]`, max 6). Toggleable. The hint is honest: "Drawn from your likes — not a fixed list." Confirmed from code: [site/BuildProfileFlow.jsx:40-48](../site/BuildProfileFlow.jsx).
4. **Submit** sends `POST /recommendations/custom` with `max_price_usd` always present. View switches to `loading`.

**Errors:**
- `400 — No known liked products` from the API → `error` view with the detail. The "Start over" button resets to `welcome`. Confirmed from code: [site/site.jsx:83-89](../site/site.jsx).
- Empty `recommendations` array → `noresults` view with the copy "Try removing a filter, raising the max price, or selecting more liked products." Confirmed from code: [site/site.jsx:30-34, 76-82](../site/site.jsx).

## Flow 4 — Use a demo profile
1. `DemoProfileFlow` mounts and fires `GET /demo-users?limit=25` (the default). Confirmed from code: [site/DemoProfileFlow.jsx:10-18](../site/DemoProfileFlow.jsx).
2. Renders profile cards showing `Profile NN`, three stats (`liked` / `rated` / `mean`), the raw `author_id`. ⚠️ The lead copy says "anonymized," but the raw author IDs are shown. Flagged in [issues.md M6](../issues.md).
3. The user picks a card; "See recommendations" enables.
4. Click → `GET /recommendations/{author_id}?top_n=10` → `results`.
5. Errors during user load show an inline `ErrorState` with retry.

## Flow 5 — Recommendations page (shared end state for flows 3 & 4)
1. While loading, the `Recommendations` component renders a shimmer skeleton grid of 6 cards plus a `LoadingState` with cold-start copy. Confirmed from code: [site/Recommendations.jsx:97-110](../site/Recommendations.jsx).
2. On success, each result is a `RecCard` with:
   - Confidence eyebrow (`Confident pick` / `Good lead` / `Soft suggestion`).
   - Score badge (top right), brand, product name, secondary/tertiary category.
   - Interval bar (1.0 ←→ 5.0) with mid label "predicted {x} · interval {lo}–{hi}."
   - Stats row: `risk-adj.`, `uncertainty`, `price` *(rendered only when present — currently never returned)*.
   - Collapsed explanation; "Why this?" toggle reveals the body + the explanation string. Confirmed from code: [site/Recommendations.jsx:34-93](../site/Recommendations.jsx).
3. Staggered reveal: `animationDelay = i * 60ms`. Collapses to instant under `prefers-reduced-motion`.
4. Footer of the results page: "Start a new profile" (calls `restart`), "How this works" (opens the sheet), and a mono run/RMSE stamp.

## Flow 6 — Model transparency sheet
1. Opens from any view via the header link or the results-page link. Confirmed from code: [site/site.jsx:62, 100](../site/site.jsx).
2. On open, calls `GET /model/metrics`. Renders best-model RMSE/MAE, dropout rate, MC samples, uncertainty correlation, calibrated 95% coverage, and a fixed bullet list of model notes. Confirmed from code: [site/ModelTransparency.jsx](../site/ModelTransparency.jsx).
3. On error, replaces the body with a retry `ErrorState`.
4. Closes via the `×` button or scrim click.

## Flow 7 — Offline / preview mode (design-review only)
1. Triggered by `?preview=1` or `?mock=1` on the URL, or by setting `window.__UPSKIN_USE_MOCK = true` before `api.js` loads. Confirmed from code: [site/index.html:77-79](../site/index.html), [site/api.js:53](../site/api.js).
2. `window.upskinApi.usingMock` becomes `true`; the header pip's title changes to "Offline preview."
3. All `upskinApi.*` calls are routed through `mockRoute()` which returns hardcoded products, users, and seeded synthetic recommendations from `mockData.js` / `mockExtras.js`.
4. The mock layer mostly mirrors the real shape — but the `top_n` query string is ignored in `mockRoute` for demo users ([issues.md L7](../issues.md)).

## Cross-cutting behaviors
- **Restart** (back to welcome) is always wired through `restart()` in `site.jsx` and is invoked from: header brand click, results page footer, error/no-results views. Confirmed from code: [site/site.jsx:19](../site/site.jsx).
- **Reduced motion**: every animation/transition collapses to 0.01 ms under `prefers-reduced-motion: reduce`. Confirmed from code: [site/colors_and_type.css:211-217](../site/colors_and_type.css).
- **Cold-start awareness**: progressive loading copy at 5 / 15 / 75 seconds (`LoadingState`). The flows reuse it for catalog fetch and recommendation fetch. Confirmed from code: [site/States.jsx](../site/States.jsx).

## Mocked, broken, or incomplete steps
- **"Optional" filters apply a $75 max price by default.** Step 2 implies filters can be skipped. [issues.md H7](../issues.md).
- **Demo profiles show raw author IDs** despite "anonymized" copy. [issues.md M6](../issues.md).
- **Price slot on rec cards is dead** — backend never returns `price_usd`. [issues.md M9](../issues.md).
- **Recommendation list can include out-of-scope products** (e.g., Wellness, Hair Removal) because the Step-6 exclusion list isn't enforced at serving time. [issues.md C2](../issues.md).
- **Recommendations are stochastic** — the same profile can return slightly different scores on re-fetch because MC-dropout has no seed. [issues.md M16](../issues.md).
- **Mock products in `mockData.js` partially diverge** from the real catalog (read-only audit found 6 of 10 mock IDs absent from the catalog). [issues.md M8](../issues.md).
