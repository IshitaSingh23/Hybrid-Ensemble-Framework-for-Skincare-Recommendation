# 01 · Features

## Confirmed implemented
| Feature | Where it lives | Notes |
|---|---|---|
| Welcome screen with two entry CTAs | [site/Welcome.jsx](../site/Welcome.jsx), [site/site.jsx:69](../site/site.jsx) | "Build my profile" + "Use a demo profile". |
| Demo-profile chooser (up to 25, sorted by `user_rating_count`) | [site/DemoProfileFlow.jsx](../site/DemoProfileFlow.jsx), [upskin_api/recommender.py:176](../upskin_api/recommender.py) | Loads `GET /demo-users`. Cards show `liked_product_count`, `user_rating_count`, `mean_user_rating` + raw `author_id`. |
| Build-profile flow (search → likes → optional filters) | [site/BuildProfileFlow.jsx](../site/BuildProfileFlow.jsx) | Two steps with a likes tray, debounced search (220 ms), category chips drawn from selected/searched products. |
| Product search | [site/api.js:122](../site/api.js), [upskin_api/recommender.py:194](../upskin_api/recommender.py) | Empty query returns popularity-sorted (`loves_count`, then `avg_product_rating`). |
| Custom-profile recommendation (`POST /recommendations/custom`) | [upskin_api/main.py:77](../upskin_api/main.py), [upskin_api/recommender.py:244](../upskin_api/recommender.py) | Requires `min_length=1` liked IDs. |
| Demo-user recommendation (`GET /recommendations/{author_id}`) | [upskin_api/main.py:64](../upskin_api/main.py), [upskin_api/recommender.py:224](../upskin_api/recommender.py) | Excludes already-seen product IDs. |
| Recommendation card with predicted score, 95% interval bar, risk-adjusted score, uncertainty, expandable explanation, optional price | [site/Recommendations.jsx](../site/Recommendations.jsx) | Three confidence buckets: `high_confidence`, `medium_confidence`, `low_confidence`. |
| Health pip in header | [site/site.jsx:39](../site/site.jsx), [upskin_api/main.py:41](../upskin_api/main.py) | Polls `GET /health` on mount. |
| Model transparency sheet ("How this works") | [site/ModelTransparency.jsx](../site/ModelTransparency.jsx), [upskin_api/main.py:46](../upskin_api/main.py) | Renders best-model metrics, calibration, dropout rate, MC samples from `GET /model/metrics`. |
| MC-dropout sampling for uncertainty | [upskin_api/model.py:96-125](../upskin_api/model.py) | `mc_samples` defaults to `model_config.mc_samples` or env `UPSKIN_MC_SAMPLES`. |
| Calibrated 95% interval | [upskin_api/model.py:67](../upskin_api/model.py), [upskin_api/model.py:118](../upskin_api/model.py) | Width = `std × calibration_multiplier` (default 1.96; v001 ships ~15.7). |
| Confidence bucketing | [upskin_api/model.py:81](../upskin_api/model.py) | Thresholds from `calibration_report` in `all_metrics.json`. |
| Risk-adjusted ranking | [upskin_api/recommender.py:321](../upskin_api/recommender.py) | `predicted − 0.5 × uncertainty`, clipped to [1, 5]. |
| Heuristic explanation copy | [upskin_api/recommender.py:447-476](../upskin_api/recommender.py) | Keyword groups: hydration / barrier / brightening / acne-oil / soothing / exfoliation. |
| Reduced-motion compliance | [site/colors_and_type.css:211](../site/colors_and_type.css) | Global `prefers-reduced-motion` override on animations + transitions. |
| Skeleton loaders with shimmer | [site/Skeletons.jsx](../site/Skeletons.jsx), [site/site.css:46](../site/site.css) | Used for tiles, profile cards, rec cards, metric rows. |
| Cold-start aware loading state | [site/States.jsx:31](../site/States.jsx) | Progressive reason text at ≥5 s ("Backend waking…"), ≥15 s ("Cold start ~30–60s"), ≥75 s ("Service may be down"). |
| Offline preview / design-review mode | [site/index.html:77](../site/index.html), [site/mockData.js](../site/mockData.js), [site/mockExtras.js](../site/mockExtras.js) | Opt-in via `?preview=1` / `?mock=1` / `window.__UPSKIN_USE_MOCK`. |
| Runtime API URL override | [site/api.js:38](../site/api.js), [site/runtime-config.js](../site/runtime-config.js) | Priority: `__UPSKIN_API_URL` → `__UPSKIN_RUNTIME_CONFIG.apiUrl` → `NEXT_PUBLIC_UPSKIN_API_URL` → `?api=` → host default. |
| Backend version pinning by env | [upskin_api/artifacts.py:77](../upskin_api/artifacts.py) | `UPSKIN_MODEL_RUN_ID=v002` forces the latest run; otherwise lowest `test_bnn_rmse`. |
| CORS allow-list driven by env | [upskin_api/main.py:18-38](../upskin_api/main.py) | `UPSKIN_CORS_ORIGINS` comma-separated; methods limited to GET/POST/OPTIONS. |
| Filters in custom recommendations | [upskin_api/schemas.py:6](../upskin_api/schemas.py), [upskin_api/recommender.py:339-362](../upskin_api/recommender.py) | `secondary_categories`, `max_price_usd`, `exclude_product_ids`, `include_out_of_stock`. |
| Pre-warm fetch for the sleeping Render dyno | [site/index.html:96-101](../site/index.html) | Fires `/health` in parallel with Babel compile. |

## Partially implemented
| Feature | Where | Gap |
|---|---|---|
| Hybrid (BNN × matrix) recommendations | [upskin_api/recommender.py:378](../upskin_api/recommender.py), [README.md](../README.md) | The hybrid `mf_score` is a **user/product mean proxy** at serving time, not the trained MF/Ridge model. Self-declared in [stale.md:5](../stale.md) and surfaced via `uses_mf_proxy: true` in `/health`. |
| Skincare-only candidate set | [upskin_api/recommender.py:83](../upskin_api/recommender.py), [issues.md C2](../issues.md) | Step-6 exclusion list (Hair Removal, Wellness, etc.) lives in `step6_recommendations/recommendation_metrics.json` but the API reads `filter_report` from `final_pipeline_summary.json`, which is missing the key. Out-of-scope products can leak in. |
| "Optional" filter UX | [site/BuildProfileFlow.jsx:13](../site/BuildProfileFlow.jsx), [issues.md H7](../issues.md) | `maxPrice` defaults to **$75** and is **always sent**. Step 2 copy says "we'll keep it open." |
| Recommendation card price | [site/Recommendations.jsx:76](../site/Recommendations.jsx) vs [upskin_api/schemas.py:35](../upskin_api/schemas.py) | Card renders `rec.price_usd`, but `RecommendationItem` does not include price. Always falls through. |
| Product image | [site/components.jsx:71](../site/components.jsx), [site/Recommendations.jsx:42](../site/Recommendations.jsx) | UI tries `rec.image_url`, falls back to placeholder SVG; API never returns image URLs. |
| Anonymized demo profiles | [site/DemoProfileFlow.jsx:45](../site/DemoProfileFlow.jsx), [upskin_api/recommender.py:184](../upskin_api/recommender.py) | UI claims anonymization, but the raw `author_id` from `user_history.csv` is returned and rendered. |
| Pydantic response models | [upskin_api/main.py](../upskin_api/main.py) | `/products/search` and `/recommendations/*` use `response_model`; `/health`, `/model/metrics`, `/demo-users` do not. |
| Startup readiness | [upskin_api/recommender.py:479-481](../upskin_api/recommender.py) | Model bundle is lazy-loaded on the first request via `@lru_cache`; `uvicorn` can come up before artifacts are validated. |

## Not implemented but implied / referenced
| Topic | Where it surfaces | Status |
|---|---|---|
| Production React build (no Babel-in-browser) | [site/index.html:86](../site/index.html), [issues.md H11](../issues.md) | Frontend runs Babel-standalone + UMD React in the browser. No Vite/Next build step. |
| Subresource Integrity / CSP on CDN scripts | [site/index.html:84-86](../site/index.html) | None present. |
| Rate limiting on `/recommendations/*` | [upskin_api/main.py](../upskin_api/main.py), [issues.md H6](../issues.md) | No throttle, no body-size cap, no list-length cap. |
| Artifact integrity verification | [upskin_api/model.py:152](../upskin_api/model.py), [upskin_api/recommender.py:96](../upskin_api/recommender.py), [issues.md H10](../issues.md) | `torch.load`, `joblib.load`, `np.load(..., allow_pickle=True)` with no hash/signature check. |
| User accounts / persistence | repo-wide | `Not found in repository`. No DB driver, no auth library, no session middleware. |
| Saved "favorites" or "follow-up runs" for a profile | repo-wide | `Not found in repository`. |
| Logging / metrics export | repo-wide | `Not found in repository` beyond Uvicorn's default access log. |
| Screenshots in README | [README.md:52](../README.md) | TODO comment in README; `docs/screenshots/` doesn't exist. |

## Nice-to-have / future (driven by `stale.md` and `issues.md`)
- Export the trained MF / Ridge model so `mf_score` matches training distribution. [stale.md:5](../stale.md), [issues.md C1](../issues.md).
- Add per-request seeding for reproducible MC-dropout demos. [issues.md M16](../issues.md).
- Add ingredient-avoidance filters and a clearer safety disclaimer. [stale.md:62](../stale.md).
- Add a real explanation/attribution layer (SHAP-style or attention-based) and rename the current copy. [stale.md:37](../stale.md), [issues.md M5](../issues.md).
- Add structured empty-state reasons (`recommendations: []` is currently opaque). [issues.md M11](../issues.md).
- Add response models for `/health`, `/model/metrics`, `/demo-users`. [issues.md M17](../issues.md).
- Bundle the frontend (Vite or Next) and serve prod React with SRI/CSP. [issues.md H11](../issues.md).
