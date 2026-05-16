# 03 · Architecture

## Stack at a glance

| Layer | Tech | Source |
|---|---|---|
| Frontend (static) | HTML + React 18 UMD + Babel-standalone | [site/index.html](../site/index.html) |
| Frontend bundling | **None** — JSX is compiled in the browser at page load | [site/index.html:86-115](../site/index.html) |
| Backend API | FastAPI 0.117 + Uvicorn 0.32 + Pydantic 2.10 | [requirements-api.txt](../requirements-api.txt), [upskin_api/main.py](../upskin_api/main.py) |
| ML model | PyTorch 2.11 MC-dropout BNN | [upskin_api/model.py:15](../upskin_api/model.py) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, training-time), persisted as NPZ | [artifacts/run_config.json](../artifacts/run_config.json), [artifacts/transformer/](../artifacts/transformer/) |
| Preprocessing | scikit-learn `ColumnTransformer`, PCA on embeddings, persisted as joblib | [upskin_api/model.py:168](../upskin_api/model.py) |
| Containerization | Dockerfile based on `python:3.11-slim` | [Dockerfile](../Dockerfile) |
| Hosting | Vercel (frontend) + Render (backend) | [docs/backend_api_contract.md:151](../docs/backend_api_contract.md) |
| Persistence | Filesystem only (CSV / NPZ / joblib / JSON under `artifacts/`) | [upskin_api/recommender.py:85-119](../upskin_api/recommender.py) |
| Auth | **None** | (see [04_auth_and_roles.md](04_auth_and_roles.md)) |
| Database | **None** | (see [05_database_schema.md](05_database_schema.md)) |
| External services | Google Fonts CDN, unpkg.com (React UMD + Babel) | [site/index.html:9-13](../site/index.html), [site/colors_and_type.css:6](../site/colors_and_type.css) |

## Frontend
- **Mount:** the page ships with a boot splash that `createRoot` replaces once Babel finishes compiling the JSX files declared as `<script type="text/babel">`. Confirmed from code: [site/index.html:39-115](../site/index.html), [site/site.jsx:105](../site/site.jsx).
- **Component tree:** `Site` → header (brand + status pip + "How this works") → view-stack switch (`welcome` | `demo` | `custom` | `loading` | `results` | `noresults` | `error`) → footer → `ModelTransparency` sheet. Confirmed from code: [site/site.jsx:50-103](../site/site.jsx).
- **State management:** local `useState` only. No Context, no Zustand, no Redux. Confirmed from code: [site/site.jsx:5-9](../site/site.jsx).
- **API client:** single global `window.upskinApi` set up by an IIFE in [site/api.js](../site/api.js). All flows call through `window.upskinApi.*`. The client owns base-URL resolution, JSON content-type, error wrapping, and the optional mock route table.
- **Asset paths:** `window.UPSKIN_ASSETS = "./assets"` set in `index.html`, used by `assetPath()` in [site/components.jsx:4](../site/components.jsx).
- **Build / deploy:** Vercel serves `site/` as static (no build / install command). Confirmed from code: [site/vercel.json](../site/vercel.json).

## Backend
- **Entry point:** `upskin_api.main:app`. Defines five public routes, applies CORS (env-driven), and delegates to `RecommendationService` via a process-singleton `get_service()`. Confirmed from code: [upskin_api/main.py](../upskin_api/main.py), [upskin_api/recommender.py:479-481](../upskin_api/recommender.py).
- **Service singleton:** `@lru_cache(maxsize=1)` on `get_service()` means the model and CSV catalogs are loaded once on the first request, then reused. Restart is the only way to reload. Confirmed from code: [upskin_api/recommender.py:479](../upskin_api/recommender.py), [issues.md L4](../issues.md).
- **Best-run resolution:** `resolve_best_run()` reads `artifacts/versions/results_log.csv`, sorts by `test_bnn_rmse`, and picks the lowest unless `UPSKIN_MODEL_RUN_ID` forces a specific version (Docker pins this to `v002`). Confirmed from code: [upskin_api/artifacts.py:59-106](../upskin_api/artifacts.py), [Dockerfile:8](../Dockerfile).
- **Model bundle:** wraps the BNN checkpoint + sklearn preprocessor + PCA + feature schema + JSON metrics. `predict_mc` runs `mc_samples` forward passes in train mode for dropout sampling, then computes mean / std / 95% interval. Confirmed from code: [upskin_api/model.py:39-125](../upskin_api/model.py).
- **Candidate scoring (`_candidate_features`):** for each request,
  1. Drop already-seen and explicitly excluded products.
  2. Apply user filters: secondary categories, `max_price_usd`, `include_out_of_stock`.
  3. Apply Step-6 exclusion filters from `bundle.best_run.summary["filter_report"]` (`Strongly inferred` to be empty for current artifacts — see [issues.md C2](../issues.md)).
  4. Build profile vector = L2-normalized mean of source-product transformer embeddings.
  5. Compute `content_score = embeddings @ profile_vector`, mapped to a 1–5 `content_rating_score`.
  6. Build a **proxy `mf_score`** = clip(global mean + user offset + product offset, 1, 5) — *not* the trained MF/Ridge model.
  7. Fill ensemble component columns (`ridge_ensemble_score`, `legacy_mf_score`, `item_knn_score`, etc.) by **copying the proxy** — the schema needs them, but the trained ensembles weren't exported. Confirmed from code: [upskin_api/recommender.py:382-388](../upskin_api/recommender.py).
  8. Merge in the per-product PCA embedding frame.
  9. Send the resulting DataFrame to `bundle.predict_mc`. Confirmed from code: [upskin_api/recommender.py:339-427](../upskin_api/recommender.py).
- **Ranking:** sort by `risk_adjusted_score` (clip(pred − 0.5·std, 1, 5)), then `predicted_score`, `avg_product_rating`, `loves_count`. Confirmed from code: [upskin_api/recommender.py:325-328](../upskin_api/recommender.py).

## Data flow (text diagram)

```
                Vercel static                    Render Docker (Uvicorn)
                ┌──────────────┐                 ┌────────────────────────────────────────┐
 visitor ─────► │ index.html   │ ──── fetch ───► │ /health  /model/metrics  /demo-users  │
                │ site.jsx     │                 │ /products/search                       │
                │ flows JSX    │                 │ /recommendations/{author_id}           │
                │ api.js       │                 │ /recommendations/custom                │
                │ runtime-cfg  │                 └──────────────┬─────────────────────────┘
                └──────┬───────┘                                │
                       │                                        ▼
                       │                          ┌─────────────────────────────┐
                       │                          │ RecommendationService (lru) │
                       │                          │   load_model_bundle()       │
                       │                          │   product_catalog (CSV)     │
                       │                          │   product_embeddings (NPZ)  │
                       │                          │   user_history (CSV)        │
                       │                          │   train_df (CSV)            │
                       │                          └────────────┬────────────────┘
                       │                                       ▼
                       │                          ┌─────────────────────────────┐
                       │                          │ MCDropoutBNN (PyTorch)      │
                       │                          │   Preprocessor (joblib)     │
                       │                          │   embedding_pca (joblib)    │
                       │                          │   model_config / all_metrics│
                       │                          │   artifacts/versions/<run>/ │
                       │                          └─────────────────────────────┘
                       │
                       └── optional ── ?preview=1 / ?mock=1 ──► site/mockData.js, site/mockExtras.js
```

## API surface
See [06_api_contracts.md](06_api_contracts.md) for the full list. The frontend calls only the six documented endpoints, and there is no other public surface (no admin, no auth).

## Third-party services
| Service | Used for | Source |
|---|---|---|
| Google Fonts | Fraunces + Inter typefaces | [site/colors_and_type.css:6](../site/colors_and_type.css) |
| unpkg.com | React 18 UMD (`react.production.min.js`, `react-dom.production.min.js`) + Babel standalone 7.29 | [site/index.html:84-86](../site/index.html) |
| Hugging Face (training-time only) | `sentence-transformers/all-MiniLM-L6-v2` | [artifacts/run_config.json:7](../artifacts/run_config.json) |
| Render | Backend Docker host | [docs/backend_api_contract.md:151](../docs/backend_api_contract.md) |
| Vercel | Frontend static host | [docs/backend_api_contract.md:152](../docs/backend_api_contract.md) |

No analytics, no telemetry, no error tracker, no auth provider. `Confirmed from code` — no SDKs referenced.

## Auth / DB / Storage / ML integrations
- **Auth:** none. Public read-only API. See [04_auth_and_roles.md](04_auth_and_roles.md).
- **DB:** none. All persistence is files under `artifacts/`. See [05_database_schema.md](05_database_schema.md).
- **Object storage:** none. Artifacts are copied into the Docker image at build time. [Dockerfile:19](../Dockerfile).
- **ML serving:** in-process PyTorch eval on CPU (`torch.device("cpu")` at [upskin_api/model.py:173](../upskin_api/model.py)). MC-dropout is achieved by calling `self.model.train()` *only during* `predict_mc`, then returning to `eval()`.

## Architectural guardrails (from code + docs)
- **Frontend never invents data.** Live products/users/metrics/recommendations come from the API; mock layer is opt-in only. [site/README.md:106](../site/README.md), [docs/frontend_handoff_prompt.md:31](../docs/frontend_handoff_prompt.md).
- **No medical / dermatology / allergy / condition-treatment claims** in any UI copy. [README.md:108-114](../README.md), [stale.md:62](../stale.md).
- **Honest uncertainty** is the brand: every score ships with a calibrated interval and a confidence label. [site/Recommendations.jsx](../site/Recommendations.jsx).
- **Prefer reduced motion is respected** globally. [site/colors_and_type.css:211](../site/colors_and_type.css).
- **`v001`/`v002` is not in frontend code.** Backend resolves the best run dynamically. [docs/frontend_handoff_prompt.md:51](../docs/frontend_handoff_prompt.md).

## Known architectural risks
- Browser-compiled JSX in production has both perf and supply-chain cost (no SRI, no CSP, dev React or production React depending on URL — index.html points at `.production.min.js`, fine, but Babel is still standalone). [issues.md H11](../issues.md).
- Service singleton + lazy load means a deploy can pass `uvicorn` startup but still die on first request. [issues.md M14](../issues.md).
- Required artifacts are git-ignored but Docker COPYs them in — clean clones can't build an image. [issues.md H9](../issues.md), [.gitignore](../.gitignore), [Dockerfile:19](../Dockerfile).
- Train/serve skew in `mf_score`: BNN was trained on a real MF score, served on a mean proxy. [issues.md C1](../issues.md), [stale.md:5](../stale.md).
