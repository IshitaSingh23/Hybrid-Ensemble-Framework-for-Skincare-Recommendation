# 08 · Pages and Routes

## Frontend
The frontend is a **single-page app with no URL routing**. There is exactly one HTML page ([site/index.html](../site/index.html)) that mounts the `Site` component. Navigation is purely a local `view` state in [site/site.jsx](../site/site.jsx:6). Browser back/forward does not change the view; deep links to a view are not supported.

| View key | When shown | Component | Data dependencies | Auth | Status |
|---|---|---|---|---|---|
| `welcome` | Initial render after splash; after every `restart()` | [Welcome.jsx](../site/Welcome.jsx) | None | — | ✅ Implemented |
| `demo` | "Use a demo profile" CTA | [DemoProfileFlow.jsx](../site/DemoProfileFlow.jsx) | `GET /demo-users` | — | ✅ Implemented |
| `custom` | "Build my profile" CTA | [BuildProfileFlow.jsx](../site/BuildProfileFlow.jsx) | `GET /products/search?q=` (debounced 220 ms) | — | ✅ Implemented (`maxPrice` UX bug — see [07_user_flows.md](07_user_flows.md)) |
| `loading` | After submitting a recommendation request | [Recommendations.jsx](../site/Recommendations.jsx) with `data=null` | — | — | ✅ Implemented |
| `results` | API responded with at least one recommendation | [Recommendations.jsx](../site/Recommendations.jsx) | `GET /recommendations/{id}` or `POST /recommendations/custom` | — | ✅ Implemented |
| `noresults` | API responded with `recommendations: []` | Inline `EmptyState` in `site.jsx` | — | — | ✅ Implemented (reason not surfaced — see [issues.md M11](../issues.md)) |
| `error` | Any thrown error from the API client | Inline `ErrorState` in `site.jsx` | — | — | ✅ Implemented |
| Model sheet (`sheet`) | "How this works" link (header / footer / results) | [ModelTransparency.jsx](../site/ModelTransparency.jsx) | `GET /model/metrics` | — | ✅ Implemented |

Confirmed from code: [site/site.jsx:69-90](../site/site.jsx).

## Query parameters honored at load time
| Param | Effect | Source |
|---|---|---|
| `?api=<url>` | Overrides API base URL (`window.__UPSKIN_API_URL`). ⚠️ unrestricted in production — see [issues.md M7](../issues.md). | [site/index.html:71-75](../site/index.html), [site/api.js:11-15](../site/api.js) |
| `?preview=1` | Enables offline mock layer (`window.__UPSKIN_USE_MOCK = true`). | [site/index.html:77-79](../site/index.html) |
| `?mock=1` | Same as `?preview=1`. | [site/index.html:77-79](../site/index.html), also accepted by mock route docs in [site/README.md:60](../site/README.md) |

No client-side router (no React Router, no history API). `Confirmed from code` via grep — no `react-router-dom`, no `pushState` calls.

## Backend
The FastAPI app exposes a small REST surface; there are no admin routes, no auth-gated routes, and no rendered HTML.

| Path | Method | Purpose | Auth | Key components | Data dependencies | Status |
|---|---|---|---|---|---|---|
| `/health` | GET | Service + model status | — | `RecommendationService.health()` | model bundle + product catalog + user history (lazy-loaded) | ✅ Implemented |
| `/model/metrics` | GET | Model transparency payload | — | `RecommendationService.metrics()` | `final_pipeline_summary.json`, `all_metrics.json` | ✅ Implemented (leaks local path — [issues.md M12](../issues.md)) |
| `/demo-users?limit=25` | GET | Anonymized profile list (max 100) | — | `RecommendationService.demo_users()` | `artifacts/matrix/user_history.csv` | ✅ Implemented (no response model — [issues.md M17](../issues.md)) |
| `/products/search?q=&limit=20` | GET | Catalog search (max 50) | — | `RecommendationService.search_products()` | `artifacts/transformer/product_catalog.csv` | ✅ Implemented (response model declared) |
| `/recommendations/{author_id}?top_n=10` | GET | Recommendations for a demo user (top_n ≤ 50) | — | `recommend_for_demo_user()` → `_recommend()` → `predict_mc` | model bundle, embeddings, train_df, user_history | ✅ Implemented; stochastic; train/serve skew on `mf_score` — [issues.md C1](../issues.md) |
| `/recommendations/custom` | POST | Recommendations for a new visitor (top_n ≤ 50) | — | `recommend_for_custom()` → `_recommend()` | same | ✅ Implemented; no rate limit / size cap — [issues.md H6](../issues.md) |

Confirmed from code: [upskin_api/main.py:41-86](../upskin_api/main.py).

### Error responses
- `404 Not Found` — unknown `author_id` on `GET /recommendations/{author_id}`. From `KeyError` at [upskin_api/recommender.py:227](../upskin_api/recommender.py).
- `400 Bad Request` — `ValueError` from the recommender, e.g. `"None of the liked_product_ids exist in the product catalog."` Confirmed from code: [upskin_api/main.py:72-74, 84-86](../upskin_api/main.py).
- Validation errors (`422`) come from Pydantic on body parsing (e.g., `liked_product_ids` empty).
- All other exceptions fall through to FastAPI's default 500 handler.

## Render notes
- Frontend is **statically served** by Vercel from the repo's `site/` directory. Cache headers on JS/CSS/SVG/woff/woff2 are `max-age=300, must-revalidate`; `runtime-config.js` is `no-cache`. Confirmed from code: [site/vercel.json](../site/vercel.json).
- Backend is a single Uvicorn worker exposed on `$PORT`. The Docker default is `8000`. Confirmed from code: [Dockerfile:10, 23](../Dockerfile).

## Routes that do not yet exist (referenced or implied)
- **Per-profile favorites / share link** — `Not found in repository`.
- **Admin endpoint to reload artifacts without restart** — `Not found in repository`; service singleton is permanently cached (see [issues.md L4](../issues.md)).
- **Healthcheck used by container orchestration** — `Not found in repository`; the Dockerfile defines no `HEALTHCHECK` (see [issues.md L8](../issues.md)).
