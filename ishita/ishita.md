# Ishita notebooks

Run notebooks from the `up-skin` project folder after starting the local environment:

```bash
source venv/bin/activate
jupyter lab
```

## Current workflow

1. `notebooks/Matrix_completion.ipynb`
   - Current best Algorithm 1 baseline.
   - Uses deduplicated skincare reviews, active-user/product filtering, per-user holdout, global/user-item baselines, biased matrix factorization, RMSE/MAE, and Hit Rate@K.

2. `notebooks/Transformer_product_understanding.ipynb`
   - Implements Algorithm 2 from the proposal.
   - Builds one metadata + ingredient text document per skincare product.
   - Encodes products with `sentence-transformers/all-MiniLM-L6-v2`.
   - Supports product similarity, cold-start content recommendations, explanation snippets, content Hit Rate@K, and a hybrid scoring scaffold for combining transformer scores with matrix-completion scores.

The Kaggle Sephora CSVs should be placed in `Datasets/` inside `up-skin`.
