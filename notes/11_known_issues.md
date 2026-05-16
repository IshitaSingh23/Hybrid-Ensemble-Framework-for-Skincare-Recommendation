# 11 · Known Issues

This list is distilled from the in-repo audit at [issues.md](../issues.md) (43 KB, ~40 findings) plus the self-declared prototype caveats in [stale.md](../stale.md). All claims here are `Confirmed from code` unless tagged otherwise; the issues file lists specific line numbers if you need to reproduce.

## Critical

### C1 — Train/serve skew on `mf_score`
- **Where:** [upskin_api/recommender.py:370-388](../upskin_api/recommender.py), [stale.md:5](../stale.md), [issues.md C1](../issues.md).
- **Symptom:** The BNN was trained on a feature column called `mf_score` produced by a real matrix-factorization scorer; at serving time the API constructs `mf_score` as `global_mean + (user_mean − global_mean) + (product_mean − global_mean)` and **copies it into every ensemble component slot** (`ridge_ensemble_score`, `legacy_mf_score`, `item_knn_score`, `metadata_content_score`, `gb_ensemble_score`, `rf_ensemble_score`). The served BNN therefore consumes a different feature distribution than the one its reported `test_bnn_rmse` was measured on.
- **Surface:** the only visible hint is `uses_mf_proxy: true` + the `mf_proxy_note` string in `/health` and `/model/metrics`.
- **Fix direction:** export the trained MF/Ridge ensemble at training time and load it in `RecommendationService` instead of synthesizing a proxy.

### C2 — Skincare exclusion filter is not enforced at serving time
- **Where:** [upskin_api/recommender.py:83, 355-361](../upskin_api/recommender.py), [issues.md C2](../issues.md).
- **Symptom:** Step 6 of the notebook pipeline records `excluded_secondary_categories` (High Tech Tools, Wellness, Hair Removal, Holistic Wellness, Teeth Whitening) and `excluded_tertiary_categories` (Facial Cleansing Brushes, Facial Rollers) in `step6_recommendations/recommendation_metrics.json`. The API reads `filter_report` from `final_pipeline_summary.json` — which doesn't contain those keys — so the exclusion is silently a no-op. A read-only audit found 73 "High Tech Tools" and 74 "Wellness" rows still in the live candidate features.
- **Fix direction:** read the filter report from `step6_recommendations/recommendation_metrics.json` (or copy the exclusion keys into `final_pipeline_summary.json` at training time).

## High

| ID | Title | Where | Note |
|---|---|---|---|
| H1 | Documented reproducible pipeline disagrees with current artifacts | `viraj/notes/01_workflow.md`, `viraj/scripts/build_handoff_artifacts.py`, [issues.md H1](../issues.md) | A rerun of the documented script would invalidate the current `v001`/`v002` artifacts. |
| H2 | Stale matrix/transformer metrics in docs | `viraj/viraj.md`, `viraj/notes/01_workflow.md`, [issues.md H2](../issues.md) | Doc-vs-artifact mismatch on row counts and RMSE. |
| H3 | Matrix holdout split violates "1-per-user" guarantee | `artifacts/matrix/split_sanity.json` (test_rows 7017 > test_users 6797), [issues.md H3](../issues.md) | 220 extra holdout rows; `min_train_ratings_per_user = 5` despite intended 10. |
| H4 | Weak personalization across demo users | `artifacts/versions/v001/step6_recommendations/top10_recommendations.csv`, [issues.md H4](../issues.md) | 5 demo users share 28 unique products across 50 rec rows; "Wake Up Honey Eye Cream" and "Truth Barrier Booster" appear in *every* demo user's top-10. |
| H5 | Custom cold-start mistakes "harshness" for "taste" | [upskin_api/recommender.py:255-275](../upskin_api/recommender.py), [issues.md H5](../issues.md) | A new visitor who picks highly-rated products gets `mean_user_rating ≈ 4.5`, behaving like a generous rater regardless of actual taste. |
| H6 | Public endpoints have no rate limit, body cap, or list cap | [upskin_api/main.py](../upskin_api/main.py), [upskin_api/schemas.py:13-16](../upskin_api/schemas.py), [issues.md H6](../issues.md) | `liked_product_ids` has `min_length=1` and **no max**; `_recommend` runs MC-dropout passes for each request. |
| H7 | "Optional" filters silently apply a $75 max-price filter | [site/BuildProfileFlow.jsx:13, 54-65](../site/BuildProfileFlow.jsx), [issues.md H7](../issues.md) | Step 2 copy says "we'll keep it open." `submit()` always sends `max_price_usd`. |
| H8 | Local venv runs scikit-learn 1.6.1 against 1.8.0-pickled artifacts | [requirements.txt:115](../requirements.txt), [requirements-api.txt:6](../requirements-api.txt), [issues.md H8](../issues.md) | Tests emit `InconsistentVersionWarning` and are not failing on it. |
| H9 | Required artifacts are git-ignored but Docker COPYs them | [.gitignore:6](../.gitignore), [Dockerfile:19](../Dockerfile), [issues.md H9](../issues.md) | A clean CI clone cannot build a working image. |
| H10 | `torch.load`/`joblib.load`/`np.load(allow_pickle=True)` with no integrity check | [upskin_api/model.py:152-170](../upskin_api/model.py), [upskin_api/recommender.py:95](../upskin_api/recommender.py), [issues.md H10](../issues.md) | Supply-chain risk if an attacker swaps an artifact. |
| H11 | "Production" frontend uses browser Babel + CDN React with no SRI/CSP | [site/index.html:84-86, 107-115](../site/index.html), [issues.md H11](../issues.md) | First load is slow and CDN-dependent; any unpkg compromise executes. |
| H12 | Tests are contract-smoke only | [tests/test_upskin_api.py](../tests/test_upskin_api.py), [issues.md H12](../issues.md) | No coverage of model parity, filter enforcement, or golden recommendations. |

## Medium

| ID | Title | Where |
|---|---|---|
| M1 | "BNN beats MF" copy uses no confidence intervals or ranking baselines | [site/ModelTransparency.jsx:91](../site/ModelTransparency.jsx), [issues.md M1](../issues.md) |
| M2 | Calibrated 95% intervals are ~1.83 wide on a 1–5 scale — visually precise, statistically thin | [upskin_api/model.py:67](../upskin_api/model.py), `all_metrics.json`, [issues.md M2](../issues.md) |
| M3 | Cosine similarity → 1–5 rating uses an arbitrary `1 + 4·clip(score, 0, 1)` mapping | [upskin_api/recommender.py:368](../upskin_api/recommender.py), [issues.md M3](../issues.md) |
| M4 | `hybrid_alpha = 0.7` is a fixed serving rule, not a tuned parameter | [artifacts/run_config.json:4](../artifacts/run_config.json), [upskin_api/recommender.py:70](../upskin_api/recommender.py), [issues.md M4](../issues.md) |
| M5 | Explanations look model-derived but are keyword/category templates | [upskin_api/recommender.py:447-476](../upskin_api/recommender.py), [stale.md:37](../stale.md) |
| M6 | "Anonymized" demo profiles show raw `author_id` | [site/DemoProfileFlow.jsx:87](../site/DemoProfileFlow.jsx), [issues.md M6](../issues.md) |
| M7 | `?api=<url>` query override is unrestricted in production | [site/index.html:71-75](../site/index.html), [site/api.js:13](../site/api.js), [issues.md M7](../issues.md) |
| M8 | Mock data layer is shipped + activatable in production | [site/index.html:89-90](../site/index.html), [issues.md M8](../issues.md) |
| M9 | Recommendation cards reference `price_usd`, which the API never returns | [site/Recommendations.jsx:76](../site/Recommendations.jsx), [upskin_api/schemas.py:35](../upskin_api/schemas.py), [issues.md M9](../issues.md) |
| M10 | Category filter chips are `<span onClick>` (not keyboard accessible) | [site/components.jsx:53-67](../site/components.jsx), [issues.md M10](../issues.md) |
| M11 | Empty `recommendations: []` carries no structured reason | [upskin_api/recommender.py:312-336](../upskin_api/recommender.py), [issues.md M11](../issues.md) |
| M12 | `/model/metrics` leaks a local absolute path (`stale_notes_file`) | [upskin_api/recommender.py:173](../upskin_api/recommender.py), [issues.md M12](../issues.md) |
| M13 | No `.env.example`, no `render.yaml`, no CI manifest | [issues.md M13](../issues.md) |
| M14 | API doesn't load artifacts at process startup despite docs claiming "fail fast" | [upskin_api/recommender.py:479-481](../upskin_api/recommender.py), [issues.md M14](../issues.md) |
| M15 | Generated feature artifacts include eval columns + raw ID lists | `artifacts/handoff/bayesian_handoff_features.csv`, [issues.md M15](../issues.md) |
| M16 | MC-dropout is stochastic with no request-level seed | [upskin_api/model.py:96-114](../upskin_api/model.py), [issues.md M16](../issues.md) |
| M17 | `/health`, `/model/metrics`, `/demo-users` lack `response_model` | [upskin_api/main.py](../upskin_api/main.py), [issues.md M17](../issues.md) |

## Low

| ID | Title | Where |
|---|---|---|
| L1 | Empty `package-lock.json` at root and in `site/`, no `package.json` | [issues.md L1](../issues.md) |
| L2 | Duplicate / deprecated notebooks left in the tree (`ishita/notebooks/Code.ipynb`, `viraj/notebooks/ishita-notebook-runs/`) | [issues.md L2](../issues.md) |
| L3 | `docs/audit_4-28-26.md` is local-only (`.gitignore` ignores `docs/`) | [.gitignore:8](../.gitignore), [issues.md L3](../issues.md) |
| L4 | `@lru_cache(maxsize=1)` prevents artifact reload without restart | [upskin_api/recommender.py:479](../upskin_api/recommender.py), [issues.md L4](../issues.md) |
| L5 | Embedding lookup uses `df.index.to_numpy()` — fragile to a future `reset_index` | [upskin_api/recommender.py:366](../upskin_api/recommender.py), [issues.md L5](../issues.md) |
| L6 | Empty search defaults to popularity, biases new profiles | [upskin_api/recommender.py:209](../upskin_api/recommender.py), [site/BuildProfileFlow.jsx:17](../site/BuildProfileFlow.jsx), [issues.md L6](../issues.md) |
| L7 | Mock route ignores requested `top_n` for demo users | [site/api.js:104-106](../site/api.js), [site/mockData.js:84](../site/mockData.js), [issues.md L7](../issues.md) |
| L8 | Dockerfile has no non-root user and no `HEALTHCHECK` | [Dockerfile](../Dockerfile), [issues.md L8](../issues.md) |
| L9 | Local workspace contains ~2 GB ignored state (`venv/` 1.5 GB, `Datasets/` 504 MB, `artifacts/` 47 MB) | [issues.md L9](../issues.md) |
| L10 | `product_catalog.csv` carries scratch notebook columns (`product_text`, `transformer_text`) | [issues.md L10](../issues.md) |

## Open questions from the audit (still unanswered)
From [issues.md:512-519](../issues.md):
1. Is `viraj/scripts/build_handoff_artifacts.py` canonical or obsolete?
2. Should the Step-6 exclusion policy be a production policy?
3. Is the priority rating prediction (RMSE/MAE) or top-N ranking quality (NDCG, Hit Rate, precision@K)?
4. Should demo `author_id` values be hashed?
5. Was `v001` intentionally produced under scikit-learn 1.8.0?
6. Should mocks ship to production at all?
7. What's the artifact-distribution mechanism for clean CI?
8. Is stochastic MC-dropout acceptable in demos, or should it be seeded?
