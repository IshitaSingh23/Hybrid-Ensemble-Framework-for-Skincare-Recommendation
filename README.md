<div align="center">
  <img src="site/assets/wordmark.svg" alt="Up Skin" width="200"/>

  <br/>
  <em>A skincare studio, in software.</em>
  <br/><br/>

  <p>
    Discover skincare you'll likely love — through the products you already adore,<br/>
    the ingredients in their neighborhood, and the model's confidence shown honestly.
  </p>

  <p>
    <a href="https://up-skin.vercel.app">Live demo</a> ·
    <a href="https://upskin-api.onrender.com/health">API status</a> ·
    <a href="docs/backend_api_contract.md">API contract</a> ·
    <a href="site/README.md">Frontend docs</a>
  </p>
</div>

---

## What it is

Up Skin is a recommender for skincare. You tell it a handful of products you already love (or pick a demo profile), and it returns products you're likely to enjoy — each with a predicted rating, a calibrated confidence interval, and an honest label for how sure the model actually is.

It's built around the idea that a recommender shouldn't pretend. When the model is uncertain, the card says so.

## Try it

Two ways in, both live on the [demo site](https://up-skin.vercel.app):

- **Build my profile** — search for 3–8 products you've loved, set an optional price ceiling and category filter, and generate fresh recommendations. ([site/BuildProfileFlow.jsx](site/BuildProfileFlow.jsx))
- **Use a demo profile** — pick one of 25 anonymized profiles with their like history pre-loaded. One click to results. ([site/DemoProfileFlow.jsx](site/DemoProfileFlow.jsx))

Both flows land on the same recommendations grid.

## How recommendations work

Each card shows a predicted score from 1.0 to 5.0, a 95% interval the score is likely to fall inside, and one of three honest labels ([site/Recommendations.jsx](site/Recommendations.jsx:4)):

| Label | Meaning |
|---|---|
| **Confident pick** | The model is fairly sure you'll like this. |
| **Good lead** | A reasonable match — worth a closer look. |
| **Soft suggestion** | The model is less sure here. Take it lightly. |

A narrow interval bar means the model is decisive. A wide bar means it's hedging — that's the point of showing it.

## Screenshots

<!-- TODO: capture three PNGs and drop them in docs/screenshots/, then uncomment -->
<!-- ![Welcome](docs/screenshots/welcome.png) -->
<!-- ![Build profile flow](docs/screenshots/build-profile.png) -->
<!-- ![Recommendations](docs/screenshots/recommendations.png) -->

_Screenshots forthcoming. Capture from the [live site](https://up-skin.vercel.app) and add to `docs/screenshots/`._

## Under the hood

The recommendation service is a **Bayesian Neural Network with MC dropout** for uncertainty quantification, blended with a Ridge-based matrix-factorization baseline. The final score is a hybrid (default `0.7 × BNN + 0.3 × matrix`), and the prediction interval comes from MC-dropout samples calibrated to 95% coverage. See [upskin_api/recommender.py](upskin_api/recommender.py) and [upskin_api/model.py](upskin_api/model.py).

The frontend never invents data: products, demo profiles, recommendations, and model metrics all come live from the FastAPI service. There's an opt-in offline preview mode (`?preview=1`) for design review when the backend is asleep.

## Tech stack

| Layer | Stack |
|---|---|
| Frontend | React 18 (via Babel-standalone), plain HTML/CSS — no build step |
| Backend | FastAPI · Uvicorn · Pydantic |
| ML | PyTorch (BNN) · scikit-learn · LightGBM · XGBoost · sentence-transformers |
| Hosting | Vercel (static frontend) · Render / Docker (FastAPI backend) |

## Project layout

```
up-skin/
├── site/              Frontend — static React, Vercel-deployed
├── upskin_api/        FastAPI service — recommender, model bundle, schemas
├── docs/              API contract, audit, design handoff, proposal
├── Datasets/          Training data
├── artifacts/         Model run artifacts (BNN weights, calibration)
├── ishita/  viraj/    Per-contributor notebooks and experiments
├── tests/             Backend test suite
├── Dockerfile         Backend container for Render / Railway
├── requirements.txt       ML stack (notebook work)
└── requirements-api.txt   FastAPI-only deps (production)
```

## Run it locally

Two terminals.

```bash
# Backend (FastAPI on :8000)
python -m pip install -r requirements-api.txt
uvicorn upskin_api.main:app --reload --port 8000

# Frontend (static on :5173)
python -m http.server 5173 --directory site
```

Open <http://localhost:5173/>. The page calls `http://localhost:8000` by default.

For runtime API-URL config, offline preview, the full file map, and deployment notes, see [site/README.md](site/README.md). For the wire format the frontend expects, see [docs/backend_api_contract.md](docs/backend_api_contract.md).

## Hard rules

These are product principles, not implementation details — they shape what the UI is and isn't allowed to say:

- **No medical, dermatology, allergy, or condition-treatment claims.** Phrasing is *"may fit your preferences"*, not *"will fix your skin"*.
- **Honest uncertainty.** Confidence buckets and intervals are shown alongside every score. The model never pretends to be more sure than it is.
- **Live data by default.** Offline mock data only loads when explicitly enabled.
- **Reduced-motion respected.** Staggered reveals and shimmer collapse to instant when the OS asks for less motion.

## Credits

Up Skin began as a STAT-542 (Statistical Learning, UIUC) graduate project — see [docs/proposal-STAT-542.pdf](docs/proposal-STAT-542.pdf). Notebook experiments and feature work live under [ishita/](ishita/) and [viraj/](viraj/). Design system and frontend handoff documented in [docs/frontend_handoff_prompt.md](docs/frontend_handoff_prompt.md).
