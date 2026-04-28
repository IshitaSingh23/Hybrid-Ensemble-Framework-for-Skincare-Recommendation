# Up Skin Backend API Contract

This backend is a model-backed handoff API for the recommendation frontend. It does not serve precomputed recommendation rows as the source of truth. It resolves the best saved model run from `artifacts/versions/results_log.csv`, loads that run's model bundle, builds candidate features, and runs MC-dropout inference.

## Local Run

```bash
cd /Users/veerr_89/Work/projects/up-skin
source venv/bin/activate
python -m pip install -r requirements-api.txt
uvicorn upskin_api.main:app --reload --host 0.0.0.0 --port 8000
```

If the frontend is hosted on a different origin, set CORS explicitly:

```bash
UPSKIN_CORS_ORIGINS="http://localhost:5173,https://your-frontend.vercel.app" \
uvicorn upskin_api.main:app --host 0.0.0.0 --port 8000
```

For faster local tests, lower MC samples:

```bash
UPSKIN_MC_SAMPLES=3 pytest tests/test_upskin_api.py
```

## Required Artifacts

Version selection:
- `artifacts/versions/results_log.csv`
- `artifacts/versions/<best_run>/final_pipeline_summary.json`

Best run model bundle:
- `artifacts/versions/<best_run>/step5_bnn/mc_dropout_bnn_model.pt`
- `artifacts/versions/<best_run>/step5_bnn/preprocessor.joblib`
- `artifacts/versions/<best_run>/step5_bnn/model_config.json`
- `artifacts/versions/<best_run>/step5_bnn/all_metrics.json`
- `artifacts/versions/<best_run>/step4_features/feature_schema.json`
- `artifacts/versions/<best_run>/step4_features/embedding_pca.joblib`

Catalog and profile data:
- `artifacts/transformer/product_catalog.csv`
- `artifacts/transformer/product_embeddings.npz`
- `artifacts/matrix/user_history.csv`
- `artifacts/matrix/train_df.csv`

## Endpoints

### `GET /health`

Returns API/model status, resolved best run, product count, demo user count, and prototype flags.

### `GET /model/metrics`

Returns the best model summary, uncertainty metrics, calibration details, and MF proxy warning.

### `GET /demo-users`

Returns demo users from `artifacts/matrix/user_history.csv`.

Query params:
- `limit`: default `25`, max `100`

### `GET /products/search?q=`

Searches product name, brand, secondary category, and tertiary category from `product_catalog.csv`.

Query params:
- `q`: optional search text. Empty query returns popular products.
- `limit`: default `20`, max `50`

### `GET /recommendations/{author_id}?top_n=10`

Builds a profile from the demo user's liked/rated products, excludes already-seen products, scores candidates with the BNN, and returns ranked recommendations.

### `POST /recommendations/custom`

Builds a new visitor profile from liked product IDs.

Request:

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

Response recommendation item:

```json
{
  "product_id": "P503879",
  "product_name": "Wake Up Honey Eye Cream with Brightening Vitamin C",
  "brand_name": "Farmacy",
  "category": "Eye Care / Eye Creams & Treatments",
  "predicted_score": 4.94,
  "risk_adjusted_score": 4.93,
  "uncertainty": 0.029,
  "confidence_bucket": "high_confidence",
  "predicted_interval": {
    "lower": 4.49,
    "upper": 5.0,
    "level": "calibrated_95"
  },
  "explanation": "..."
}
```

## Frontend (site/)

The production frontend lives in `site/`. It is a static HTML/JSX bundle that
calls these endpoints directly. Run it alongside the backend:

```bash
# from the repo root, in a second terminal
python -m http.server 5173 --directory site
```

Open <http://localhost:5173/>. The page resolves the API base URL from
`window.__UPSKIN_API_URL` (or `NEXT_PUBLIC_UPSKIN_API_URL` when bundled), and
defaults to `http://localhost:8000`. Pass `?api=<url>` on the page URL to
override at runtime, or `?mock=1` to use the offline design preview layer
instead of the live backend. Full setup notes live in `site/README.md`.

## Hosting

Host the backend/model as a Dockerized FastAPI service on Render or Railway. Host the frontend on Vercel and point it at the backend URL.

Do not use Vercel serverless for the PyTorch model service unless the model bundle is substantially simplified. The Python runtime exists, but this project is a better fit for a normal Docker web service because it needs PyTorch, sklearn/joblib artifacts, pandas, and CSV/NPZ artifact loading.

Deployment note: `artifacts/` is ignored by git in this repo. For deployment, either attach the artifacts at build/runtime, use a persistent disk, or intentionally publish the required model bundle to the deployment target. The API will fail fast if required artifacts are missing.
