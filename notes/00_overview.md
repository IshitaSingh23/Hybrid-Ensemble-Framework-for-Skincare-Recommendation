# 00 · Overview

## Purpose
Up Skin is a class-demo skincare recommender that returns products a visitor is likely to enjoy, paired with a predicted 1.0–5.0 rating, a calibrated 95% interval, and a textual "confidence bucket." Confirmed from code: [README.md](../README.md), [site/Recommendations.jsx](../site/Recommendations.jsx), [upskin_api/recommender.py](../upskin_api/recommender.py).

## Product
- **What it is:** an uncertainty-aware recommendation UI on top of a FastAPI model service. Confirmed from code: [upskin_api/main.py](../upskin_api/main.py), [site/site.jsx](../site/site.jsx).
- **Who it serves:** demo visitors and class reviewers, not a real user base. The "anonymized" demo profiles are seeded from `artifacts/matrix/user_history.csv`. Confirmed from code: [upskin_api/recommender.py:107](../upskin_api/recommender.py).
- **Primary problem solved:** show that a recommender can *signal its own uncertainty* (MC-dropout intervals and confidence labels) rather than always projecting decisiveness. Confirmed from code: [README.md](../README.md), [site/Recommendations.jsx:4](../site/Recommendations.jsx).
- **What it explicitly does not do:** medical, dermatology, allergy, condition-treatment claims. Disclaimer is rendered in the footer and the model sheet. Confirmed from code: [site/site.jsx:94](../site/site.jsx), [site/ModelTransparency.jsx:61](../site/ModelTransparency.jsx).

## Core user journey
1. Land on the welcome screen with two CTAs: **Build my profile** or **Use a demo profile**. Confirmed from code: [site/Welcome.jsx](../site/Welcome.jsx).
2. Either search the catalog and pick 1–N liked products with optional filters (max price, top-N count, category chips drawn from selected/searched items), or pick one of up to 25 anonymized demo profiles. Confirmed from code: [site/BuildProfileFlow.jsx](../site/BuildProfileFlow.jsx), [site/DemoProfileFlow.jsx](../site/DemoProfileFlow.jsx).
3. Frontend calls `GET /recommendations/{author_id}` (demo) or `POST /recommendations/custom` (build). Confirmed from code: [site/api.js](../site/api.js).
4. Backend builds a profile vector (mean of source-product transformer embeddings), constructs a candidate feature frame, runs the MC-dropout BNN for `mc_samples` passes, computes mean + std + 95% calibrated interval, and ranks by risk-adjusted score. Confirmed from code: [upskin_api/recommender.py:264](../upskin_api/recommender.py), [upskin_api/model.py:96](../upskin_api/model.py).
5. Results page renders product cards with score, interval bar, risk-adjusted score, uncertainty, optional price, and a heuristic explanation. Confirmed from code: [site/Recommendations.jsx](../site/Recommendations.jsx).

## Stack at a glance
- **Frontend:** static HTML + React 18 UMD + Babel-standalone (no bundler, no build step). Confirmed from code: [site/index.html:84-115](../site/index.html).
- **Backend:** FastAPI / Uvicorn / Pydantic v2. Confirmed from code: [upskin_api/main.py:5](../upskin_api/main.py), [requirements-api.txt](../requirements-api.txt).
- **Model:** PyTorch MC-dropout BNN (`MCDropoutBNN`, two hidden layers, sigmoid-scaled to 1–5), plus a sklearn `ColumnTransformer` preprocessor and PCA over sentence-transformer embeddings. Confirmed from code: [upskin_api/model.py:15-37](../upskin_api/model.py).
- **Persistence:** filesystem only. CSV / NPZ / joblib / JSON under `artifacts/` selected by `artifacts/versions/results_log.csv`. Confirmed from code: [upskin_api/artifacts.py](../upskin_api/artifacts.py).
- **Hosting:** Vercel (static `site/`) + Render (Dockerized FastAPI). Confirmed from code: [site/vercel.json](../site/vercel.json), [Dockerfile](../Dockerfile), [docs/backend_api_contract.md:151](../docs/backend_api_contract.md).

## Current maturity
- **Live demo URLs:** <https://up-skin.vercel.app> (frontend) and <https://upskin-api.onrender.com> (API). Confirmed from code: [README.md](../README.md), [docs/backend_api_contract.md:151](../docs/backend_api_contract.md).
- **Test coverage:** 4 pytest contract-smoke tests against the FastAPI app. Confirmed from code: [tests/test_upskin_api.py](../tests/test_upskin_api.py).
- **No CI configured** (`Strongly inferred` — no `.github/`, no `Makefile`, no `package.json`).
- **No auth, no DB:** the API is fully read-only over baked artifacts and serves recommendations from a frozen model bundle. Confirmed from code: [upskin_api/main.py](../upskin_api/main.py).

## Repo reality (implemented vs aspirational)
- **Implemented:** end-to-end recommendation flow, demo profiles, custom liked-product flow, model transparency sheet, MC-dropout uncertainty intervals, hybrid (BNN + matrix-mean) feature, ingredient/highlight-keyword "explanations," offline preview mode behind `?preview=1` / `?mock=1`. Confirmed from code: [site/api.js:53](../site/api.js), [upskin_api/recommender.py](../upskin_api/recommender.py).
- **Prototype / proxy parts (also self-declared in `stale.md`):**
  - `mf_score` in the served feature frame is a user/product mean **proxy**, not the trained matrix-factorization scorer. Confirmed from code: [upskin_api/recommender.py:370-377](../upskin_api/recommender.py), [stale.md:5](../stale.md).
  - "Risk-adjusted score" = `pred − 0.5 × uncertainty` — a fixed serving rule, not a tuned hyperparameter. Confirmed from code: [upskin_api/recommender.py:321](../upskin_api/recommender.py), [stale.md:51](../stale.md).
  - Explanations are keyword/category templates, not model attribution. Confirmed from code: [upskin_api/recommender.py:447-476](../upskin_api/recommender.py), [stale.md:37](../stale.md).
  - Step-6 skincare exclusion filter (e.g., "Hair Removal", "Wellness") is documented but **not enforced at serving time** — the API reads `filter_report` from a JSON that does not contain it. Confirmed from code: [upskin_api/recommender.py:83](../upskin_api/recommender.py), [issues.md C2](../issues.md).
- **Not implemented:** image URLs in API responses, accounts/persistence, retraining loop, secret/auth, rate limiting, CSP/SRI, structured empty-state reasons. Confirmed from code: [upskin_api/schemas.py](../upskin_api/schemas.py), [site/index.html:84](../site/index.html), [issues.md](../issues.md).

## Honest tagline (from README)
> "A recommender shouldn't pretend. When the model is uncertain, the card says so." — [README.md](../README.md)
