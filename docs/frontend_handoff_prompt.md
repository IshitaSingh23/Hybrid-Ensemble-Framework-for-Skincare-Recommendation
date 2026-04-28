# Claude Design Frontend Prompt

Use this prompt with Claude Design or another frontend builder.

```text
You are building the frontend for "Up Skin", a beauty-editorial class-demo website for an uncertainty-aware skincare recommendation system.

Project root:
`/Users/veerr_89/Work/projects/up-skin`

Backend source files to understand the API:
- `upskin_api/main.py`
- `upskin_api/schemas.py`
- `upskin_api/recommender.py`
- `docs/backend_api_contract.md`
- `stale.md`

Local backend run command:
```bash
cd /Users/veerr_89/Work/projects/up-skin
source venv/bin/activate
python -m pip install -r requirements-api.txt
uvicorn upskin_api.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend API base URL:
- Use an environment variable, for example `NEXT_PUBLIC_UPSKIN_API_URL`.
- Default local value: `http://localhost:8000`.
- Do not bake deployment URLs into components.

Critical rule:
Do not hardcode recommendation results, product rows, model metrics, demo users, confidence buckets, artifact version names, or model outputs. The frontend must consume live JSON from the backend API. UI labels, skeleton states, empty states, and product-image placeholders are fine; anything model/data-related must come from API responses.

The backend dynamically selects the best model by reading:
- `artifacts/versions/results_log.csv`

It chooses the row with the lowest `test_bnn_rmse`, then loads that run's artifacts from:
- `artifacts/versions/<best_run>/final_pipeline_summary.json`
- `artifacts/versions/<best_run>/step5_bnn/mc_dropout_bnn_model.pt`
- `artifacts/versions/<best_run>/step5_bnn/preprocessor.joblib`
- `artifacts/versions/<best_run>/step5_bnn/model_config.json`
- `artifacts/versions/<best_run>/step5_bnn/all_metrics.json`
- `artifacts/versions/<best_run>/step4_features/feature_schema.json`
- `artifacts/versions/<best_run>/step4_features/embedding_pca.joblib`

The backend also reads product/user data from:
- `artifacts/transformer/product_catalog.csv`
- `artifacts/transformer/product_embeddings.npz`
- `artifacts/matrix/user_history.csv`
- `artifacts/matrix/train_df.csv`

The current best run happens to be `v001`, but do not put `v001` in frontend code.

API contract:

1. `GET /health`

Purpose:
- Check backend/model status.
- Detect prototype flags.
- Display lightweight system status.

Response fields:
```json
{
  "status": "ok",
  "run_id": "v001",
  "best_model_rmse": 0.7636,
  "model_type": "MC Dropout Bayesian Neural Network",
  "product_count": 2420,
  "demo_user_count": 6798,
  "uses_mf_proxy": true,
  "mf_proxy_note": "..."
}
```

Frontend usage:
- Show backend status subtly.
- If `uses_mf_proxy` is true, show a clear prototype note.
- Do not display `run_id` as the main product headline; keep it in the model transparency area.

2. `GET /model/metrics`

Purpose:
- Populate a transparency panel.
- Explain why this model was chosen.
- Show uncertainty calibration and prototype limitations.

Response fields:
```json
{
  "run_id": "v001",
  "best_model": {
    "model_type": "MC Dropout Bayesian Neural Network",
    "best_epoch": 7,
    "test_bnn_rmse": 0.7636,
    "test_bnn_mae": 0.4956,
    "test_mf_rmse": 0.7786,
    "test_mf_mae": 0.4888,
    "test_hybrid_rmse": 0.7922,
    "test_hybrid_mae": 0.5726,
    "bnn_beats_mf_rmse": true,
    "bnn_beats_hybrid_rmse": true
  },
  "uncertainty": {
    "mc_samples": 100,
    "test_uncertainty_abs_error_corr": 0.3949,
    "test_calibrated_interval_coverage": 0.9465
  },
  "all_metrics": {
    "test_decision_report": {},
    "calibration_report": {},
    "confidence_bucket_summary": []
  },
  "uses_mf_proxy": true,
  "mf_proxy_note": "...",
  "stale_notes_file": "/Users/veerr_89/Work/projects/up-skin/stale.md"
}
```

Frontend usage:
- Show BNN RMSE, MF RMSE, Hybrid RMSE, BNN MAE, uncertainty-error correlation, and calibrated interval coverage.
- Explain uncertainty as "how sure the model is about its rating prediction," not product safety.
- Keep stale/prototype notes visible but gentle.

3. `GET /demo-users?limit=25`

Purpose:
- Let visitors try a real saved user profile.

Response item fields:
```json
{
  "author_id": "10000770719",
  "user_rating_count": 9,
  "mean_user_rating": 4.8889,
  "liked_product_count": 9,
  "rated_product_count": 9,
  "liked_product_ids": ["P404338", "P447212"]
}
```

Frontend usage:
- Present demo users as anonymized "Demo Profile 1", "Demo Profile 2", etc.
- Do not make `author_id` visually important; it can appear in small technical text.
- Use rating count and liked count to explain why a profile has more/less context.

4. `GET /products/search?q=<text>&limit=20`

Purpose:
- Search real products from `product_catalog.csv`.
- Used in custom onboarding to let a visitor select liked products.

Response item fields:
```json
{
  "product_id": "P434548",
  "product_name": "Honeymoon Glow AHA Resurfacing Night Serum",
  "brand_name": "Farmacy",
  "category": "Moisturizers / Night Creams",
  "price_usd": 60.0,
  "avg_product_rating": 4.3154,
  "loves_count": 177152
}
```

Frontend usage:
- Search by product, brand, or category.
- Empty query may return popular products.
- Each search result needs an image area, but the API does not currently return image URLs. Use a graceful product-photo placeholder slot. Do not invent real product images.
- If the backend later returns `image_url`, display it in the same slot.

5. `GET /recommendations/{author_id}?top_n=10`

Purpose:
- Generate model-backed recommendations for one demo user.

Frontend usage:
- Call after the user chooses a demo profile.
- Show loading state while recommendations are computed.
- Backend excludes already-seen products.

6. `POST /recommendations/custom`

Purpose:
- Generate model-backed recommendations for a new visitor from liked product IDs.

Request body:
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

Input features the frontend should provide:
- Liked product selector:
  - Search products with `/products/search`.
  - Let users select at least 1 liked product; encourage 3-8 for a better experience.
  - Show selected products as removable chips or small product tiles.
- Recommendation count:
  - Offer choices like 5, 10, 20.
  - Send as `top_n`.
- Optional filters:
  - Max price slider/input, sent as `filters.max_price_usd`.
  - Category chips, sent as `filters.secondary_categories`.
  - Do not hardcode a category list. Derive visible chips from searched/selected product categories, or omit the category filter until the backend exposes a category metadata endpoint.
  - Optional "include out of stock" toggle, sent as `filters.include_out_of_stock`.
- Exclusions:
  - The backend automatically excludes liked products.
  - Use `filters.exclude_product_ids` only for user-dismissed products if you build a "hide this" interaction.

Response shape for both recommendation endpoints:
```json
{
  "run_id": "v001",
  "best_model_rmse": 0.7636,
  "uses_mf_proxy": true,
  "mf_proxy_note": "...",
  "recommendations": [
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
  ]
}
```

Output features each recommendation card must show:
- Product image placeholder area:
  - Reserved aspect-ratio image frame at top of card.
  - Use a soft abstract skincare/flower placeholder if no `image_url` exists.
  - Do not use unrelated stock photos.
- Product name.
- Brand name.
- Category.
- Predicted score.
- Risk-adjusted score.
- Uncertainty.
- Confidence bucket.
- Predicted interval lower/upper.
- Explanation.
- Prototype note if `uses_mf_proxy` is true.

Required screens and flow:

1. Welcome / onboarding
- This should feel like an experience, not a form.
- Open with a warm skin-focused introduction: discovering products through preference, ingredients, and model confidence.
- Avoid medical claims.
- Give two paths:
  - "Use a demo profile"
  - "Build my profile"
- Use smooth staged transitions between steps.
- The onboarding should feel welcoming, calm, and a little lush, like entering a modern skincare studio.

2. Demo profile flow
- Fetch `/demo-users`.
- Show anonymized demo profiles with rating count, liked count, and mean rating.
- On selection, call `/recommendations/{author_id}?top_n=<n>`.
- Results should appear with a soft transition, not a hard page jump.

3. Custom profile flow
- Step 1: Search products.
- Step 2: Select liked products.
- Step 3: Optional filters.
- Step 4: Generate recommendations via `POST /recommendations/custom`.
- Keep progress visible.
- Let users go back without losing selected products.
- Empty state should guide users to search by product, brand, or category.

4. Recommendation results
- Product-forward card layout.
- Product photo placeholder slot is required.
- Confidence should be easy to scan:
  - High confidence: calm positive treatment.
  - Medium confidence: balanced treatment.
  - Low confidence: gentle caution, not alarm.
- Show uncertainty as model confidence, not skin safety.
- Include explanation text but keep it readable. Long explanations can collapse/expand.

5. Model transparency panel
- Pull from `/model/metrics`.
- Display the best model comparison in plain language:
  - BNN RMSE.
  - MF RMSE.
  - Hybrid RMSE.
  - BNN MAE.
  - Uncertainty-error correlation.
  - Calibrated interval coverage.
- Include prototype limitations from API flags and `stale.md`.
- Keep this panel secondary, like "How this works" or "Model notes".

Visual and UX direction:
- Aesthetic: flowery, skin-focused, welcoming, beauty-editorial.
- The site should feel soft, polished, and fresh: petals, botanicals, dewy skin, glass bottles, serum drops, soft daylight, clean whitespace.
- Use a refined warm palette: blush, petal pink, rose, soft green, cream, warm white, muted berry, and small deep contrast accents.
- Avoid generic AI gradient dashboards, neon cyber colors, dark sci-fi UI, and clinical hospital styling.
- Avoid making everything beige or one-note. Use a real palette with contrast.
- Typography should feel editorial and premium: a graceful display font for major headings and a highly readable body font.
- Product cards should feel tactile and skincare-specific, with image slots, subtle dividers, ingredient/signal tags, and calm confidence indicators.
- Use icons where helpful, especially for search, filters, confidence, price, and model notes.

Motion and interaction requirements:
- Smooth page and step transitions.
- Search results should animate in softly.
- Selected product chips/cards should have gentle add/remove motion.
- Recommendation cards should reveal in a staggered sequence.
- Confidence meters/interval displays can animate from empty to value.
- Use subtle hover/tap feedback on cards and buttons.
- Respect `prefers-reduced-motion`; reduce or disable large animations for users who request it.
- Do not use bouncy/cartoon easing. Use calm, premium easing.
- Avoid animations that cause layout jumps.

Responsive requirements:
- Mobile-first.
- Search, selected products, filters, and results must be comfortable on phone screens.
- Product card text must not overflow.
- Keep image placeholder dimensions stable so loading states do not shift layout.
- On desktop, use a more editorial composition with strong product/result focus.

Error, loading, and empty states:
- Backend unavailable: show a kind message and a retry action.
- No search results: suggest searching by product, brand, or category.
- No liked products selected: explain that at least one liked product is needed.
- No recommendations returned: suggest removing filters or selecting more liked products.
- API returns `uses_mf_proxy: true`: show a concise prototype note, not a scary warning.

Safety/copy constraints:
- Do not claim dermatologist advice.
- Do not claim allergy safety.
- Do not say a product will treat acne, eczema, aging, or other conditions.
- Say "may fit your preferences" or "the model is more/less confident" rather than "this will work for your skin."
- `stale.md` says explanations are heuristic, risk adjustment uses a fixed penalty, custom personalization is content-based, and medical/allergy safety is not modeled. Do not hide those facts.

Implementation expectations:
- Build actual API-connected UI, not mock-only UI.
- Keep API calls isolated in a small client module.
- Type the response shapes.
- Use loading skeletons that match final card dimensions.
- Leave a clear place to add product image URLs later.
- Do not mutate backend artifacts from the frontend.
```

