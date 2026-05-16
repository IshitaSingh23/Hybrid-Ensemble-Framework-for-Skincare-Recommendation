# 13 · Prompt Context for Future AI Agents

> Hand this file to any agent or contributor coming into the repo cold. It exists so the agent doesn't have to relearn what the product is, how the code is organized, what to preserve, or what to be careful about.

## App purpose and goals
- **Up Skin is a class-demo skincare recommender** with one defining feature: it surfaces model uncertainty honestly (calibrated 95% intervals + a three-bucket confidence label) instead of pretending every prediction is decisive.
- Built around a STAT-542 (Statistical Learning, UIUC) graduate project. Not a real product; not a medical tool.
- **Target visitor:** a curious reviewer who picks 3–8 products they've liked (or picks one of ~25 anonymized demo profiles) and gets a ranked list of likely-loved products with confidence indicators.

## Hard product rules — preserve these
1. **No medical, dermatology, allergy, or condition-treatment claims.** Phrasing is *"may fit your preferences"*, not *"will fix your skin"*. See [site/Recommendations.jsx:4-7](../site/Recommendations.jsx), [site/site.jsx:94-97](../site/site.jsx), [README.md:108-114](../README.md).
2. **Honest uncertainty.** Every recommendation card ships a score, a 1–5 interval bar, a confidence bucket label, an `uncertainty` number, and a risk-adjusted score. Don't hide any of these.
3. **Live data by default.** The frontend must call the FastAPI backend in production; the offline preview (`?preview=1` / `?mock=1`) is design-review-only.
4. **`prefers-reduced-motion` is respected globally** — never reintroduce required animations that don't degrade.
5. **No model/data values get hardcoded in the frontend.** No `run_id`, no demo IDs, no recommendation rows, no metrics. Everything lives in the API. See [docs/frontend_handoff_prompt.md:31](../docs/frontend_handoff_prompt.md).

## Stack
- **Frontend:** static HTML + React 18 UMD + Babel-standalone. No bundler. Single page, view-state SPA. Components in `site/*.jsx`. CSS tokens in `site/colors_and_type.css`. Hosted on Vercel from `site/`.
- **Backend:** FastAPI + Uvicorn + Pydantic v2. Single package `upskin_api/`. CPU-only PyTorch. scikit-learn `ColumnTransformer` + PCA loaded from joblib. Dockerized for Render.
- **Persistence:** **filesystem only.** No database, no Redis, no auth provider. All recommendations come out of artifacts under `artifacts/versions/<run_id>/…` plus `artifacts/matrix/*` and `artifacts/transformer/*`.
- **Tests:** 4 pytest contract-smoke tests in `tests/test_upskin_api.py`. No CI.

## Architecture guardrails — don't break these
- **`get_service()` is `@lru_cache`'d.** Constructing it is expensive (model + CSVs). Restart is the only safe way to reload. If you need a reload endpoint, add it explicitly.
- **Best-run resolution is dynamic.** `RecommendationService` picks the lowest `test_bnn_rmse` from `artifacts/versions/results_log.csv` unless `UPSKIN_MODEL_RUN_ID` overrides. The Docker image pins `v002`.
- **Model bundle is loaded lazily.** A bad artifact only surfaces on the first request, not at boot. The roadmap calls for a startup hook ([12_roadmap.md](12_roadmap.md) Phase 1).
- **Frontend state is local-only.** No Context, no global store. Don't introduce one for a small feature.
- **Confidence buckets and copy** are derived from `confidence_bucket` strings the backend emits: `high_confidence`, `medium_confidence`, `low_confidence`. Keep them in sync between [upskin_api/model.py:81-86](../upskin_api/model.py) and [site/Recommendations.jsx:4-7](../site/Recommendations.jsx).

## Behaviors to preserve
- **Cold-start UX.** Render free dynos sleep. The frontend pre-warms `/health` from `index.html` and shows progressive "Backend waking" copy in `LoadingState`. Don't strip these.
- **Stable view-state shell.** `Site` manages `view` (welcome / demo / custom / loading / results / noresults / error). Adding a new view should be additive, not a router rewrite.
- **Honest model sheet.** `ModelTransparency` reads `/model/metrics` and renders BNN/MF/hybrid RMSE/MAE, dropout rate, MC samples, calibrated coverage. Don't show metrics that don't come from the API.
- **`stale.md` is the canonical honesty doc.** It is copied into the Docker image and referenced by `/model/metrics`. Don't delete; update it when you change a proxy / heuristic.

## Weak points to watch (do not regress)
| Risk | Why it matters | Touchpoint |
|---|---|---|
| `mf_score` train/serve skew | BNN trained on real MF feature, served on user/product mean proxy | [upskin_api/recommender.py:370-388](../upskin_api/recommender.py), [stale.md:5](../stale.md) |
| Step-6 exclusion list not enforced | "Skincare-only" product boundary leaks through | [upskin_api/recommender.py:83, 355-361](../upskin_api/recommender.py) |
| Stochastic MC-dropout | Same profile can flip confidence bucket between requests | [upskin_api/model.py:96-114](../upskin_api/model.py) |
| `?api=<url>` is unrestricted | Shared link can redirect user data | [site/api.js:13, 38-46](../site/api.js) |
| Mock layer ships to prod | `?mock=1` shows fake data on the live page | [site/index.html:89-90](../site/index.html) |
| "Optional" filters apply $75 max | UX contradiction in Build flow Step 2 | [site/BuildProfileFlow.jsx:13, 54-65](../site/BuildProfileFlow.jsx) |
| Demo profile shows raw `author_id` | Contradicts "anonymized" copy | [site/DemoProfileFlow.jsx:87](../site/DemoProfileFlow.jsx) |
| Public path leaked via `/model/metrics` | `stale_notes_file` is an absolute local path | [upskin_api/recommender.py:173](../upskin_api/recommender.py) |
| No rate limit on `/recommendations/*` | One client can pin the Render CPU | [upskin_api/main.py:64-86](../upskin_api/main.py) |
| Babel-in-browser + no SRI | Slow first paint and unpkg-dependent | [site/index.html:84-86](../site/index.html) |

A full catalog with line-level evidence is in [11_known_issues.md](11_known_issues.md) and the original [issues.md](../issues.md).

## Editing expectations
- **Default to small, targeted edits.** Don't refactor the static site into a bundler unless explicitly asked — that's a Phase-3 roadmap item, not a side effect of a small change.
- **Honor the design tokens.** New colors go in `:root` (`colors_and_type.css`); new components reuse the existing buttons / chips / eyebrow / step header primitives in `components.jsx`.
- **Never hardcode model values** (`run_id`, RMSE, demo IDs, recommendation rows, metrics) into the frontend. Pull from the API.
- **Update `stale.md`** if you change a heuristic that the doc currently describes (`mf_score` proxy, risk penalty, explanations, etc.). The doc and the code must agree.
- **Keep `prefers-reduced-motion` working.** Don't introduce CSS animations that don't degrade through the global override.
- **Don't add console.log or printf-style logging in committed code.** The CLAUDE.md hook policy flags this.
- **Don't add screenshots/binary assets** without checking — the `docs/` directory is git-ignored, and several decorative SVGs live under `site/assets/`.
- **Use the existing pytest suite** as the smoke gate. If you touch `upskin_api/`, run `UPSKIN_MC_SAMPLES=3 pytest tests/test_upskin_api.py`.

## Quick map of the repo
- `site/` — static frontend.
- `upskin_api/` — FastAPI service.
- `artifacts/` — model bundles, catalog, embeddings, user_history (git-ignored, required at runtime).
- `docs/` — API contract + frontend handoff + STAT-542 proposal PDF (git-ignored).
- `tests/` — pytest contract tests.
- `ishita/`, `viraj/` — notebooks + experiments that produced the artifacts (not needed to run the app).
- `stale.md` — honest list of prototype caveats.
- `issues.md` — 40+ findings audit (local-only doc).
- `notes/` — this folder.

## When the user asks you to "improve" or "harden" something
Refer to the phased plan in [12_roadmap.md](12_roadmap.md) before doing anything. The phase ordering exists to avoid two common mistakes: (1) productionizing the frontend before fixing the train/serve skew that makes the recommendations themselves suspect, and (2) adding auth/DB before there's a feature that actually needs persistence.

If asked to "add auth," confirm whether the user actually wants per-user state — currently nothing in the app uses it. If yes, see [04_auth_and_roles.md](04_auth_and_roles.md) (intentionally empty) and propose Supabase as the lightest-friction add given the user's broader stack preference.
