# 12 · Roadmap

Recommended sequencing. The "why" for each item is grounded in [11_known_issues.md](11_known_issues.md), [stale.md](../stale.md), and [issues.md](../issues.md). Nothing here changes product scope — the app remains an uncertainty-aware demo recommender; these are honesty, safety, and reliability moves.

## Phase 1 — Immediate fixes (this week)
Goal: remove the biggest train/serve, UX-trust, and security gaps without changing the product story.

1. **Fix the "optional filter applies $75 max" UX bug.** Make `maxPrice` opt-in (toggle + slider), and omit `max_price_usd` from the request when off. [issues.md H7](../issues.md), [site/BuildProfileFlow.jsx:13](../site/BuildProfileFlow.jsx).
2. **Stop showing raw `author_id` in the demo flow.** Render `Profile NN` only; if a stable handle is needed, hash to a short alias. [issues.md M6](../issues.md), [site/DemoProfileFlow.jsx:87](../site/DemoProfileFlow.jsx).
3. **Add `price_usd` to `RecommendationItem`.** The card already expects it; the schema gap is small. [issues.md M9](../issues.md), [upskin_api/schemas.py:35](../upskin_api/schemas.py).
4. **Enforce the Step-6 exclusion list at serving time.** Read `step6_recommendations/recommendation_metrics.json` (or copy the keys into `final_pipeline_summary.json` during artifact export). [issues.md C2](../issues.md).
5. **Add a startup readiness check.** A `@app.on_event("startup")` (or lifespan equivalent) that calls `get_service()` and fails the process on artifact errors. [issues.md M14](../issues.md), [upskin_api/main.py](../upskin_api/main.py).
6. **Strip the local absolute path from `/model/metrics`.** Return a stable identifier (e.g., `"stale_notes_file": "stale.md"`) or remove the field. [issues.md M12](../issues.md).
7. **Cap request shape.** `max_length=50` on `liked_product_ids` and filter lists; ignore unknown filter keys. [issues.md H6](../issues.md), [upskin_api/schemas.py](../upskin_api/schemas.py).

## Phase 2 — Short-term improvements (next ~2 weeks)
Goal: reduce model-honesty risk and remove the most visible deployment fragility.

1. **Replace the `mf_score` proxy.** Export the Ridge ensemble / MF scorer at training time. Load it in `RecommendationService` and use real per-candidate scores. Until done, keep `uses_mf_proxy: true` honest. [stale.md:5](../stale.md), [issues.md C1](../issues.md), [upskin_api/recommender.py:370-388](../upskin_api/recommender.py).
2. **Seed MC-dropout per request.** Derive a deterministic seed from `(run_id, liked_product_ids, top_n)` and expose it in the response for debugging. [issues.md M16](../issues.md), [upskin_api/model.py:96](../upskin_api/model.py).
3. **Add `response_model` to `/health`, `/model/metrics`, `/demo-users`.** Catches drift in contract tests. [issues.md M17](../issues.md).
4. **Add a structured empty-result reason** (filter that removed all candidates, no embeddings, etc.). [issues.md M11](../issues.md), [upskin_api/recommender.py:312](../upskin_api/recommender.py).
5. **Restrict `?api=<url>` overrides.** Only honor it on `localhost`/`127.0.0.1`, or against an allow-list embedded at deploy time. [issues.md M7](../issues.md), [site/api.js:13](../site/api.js).
6. **Make tests fail on scikit-learn `InconsistentVersionWarning`.** Add a `filterwarnings("error", category=InconsistentVersionWarning)` fixture. Pin the venv to 1.8.0. [issues.md H8](../issues.md).
7. **Make filter chips keyboard-accessible.** Render `Chip` as `<button aria-pressed>` when `onClick` is passed. [issues.md M10](../issues.md), [site/components.jsx:53-67](../site/components.jsx).
8. **Drop the production `mockData.js`/`mockExtras.js` script tags** behind a build-time toggle (or move them under an explicit `/preview/` HTML route). [issues.md M8](../issues.md), [site/index.html:89-90](../site/index.html).
9. **Add an artifact distribution mechanism.** A `scripts/fetch_artifacts.sh` that pulls a signed tarball into `artifacts/`, plus a `make build-docker` that runs it. [issues.md H9](../issues.md).

## Phase 3 — Medium-term improvements (next quarter)
Goal: harden serving, sharpen evaluation, productionize the frontend.

1. **Migrate the frontend to a real build pipeline** (Vite or Next, since the env scaffolding already references `NEXT_PUBLIC_UPSKIN_API_URL`). Bundle React production, add SRI on any external scripts, add a basic CSP. [issues.md H11](../issues.md).
2. **Add rate limiting** (`slowapi`, per-IP, per-route on `/recommendations/*`) and request-body size limits at the ASGI layer. [issues.md H6](../issues.md).
3. **Artifact integrity verification.** Store a hash manifest alongside `results_log.csv`; verify before loading; disable `allow_pickle` where possible. [issues.md H10](../issues.md), [upskin_api/model.py:152](../upskin_api/model.py).
4. **Rebuild the matrix split** so the 1-row-per-user holdout and `MIN_USER_RATINGS=10` invariants hold; regenerate downstream artifacts. [issues.md H3](../issues.md).
5. **Improve personalization.** Either export trained user/item vectors from the matrix model, or implement a validated nearest-user signal at serving time. [issues.md H4](../issues.md).
6. **Decouple cold-start "taste" from "harshness"** in `recommend_for_custom`. Shrink `mean_user_rating` toward the global mean for new visitors; document the cold-start mode as content-based. [issues.md H5](../issues.md), [stale.md:30](../stale.md).
7. **Calibrate confidence intervals to be informative.** Current mean width on the 1–5 scale is ~1.83; bring it down with a better-fit uncertainty method (deep ensembles, learned variance) or surface the width honestly when it's too wide. [issues.md M2](../issues.md).
8. **Add golden recommendation tests** for known demo users (top-N IDs + score tolerance). [issues.md H12](../issues.md), [tests/test_upskin_api.py](../tests/test_upskin_api.py).
9. **Add a `render.yaml`, `vercel.json` (already exists), `.env.example`, and a `Makefile`/`justfile`.** Make the env contract explicit. [issues.md M13](../issues.md).
10. **Remove duplicate/deprecated notebooks** (`ishita/notebooks/Code.ipynb`, the `ishita-notebook-runs/` copy) and mark the canonical path in `viraj/viraj.md`. [issues.md L2](../issues.md).

## Phase 4 — Long-term enhancements
Goal: deepen the product or open new directions.

- **Real attribution / explanation layer.** SHAP or attention attribution on the BNN inputs; rename the current copy to "ingredient highlights." [stale.md:37](../stale.md), [issues.md M5](../issues.md).
- **Ingredient-avoidance filters.** Let users exclude specific ingredients with a clear "not medical advice" caveat. [stale.md:62](../stale.md).
- **Save / share a profile.** Token-only (no auth), URL-encoded liked IDs and filters. Be careful not to introduce the user-data trust gap of [issues.md M7](../issues.md).
- **Account-backed history.** If pursued, see [04_auth_and_roles.md](04_auth_and_roles.md) for the recommended provider path (Supabase, given the user CLAUDE.md preference).
- **Live retraining or scheduled re-runs** of the artifact pipeline. Out of scope today: pipeline lives in `ishita/` + `viraj/` notebooks. [stale.md:20](../stale.md).
- **Image URLs in the catalog + responses.** Removes the placeholder fallback and unlocks a richer UI.
- **Ranking-quality metrics** (NDCG, Hit Rate@10, MRR) reported in `/model/metrics` alongside RMSE. [issues.md M1](../issues.md).

## Auth / data / infra hardening (cross-cutting)
- **Auth:** currently not needed (no per-user state). Revisit only if "save profile" or accounts ship — see [04_auth_and_roles.md](04_auth_and_roles.md) for the recommended path. Supabase is the lowest-friction add given the user's stack.
- **DB:** not needed for the current recommender — see [05_database_schema.md](05_database_schema.md). If saved profiles ship, the lightest add is a single Supabase table keyed by an anonymous profile UUID storing `liked_product_ids` and `filters`.
- **Docker hardening:** non-root user, `HEALTHCHECK`, multi-stage build to drop unused training deps. [issues.md L8](../issues.md).
- **CI:** add a single GitHub Actions workflow for `pytest` + `docker build` against a small artifact fixture. None exists today. `Confirmed from code`.
- **Observability:** structured JSON logs for `/recommendations/*` (request_id, top_n, mc_samples, candidate count, predicted score histogram), plus a Render dashboard for cold-start latency.

## Product polish
- Add screenshots to the README (the TODO at [README.md:52](../README.md)).
- Add a "wide interval" copy line on `RecCard` when `(upper − lower) > 1.5`. The interval bar already exists; the message doesn't. [issues.md M2](../issues.md).
- Add a clearly labeled "Refresh" affordance on the results page to acknowledge MC-dropout stochasticity (until M16 is fixed).
- Surface the matrix model label (`canonical_matrix_model`) in `ModelTransparency` more prominently — it already comes back in `/health` and `/model/metrics`. [upskin_api/recommender.py:147-148](../upskin_api/recommender.py).
