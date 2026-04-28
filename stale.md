# Stale / Prototype Items

These are known gaps that should not be hidden in the frontend or API.

## Full MF Candidate Scorer Missing

The current Step 6 recommendation candidate scoring uses a user/product mean MF proxy because the full all-candidate matrix factorization scorer/model was not exported.

Impact:
- Recommendation scoring is valid as a class-demo prototype.
- The BNN model results and uncertainty metrics are real for the saved evaluation task.
- A production website should export the real MF model or precomputed all-user/all-product MF scores.

Fix:
- Export the trained MF model parameters, user/item mappings, and `predict_user_all`.
- Replace proxy `mf_score` generation in the recommendation API.
- Keep `uses_mf_proxy` in `/health` and `/model/metrics` until this is fixed.

## No Live Retraining

The API serves saved artifacts only. New products, new reviews, and new users do not update the model until the pipeline is rerun.

Fix:
- Rerun artifact generation.
- Add a new version under `artifacts/versions/`.
- Update `results_log.csv`.

## Custom User Personalization Is Content-Based

For brand-new visitors, liked product IDs create a content profile from transformer embeddings. This is not the same as a trained historical user profile.

Fix:
- Add account/user persistence if needed.
- Collect explicit ratings over time.
- Retrain or update user-level recommendation features.

## Explanations Are Heuristic, Not Model Attribution

The API explanation text is generated from product metadata, ingredient keyword groups, content similarity, and confidence bucket. It is not SHAP, attention attribution, or a learned explanation model.

Impact:
- Explanation text is useful for a class demo and frontend UX.
- It should not be described as a formal model-attribution method.

Fix:
- Add model attribution or feature contribution analysis.
- Export explanation metadata from the notebook pipeline.
- Keep frontend copy phrased as "why this may fit" rather than "the model proved this because".

## Risk Adjustment Uses Fixed Penalty

The API computes `risk_adjusted_score = predicted_score - 0.5 * uncertainty`, matching the Step 6 prototype behavior. The penalty weight is not yet learned or tuned as a separate deployment artifact.

Impact:
- Ranking is uncertainty-aware.
- The exact risk penalty is a serving rule, not a trained model parameter.

Fix:
- Export the risk penalty from the pipeline config or tune it on validation ranking metrics.
- Add the selected penalty to model metadata and `/model/metrics`.

## Medical / Allergy Safety Not Modeled

The model recommends based on ratings, content similarity, metadata, and uncertainty. It does not diagnose skin conditions or guarantee ingredient safety.

Fix:
- Add explicit ingredient avoidance filters.
- Add dermatologist/safety disclaimers in the UI.
