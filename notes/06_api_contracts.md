# 06 · API Contracts

## Status
**Confirmed from code.** All six endpoints are defined in [upskin_api/main.py](../upskin_api/main.py); Pydantic shapes are in [upskin_api/schemas.py](../upskin_api/schemas.py); a separate narrative version of the contract lives in [docs/backend_api_contract.md](../docs/backend_api_contract.md).

## Base URLs
| Environment | URL | Source |
|---|---|---|
| Production | `https://upskin-api.onrender.com` | [site/api.js:8](../site/api.js), [site/runtime-config.js](../site/runtime-config.js) |
| Local | `http://localhost:8000` | [site/api.js:9](../site/api.js), [README.md:96](../README.md) |

Client-side resolution order: `window.__UPSKIN_API_URL` → `window.__UPSKIN_RUNTIME_CONFIG.apiUrl` → `process.env.NEXT_PUBLIC_UPSKIN_API_URL` → `?api=<url>` → host default. Confirmed from code: [site/api.js:38-46](../site/api.js).

## CORS
Allowed origins are driven by the `UPSKIN_CORS_ORIGINS` env var (comma-separated). Defaults: `http://localhost:5173`, `http://127.0.0.1:5173`, `https://up-skin.onrender.com`, `https://up-skin.vercel.app`. Credentials disabled, methods limited to `GET`/`POST`/`OPTIONS`. Confirmed from code: [upskin_api/main.py:18-38](../upskin_api/main.py).

## `GET /health`
Smoke-check for the model and catalogs. No request body, no params. Confirmed from code: [upskin_api/main.py:41](../upskin_api/main.py), [upskin_api/recommender.py:141](../upskin_api/recommender.py).

Response (no `response_model` declared):
```json
{
  "status": "ok",
  "run_id": "v002",
  "canonical_matrix_model": "ridge_ensemble",
  "mf_score_semantics": "ridge_ensemble_matrix_completion_score",
  "best_model_rmse": 0.7793,
  "model_type": "MC Dropout Bayesian Neural Network",
  "product_count": 2420,
  "demo_user_count": 6798,
  "uses_mf_proxy": true,
  "mf_proxy_note": "Full candidate-level MF scores were not exported; the API uses a user/product mean proxy."
}
```
**Frontend use:** header status pip + cold-start warm-up fetch. Confirmed from code: [site/site.jsx:13](../site/site.jsx), [site/index.html:96-101](../site/index.html).

## `GET /model/metrics`
Returns the full transparency payload used by the "How this works" sheet. Confirmed from code: [upskin_api/main.py:46](../upskin_api/main.py), [upskin_api/recommender.py:155](../upskin_api/recommender.py).

Response (key fields):
```json
{
  "run_id": "<best run id>",
  "canonical_matrix_model": "ridge_ensemble | matrix_factorization",
  "mf_score_semantics": "...",
  "best_model": {
    "model_type": "MC Dropout Bayesian Neural Network",
    "best_epoch": 7,
    "test_bnn_rmse": 0.7636,
    "test_bnn_mae": 0.4956,
    "test_mf_rmse": 0.7786,
    "test_mf_mae": 0.4888,
    "test_hybrid_rmse": 0.7922,
    "test_hybrid_mae": 0.4978,
    "bnn_beats_mf_rmse": true,
    "bnn_beats_hybrid_rmse": true
  },
  "model_config": { "input_dim": 138, "dropout_rate": 0.2, "hidden_1": 128, "hidden_2": 64, "mc_samples": 100, ... },
  "uncertainty": { "mc_samples": 100, "test_uncertainty_abs_error_corr": 0.xx, "test_calibrated_interval_coverage": 0.95, ... },
  "all_metrics": { "test_decision_report": {...}, "calibration_report": {...}, "confidence_bucket_summary": [...] },
  "uses_mf_proxy": true,
  "mf_proxy_note": "...",
  "stale_notes_file": "/<project_root>/stale.md"
}
```
**Notes:** Field shapes ultimately come from `final_pipeline_summary.json` and `all_metrics.json` of the resolved run, so they are `Strongly inferred` to drift as model artifacts change. `stale_notes_file` leaks the local absolute path — flagged in [issues.md M12](../issues.md).
**Frontend use:** [site/ModelTransparency.jsx](../site/ModelTransparency.jsx).

## `GET /demo-users?limit=25`
Returns up to `limit` (≤ 100) demo users from `artifacts/matrix/user_history.csv`, sorted by `user_rating_count` desc. Confirmed from code: [upskin_api/main.py:51](../upskin_api/main.py), [upskin_api/recommender.py:176](../upskin_api/recommender.py).

Response item:
```json
{
  "author_id": "10000770719",
  "user_rating_count": 9,
  "mean_user_rating": 4.89,
  "liked_product_count": 9,
  "rated_product_count": 9,
  "liked_product_ids": ["P404338", "P447212", ...]   // first 10 only
}
```
**Frontend use:** [site/DemoProfileFlow.jsx](../site/DemoProfileFlow.jsx).

## `GET /products/search?q=&limit=20`
Substring match (lowercased) over `product_name + brand_name + secondary_category + tertiary_category`. Empty `q` returns products sorted by `loves_count` desc then `avg_product_rating` desc. Confirmed from code: [upskin_api/main.py:57](../upskin_api/main.py), [upskin_api/recommender.py:194](../upskin_api/recommender.py).

`response_model = list[ProductSearchItem]`:
```json
{
  "product_id": "P503879",
  "product_name": "Wake Up Honey Eye Cream with Brightening Vitamin C",
  "brand_name": "Farmacy",
  "category": "Eye Care / Eye Creams & Treatments",
  "price_usd": 48.0,
  "avg_product_rating": 4.51,
  "loves_count": 312044
}
```
**Frontend use:** [site/BuildProfileFlow.jsx:21-27](../site/BuildProfileFlow.jsx).

## `GET /recommendations/{author_id}?top_n=10`
Builds a profile from the demo user's `liked_product_ids` (falling back to `rated_product_ids`), excludes already-seen products, scores candidates with the BNN, and returns `top_n` items (≤ 50). Confirmed from code: [upskin_api/main.py:64](../upskin_api/main.py), [upskin_api/recommender.py:224](../upskin_api/recommender.py).

Error states:
- `404` if `author_id` is not in `user_history.csv`.
- `400` for downstream `ValueError` (e.g., profile has no products with available embeddings).

## `POST /recommendations/custom`
Body (`CustomRecommendationRequest`, Confirmed from code: [upskin_api/schemas.py:13](../upskin_api/schemas.py)):
```json
{
  "liked_product_ids": ["P503879", "P423688"],
  "top_n": 10,
  "filters": {
    "secondary_categories": ["Moisturizers"],
    "max_price_usd": 75,
    "exclude_product_ids": [],
    "include_out_of_stock": false
  }
}
```
- `liked_product_ids`: `min_length=1`, **no max length** (flagged in [issues.md H6](../issues.md)).
- `top_n`: `1..50`.
- `filters` defaults to an empty `RecommendationFilters` if omitted.

Errors:
- `400` if none of the supplied `liked_product_ids` exist in the catalog. Confirmed from code: [upskin_api/recommender.py:252](../upskin_api/recommender.py).

## Shared response shape — `RecommendationResponse`
Confirmed from code: [upskin_api/schemas.py:48](../upskin_api/schemas.py).
```json
{
  "run_id": "v002",
  "best_model_rmse": 0.7793,
  "uses_mf_proxy": true,
  "mf_proxy_note": "...",
  "recommendations": [ /* RecommendationItem */ ]
}
```

Each `RecommendationItem` ([upskin_api/schemas.py:35](../upskin_api/schemas.py)):
```json
{
  "product_id": "P503879",
  "product_name": "Wake Up Honey Eye Cream with Brightening Vitamin C",
  "brand_name": "Farmacy",
  "category": "Eye Care / Eye Creams & Treatments",
  "predicted_score": 4.94,
  "risk_adjusted_score": 4.93,
  "uncertainty": 0.029,
  "confidence_bucket": "high_confidence | medium_confidence | low_confidence",
  "predicted_interval": { "lower": 4.49, "upper": 5.00, "level": "calibrated_95" },
  "explanation": "Recommended as a ... product with high confidence because its product text is similar to the selected liked products. ..."
}
```
**Notes:**
- `price_usd` is **not** part of the response (UI renders it conditionally — see [issues.md M9](../issues.md)).
- `image_url` is **not** part of the response (UI falls back to placeholder SVG — see [site/components.jsx:71](../site/components.jsx)).
- Scores are stochastic per request (MC-dropout has no fixed seed); see [issues.md M16](../issues.md).
- Interval widths can be very wide on v001 (mean ~1.83 on the 1–5 scale); see [issues.md M2](../issues.md).

## Loading and timeout behavior (client-side)
- Fetches reuse default browser timeouts; no `AbortController` is used. Network errors are wrapped into `{ status: 0, detail }`. Confirmed from code: [site/api.js:64-71](../site/api.js).
- Cold-start UX: `LoadingState` shows progressive copy at 5 s ("Backend waking…"), 15 s ("Cold start ~30–60s"), 75 s ("Service may be down"). Confirmed from code: [site/States.jsx:46-50](../site/States.jsx).
- A pre-warm fetch to `/health` runs in parallel with Babel compile. Confirmed from code: [site/index.html:96-101](../site/index.html).

## External service dependencies at request time
None. The API is self-contained over local artifacts; no outbound HTTP calls. `Confirmed from code` (no `requests.*`, no `httpx.AsyncClient` in `upskin_api/`).

## Open API contract gaps
- `/health`, `/model/metrics`, `/demo-users` lack Pydantic `response_model` declarations — schema can drift silently. [issues.md M17](../issues.md).
- `/recommendations/*` has no rate limit, body-size limit, or list-length cap. [issues.md H6](../issues.md).
- Empty-result responses look identical to "no candidates matched," which hides the cause from the client. [issues.md M11](../issues.md).
- `mf_score_semantics` and `canonical_matrix_model` keys are emitted from `/health` and `/model/metrics`, but the served `mf_score` is still the proxy — clients can't tell the difference. [issues.md C1](../issues.md).
