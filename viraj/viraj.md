# Local setup

Run these commands from inside the `up-skin` folder:

```bash
# Create the local virtual environment if it does not already exist.
/opt/homebrew/bin/python3.11 -m venv venv

# Start the virtual environment.
source venv/bin/activate

# Install the project requirements.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Start Jupyter for the notebooks.
jupyter lab

# When finished, leave the virtual environment.
deactivate
```

## Build handoff artifacts

Run this after the Kaggle CSVs are available in `Datasets/`:

```bash
source venv/bin/activate
python viraj/scripts/build_handoff_artifacts.py
```

This creates local outputs under `artifacts/`:

- Matrix Factorization train/test/prediction artifacts
- transformer product embeddings and nearest neighbors
- hybrid metrics
- `artifacts/handoff/bayesian_handoff_features.csv` for the Bayesian Neural Network step

## Step-by-step transformer notebook

Use `viraj/notebooks/transformers.ipynb` as the clean transformer implementation notebook.
The older `viraj/notebooks/Transformer_product_understanding.ipynb` can be treated as scratch/reference.

### Goal

Reuse Ishita's Matrix Factorization artifacts, add transformer product understanding, compare the same evaluation metrics, and create the Bayesian NN handoff table.

### Step 1: Load matrix artifacts

Load these files:

```text
artifacts/matrix/train_df.csv
artifacts/matrix/test_df.csv
artifacts/matrix/mf_predictions_test.csv
artifacts/matrix/skincare_products.csv
artifacts/matrix/user_history.csv
```

Expected shapes from the current run:

```text
train_df: (155597, 3)
test_df: (8448, 3)
mf_predictions: (8448, 4)
products: (2420, 27)
user_history: (8448, 5)
```

### Step 2: Build transformer product text

Build one text field per product from:

```text
product_name
brand_name
secondary_category
tertiary_category
highlights
ingredients
```

Current text-quality checks:

```text
Products with ingredients: 2286
Products without ingredients: 134
Transformer text max length after cap: 2500
Capped products: 93
```

### Step 3: Generate embeddings

Use:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Current embedding result:

```text
embeddings: (2420, 384)
dtype: float32
mean vector norm: 1.0
```

### Step 4: Product similarity sanity checks

Check moisturizer, acne/BHA, and SPF examples.

Current result:

```text
Moisturizer examples return mostly moisturizers/collagen/repair products.
Acne/BHA examples return exfoliators, pore products, acids, and clarifying products.
SPF examples return sunscreen and UV defense products very cleanly.
```

Conclusion: transformer product similarity is good enough to continue.

### Step 5: Build user content profiles

For each user:

```text
liked training products rating >= 4
-> product embeddings
-> average vector
-> normalized user content vector
```

Current result:

```text
Total train users: 8448
Users with at least one liked product: 8439
User content vectors: 8448
```

### Step 6: Score held-out products

For every row in `mf_predictions_test.csv`:

```text
content_score = user_content_vector dot product_embedding
content_rating_score = 1 + 4 * clipped(content_score)
```

Current result:

```text
Eval rows: 8448
Missing content scores: 0
Mean content_score: 0.8118
Mean content_rating_score: 4.2471
```

### Step 7: Compare rating prediction

Current RMSE/MAE:

```text
Matrix Factorization: 0.8174 / 0.5243
Transformer Content: 1.0260 / 0.8247
Hybrid 0.7 MF + 0.3 Content: 0.8294 / 0.6028
Best RMSE alpha: 0.9 MF + 0.1 Content -> RMSE 0.8159
```

Interpretation:

```text
MF is better for exact rating prediction.
Transformer content is not well calibrated as a rating predictor by itself.
Small transformer weight can slightly improve RMSE, but MF remains the main rating signal.
```

### Step 8: Compare ranking

Current Hit Rate@K:

```text
MF Hit Rate@10: 0.0149
Content Hit Rate@10: 0.0436
Hybrid Hit Rate@10: 0.0291
```

Interpretation:

```text
Transformer content is about 2.9x better than MF at Hit Rate@10.
This is the main transformer win: better ranking and product understanding.
```

### Step 9: Bayesian NN handoff

Use:

```text
artifacts/handoff/bayesian_handoff_features.csv
```

Important columns:

```text
true_rating
mf_score
content_score
content_rating_score
hybrid_score
mf_content_gap
user_rating_count
train_product_rating_count
avg_product_rating
num_reviews
price_usd
category fields
skin profile fields
```

Bayesian NN should learn:

```text
when to trust MF
when to trust transformer content
when scores disagree
how uncertainty changes for sparse users/products
```

Final project story:

```text
Matrix Factorization predicts ratings better.
Transformer embeddings rank similar products better and help product understanding.
Hybrid improves ranking over MF.
Bayesian NN should combine both signals and output uncertainty.
```
