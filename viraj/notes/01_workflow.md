# Matrix to Transformer to Bayesian Workflow

This file is the handoff map for the project pipeline:

1. Ishita owns Matrix Factorization.
2. Viraj owns Transformer product understanding and hybrid scoring.
3. The Bayesian Neural Network step consumes the combined feature table.

## Run the handoff build

Run from the `up-skin` folder:

```bash
source venv/bin/activate
python viraj/scripts/build_handoff_artifacts.py
```

Generated files are written to `artifacts/`, which is ignored by git because the files are local run outputs.

## Stage 1: Matrix Factorization

Input:
- `Datasets/product_info.csv`
- `Datasets/reviews_0-250.csv`
- `Datasets/reviews_250-500.csv`
- `Datasets/reviews_500-750.csv`
- `Datasets/reviews_750-1250.csv`
- `Datasets/reviews_1250-end.csv`

Process:
- Keep only skincare products.
- Normalize `author_id` and `product_id` as strings before grouping.
- Collapse duplicate user-product ratings by mean rating.
- Apply iterative filtering until the final matrix keeps users with at least `10` ratings and products with at least `20` ratings.
- Hold out one rating per user for testing.
- Train biased Matrix Factorization:
  `rating = global mean + user bias + item bias + user vector dot product vector`.

Final split from the current run:
- Filtered interactions: `164,045`
- Users: `8,448`
- Products: `1,235`
- Matrix missing percentage: `98.43%`
- Train rows: `155,597`
- Test rows: `8,448`
- Minimum training ratings per user after holdout: `9`

Artifacts:
- `artifacts/matrix/train_df.csv`
- `artifacts/matrix/test_df.csv`
- `artifacts/matrix/skincare_products.csv`
- `artifacts/matrix/user_history.csv`
- `artifacts/matrix/mf_predictions_test.csv`
- `artifacts/matrix/metrics.json`
- `artifacts/matrix/split_sanity.json`

Current Matrix Factorization results:
- Global mean RMSE/MAE: `1.0020 / 0.7405`
- User+Item baseline RMSE/MAE: `0.9048 / 0.6099`
- Biased MF RMSE/MAE: `0.8174 / 0.5243`
- MF Hit Rate@5/@10/@20: `0.0080 / 0.0149 / 0.0295`

What we learned:
- MF is much better than simple baselines for rating prediction.
- MF ranking is still weak, so it should not be the final recommender by itself.
- The matrix is extremely sparse even after filtering, which motivates product-text and ingredient understanding.

## Stage 2: Transformer Product Understanding

Process:
- Build one text document per skincare product using product name, brand, category, highlights, and ingredients.
- Do not use held-out review text for embeddings.
- Encode product text with `sentence-transformers/all-MiniLM-L6-v2`.
- Build product-to-product nearest neighbors.
- Build user content profiles from liked training products.
- Compute `content_score` for each test user-product pair.

Artifacts:
- `artifacts/transformer/product_embeddings.npz`
- `artifacts/transformer/product_catalog.csv`
- `artifacts/transformer/product_neighbors.csv`
- `artifacts/transformer/qualitative_checks.csv`
- `artifacts/transformer/embedding_model.txt`

Current Transformer / Hybrid results:
- Content-only RMSE/MAE: `1.0260 / 0.8247`
- Hybrid RMSE/MAE with `alpha = 0.7`: `0.8294 / 0.6028`
- Content Hit Rate@5/@10/@20: `0.0291 / 0.0436 / 0.0638`
- Hybrid Hit Rate@5/@10/@20: `0.0168 / 0.0291 / 0.0476`

Decision gate:
- Hybrid improves Hit Rate@10 versus MF alone: yes.
- Hybrid improves RMSE versus MF alone: no.

Interpretation:
- Keep MF as the strongest rating-prediction signal.
- Use transformer content features to improve ranking and cold-start/product-understanding behavior.
- For the next modeling step, pass both scores separately instead of only passing the blended score.

## Stage 3: Bayesian Neural Network Handoff

The Bayesian step should use:

- `artifacts/handoff/bayesian_handoff_features.csv`
- `artifacts/handoff/hybrid_metrics.json`

Feature table columns:
- `author_id`
- `product_id`
- `true_rating`
- `mf_score`
- `content_score`
- `content_rating_score`
- `hybrid_score`
- `mf_content_gap`
- `user_rating_count`
- `mean_user_rating`
- `train_product_rating_count`
- `mean_train_product_rating`
- `avg_product_rating`
- `num_reviews`
- `price_usd`
- category fields
- skin profile fields when available

Bayesian NN goal:
- Predict final preference score.
- Output uncertainty along with the score.

Expected uncertainty behavior:
- Lower uncertainty when user history is large, product review count is high, and MF/content scores agree.
- Higher uncertainty when user history is small, product review count is low, or MF/content scores disagree.

Recommended next implementation:
- Train a Bayesian or uncertainty-aware model using `true_rating` as the target.
- Use `mf_score`, `content_score`, `content_rating_score`, `mf_content_gap`, user/product counts, product metadata, and skin fields as inputs.
- Compare Bayesian point predictions against MF and hybrid RMSE/MAE.
- Report uncertainty calibration by checking whether high-uncertainty examples have larger prediction errors.
