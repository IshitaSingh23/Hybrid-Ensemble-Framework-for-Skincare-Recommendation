# 10 · Deployment

## Targets in production
| Layer | Host | URL |
|---|---|---|
| Frontend (static) | Vercel | <https://up-skin.vercel.app> |
| Backend (FastAPI in Docker) | Render | <https://upskin-api.onrender.com> |

Confirmed from code: [README.md:13-16](../README.md), [docs/backend_api_contract.md:151-153](../docs/backend_api_contract.md).

## Frontend deployment (Vercel)

### Build
- No bundler. The `site/` directory is uploaded as-is and served statically. Confirmed from code: [site/vercel.json](../site/vercel.json) — `framework: null`, `buildCommand: null`, `installCommand: null`, `outputDirectory: "."`.
- The `vercel.json` lives **inside** `site/`. To use it, Vercel's project root must be set to `site/`, or the deployment must be invoked from `site/`. The site README spells this out: "If you set the Vercel Project Root manually, point it at `site/`." Confirmed from code: [site/README.md:121-123](../site/README.md).

### HTTP headers / caching (from `site/vercel.json`)
- `/runtime-config.js` → `Content-Type: application/javascript; charset=utf-8`, `Cache-Control: no-cache`. Lets you edit the runtime API URL per environment without invalidating the static cache.
- `/(.*)\\.(jsx|js|css|svg|woff|woff2)$` → `Cache-Control: public, max-age=300, must-revalidate` (5-minute cache, useful for the Babel-compiled JSX files).

### Pointing the frontend at the API
- Production: edit `runtime-config.js` so it sets `window.__UPSKIN_RUNTIME_CONFIG.apiUrl = "https://upskin-api.onrender.com"` for non-local hostnames. The shipped file already has this default. Confirmed from code: [site/runtime-config.js](../site/runtime-config.js).
- Alternative: inject `window.__UPSKIN_API_URL = "<url>"` before `api.js` loads.
- The handoff doc lists a `UPSKIN_API_URL` Vercel env var ([docs/backend_api_contract.md:170](../docs/backend_api_contract.md)), but with the current bundle-less setup, env vars don't reach the page — `runtime-config.js` is the actual mechanism.

## Backend deployment (Render Docker service)

### Container build (Dockerfile)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV UPSKIN_PROJECT_ROOT=/app
ENV UPSKIN_MODEL_RUN_ID=v002
ENV UPSKIN_CORS_ORIGINS=https://up-skin.vercel.app,https://up-skin.onrender.com
ENV PORT=8000
COPY requirements-api.txt /app/requirements-api.txt
RUN pip install --no-cache-dir -r /app/requirements-api.txt
COPY upskin_api  /app/upskin_api
COPY stale.md    /app/stale.md
COPY docs/backend_api_contract.md /app/docs/backend_api_contract.md
COPY artifacts   /app/artifacts
EXPOSE 8000
CMD ["sh", "-c", "uvicorn upskin_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```
Confirmed from code: [Dockerfile](../Dockerfile). `.dockerignore` keeps the image lean (`venv/`, `__pycache__/`, `Datasets/`, etc.). Confirmed from code: [.dockerignore](../.dockerignore).

### What gets baked into the image
- The full `upskin_api/` package.
- **All of `artifacts/`** — including the 47 MB+ saved model bundles, embeddings, catalog, user_history, train_df. This is required because `artifacts/` is git-ignored ([issues.md H9](../issues.md)).
- `stale.md` (so the running app can reference its own honesty doc) and `docs/backend_api_contract.md`.

### Render env vars (recommended)
```
UPSKIN_PROJECT_ROOT=/app
UPSKIN_MODEL_RUN_ID=v002
UPSKIN_CORS_ORIGINS=https://up-skin.vercel.app
UPSKIN_MC_SAMPLES=25
```
Confirmed from code: [docs/backend_api_contract.md:160-166](../docs/backend_api_contract.md). Lowering `UPSKIN_MC_SAMPLES` is important on a small Render dyno — the default `model_config.mc_samples = 100` makes recommendation latency dominate cold-start budget.

### Render specifics (`Strongly inferred` — no `render.yaml` checked in)
- The Render service is a **Docker web service**, not a Native Python build — both because the Dockerfile is the canonical entrypoint and because the API requires PyTorch + sklearn + joblib loading that Render's static buildpacks don't ship.
- The free dyno **sleeps**. The frontend has explicit cold-start UX (`LoadingState` + `/health` warmup fetch) to compensate. [site/States.jsx](../site/States.jsx), [site/index.html:96-101](../site/index.html).
- No persistent disk is needed; the artifact bundle is fully baked into the image.

## Deployment dependencies / order
1. **Generate artifacts locally** (notebook pipeline under `ishita/` + `viraj/`) — these live outside this overview but produce `artifacts/versions/<run_id>/…`.
2. **Verify the run** appears in `artifacts/versions/results_log.csv` and that all six per-run files exist. Confirmed from code: [docs/backend_api_contract.md:41-50](../docs/backend_api_contract.md).
3. **Build and push the Docker image** (Render does this on git push to its tracked branch).
4. **Frontend deploy** is independent of the backend deploy; the frontend will simply show the "Backend waking" UX until the API is ready.
5. **CORS** must list the frontend origin; otherwise every frontend call fails preflight.

## Risks and failure points
- **Missing artifacts.** `Dockerfile:19` requires `COPY artifacts /app/artifacts`. A clean clone has no artifacts, so a fresh CI build fails immediately. There is **no artifact distribution mechanism** in the repo (no LFS, no S3 download script). [issues.md H9](../issues.md), [issues.md H10](../issues.md).
- **scikit-learn version drift.** Pickles were produced under 1.8.0; some local venvs run 1.6.1. This silently changes feature transforms. The runtime `requirements-api.txt` pins 1.8.0 ✅, but `requirements.txt` (used by notebooks) pins 1.6.1. [issues.md H8](../issues.md).
- **Cold-start blindness.** `get_service()` is lazy. A bad artifact only fails on the first request, not on uvicorn boot. Add a startup hook to load the bundle. [issues.md M14](../issues.md).
- **Public path leakage.** `/model/metrics` returns `stale_notes_file = "/Users/.../up-skin/stale.md"` — a local absolute path baked into a saved JSON. [issues.md M12](../issues.md).
- **Browser-compiled JSX.** No SRI on `unpkg.com` scripts, no CSP. Any compromise of unpkg's CDN executes in users' browsers. [issues.md H11](../issues.md).
- **Public expensive endpoints.** `/recommendations/*` have no rate limit, no body cap; an attacker can pin the CPU on a small dyno. [issues.md H6](../issues.md).
- **Docker container runs as root** with no `HEALTHCHECK`. [issues.md L8](../issues.md).
- **`?api=<url>` is unrestricted** in production, so a shared link can redirect user activity to an attacker's CORS-enabled endpoint. [issues.md M7](../issues.md).
- **Mock layer is shipped to production.** `index.html` always loads `mockData.js` / `mockExtras.js`; `?mock=1` flips them on. Designed for prototype/demo, but means a hosted page can render fake products and metrics. [issues.md M8](../issues.md).
- **No CI** (no `.github/workflows/`). All build/test happens locally + Render's build step. `Confirmed from code` — no CI manifests.

## Environment separation clues
- Vercel + Render production URLs are the only deployment targets referenced in the repo.
- `localhost:8000` is the canonical local target.
- No staging environment, no `.env.staging`, no `render.yaml` — separation is informal. `Confirmed from code`.

## Recommended next deployment steps
1. Add a `render.yaml` and a `.env.example` so the env contract is in the repo. [issues.md M13](../issues.md).
2. Add an artifact-fetch step (LFS, signed S3 URL, or a release attachment) so Docker builds without local state. [issues.md H9](../issues.md).
3. Add a FastAPI startup hook that constructs `RecommendationService` and exits non-zero on failure. [issues.md M14](../issues.md).
4. Migrate the frontend to a Vite (or Next) build with SRI on third-party scripts. [issues.md H11](../issues.md).
5. Add rate limiting (slowapi or per-IP middleware) + body-size and list-length caps. [issues.md H6](../issues.md).
6. Verify Docker image integrity (`HEALTHCHECK /health`, non-root user). [issues.md L8](../issues.md).
