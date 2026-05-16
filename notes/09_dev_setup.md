# 09 · Dev Setup

## Runtime versions
| Tool | Version | Source |
|---|---|---|
| Python (image) | 3.11-slim | [Dockerfile:1](../Dockerfile) |
| Python (local pin doc) | 3.11.14 via `~/.venvs/global/bin/python` | global user CLAUDE.md (not project-specific) |
| FastAPI | 0.117.1 | [requirements-api.txt:1](../requirements-api.txt) |
| Uvicorn | 0.32.1 (`[standard]`) | [requirements-api.txt:2](../requirements-api.txt) |
| Pydantic | 2.10.6 | [requirements-api.txt:3](../requirements-api.txt) |
| PyTorch | 2.11.0 (CPU) | [requirements-api.txt:8](../requirements-api.txt) |
| scikit-learn | **1.8.0** in API, **1.6.1** in `requirements.txt` (notebook stack) — version drift flagged in [issues.md H8](../issues.md) | [requirements-api.txt:6](../requirements-api.txt), [requirements.txt](../requirements.txt) |
| pytest / httpx | 8.3.5 / 0.28.1 | [requirements-api.txt:9-10](../requirements-api.txt) |
| Frontend runtime | React 18.3.1 UMD + Babel 7.29 standalone (from unpkg) | [site/index.html:84-86](../site/index.html) |
| Node / npm | Not used by the build. Two empty `package-lock.json` files exist (no `package.json`) — flagged in [issues.md L1](../issues.md). | repo root |

## Install
```bash
cd /Users/veerr_89/Work/projects/up-skin

# Recommended — backend-only (matches Docker)
python3.11 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-api.txt
```
The full `requirements.txt` (notebook stack: ipython, jupyter, matplotlib, transformers, lightgbm, xgboost, …) is **not** needed to run the API or the frontend. Use it only for the modeling notebooks under `ishita/` and `viraj/`.

## Run
Two terminals.
```bash
# Backend — FastAPI on :8000
uvicorn upskin_api.main:app --reload --host 0.0.0.0 --port 8000

# Frontend — any static server on :5173
python -m http.server 5173 --directory site
```
Open <http://localhost:5173/>. The page calls `http://localhost:8000` by default. Confirmed from code: [README.md:93-103](../README.md), [site/README.md:13-37](../site/README.md), [site/api.js:18-32](../site/api.js).

For faster local recommendation calls (the default `mc_samples=100` is slow on CPU):
```bash
UPSKIN_MC_SAMPLES=10 uvicorn upskin_api.main:app --reload --port 8000
```

To force the latest pipeline (v002, Ridge-backed):
```bash
UPSKIN_MODEL_RUN_ID=v002 UPSKIN_MC_SAMPLES=25 uvicorn upskin_api.main:app --port 8000
```
Confirmed from code: [docs/backend_api_contract.md:33-37](../docs/backend_api_contract.md).

## Tests
```bash
UPSKIN_MC_SAMPLES=3 pytest tests/test_upskin_api.py
```
Four contract-smoke tests against the real FastAPI app — they require the local `artifacts/` directory. Confirmed from code: [tests/test_upskin_api.py](../tests/test_upskin_api.py).

⚠️ A read-only audit ([issues.md H8](../issues.md)) confirmed that the local `venv` runs scikit-learn `1.6.1` while the saved preprocessor was pickled under `1.8.0`. The tests pass but emit `InconsistentVersionWarning`. If you can, recreate the venv against `requirements-api.txt`'s `scikit-learn==1.8.0`.

## Required env vars
| Variable | Used by | Default | Notes |
|---|---|---|---|
| `UPSKIN_PROJECT_ROOT` | [upskin_api/artifacts.py:46](../upskin_api/artifacts.py) | walks parents until `artifacts/versions/results_log.csv` is found | Set to repo root in Docker. |
| `UPSKIN_MODEL_RUN_ID` | [upskin_api/artifacts.py:77](../upskin_api/artifacts.py) | best `test_bnn_rmse` | Set to `v002` in Docker. |
| `UPSKIN_CORS_ORIGINS` | [upskin_api/main.py:28](../upskin_api/main.py) | localhost + production hosts | Comma-separated. |
| `UPSKIN_MC_SAMPLES` | [upskin_api/recommender.py:71](../upskin_api/recommender.py) | `model_config.mc_samples` (100 on v002) | Lower for local dev / tests. |
| `PORT` | Dockerfile / Uvicorn | `8000` | Render injects this. |
| `NEXT_PUBLIC_UPSKIN_API_URL` | [site/api.js:43](../site/api.js) | unset | Optional; used only if the site is bundled into a Next/Vite app. |
| `window.__UPSKIN_RUNTIME_CONFIG.apiUrl` | runtime-config.js | host-aware default | Edit at deploy time on static hosts. |

There is **no `.env.example`** in the repo — this is flagged in [issues.md M13](../issues.md). The list above is the de-facto contract.

## Local setup steps
1. **Clone the repo** *and* obtain the `artifacts/` directory out of band. `artifacts/` is in `.gitignore`. Without it, the API fails fast at the first `/health` call with `FileNotFoundError: Missing required model artifacts: …`. Confirmed from code: [upskin_api/model.py:148-150](../upskin_api/model.py), [.gitignore:6](../.gitignore), [issues.md H9](../issues.md).
2. Create the venv, install `requirements-api.txt`, run uvicorn.
3. In another terminal, serve `site/` statically. Reload reflects changes immediately (no build step).
4. Sanity-check `<http://localhost:8000/health>` — should return `{"status": "ok", "run_id": "<id>", …}`.

## Service linking
- **Frontend ↔ Backend:** The frontend resolves the API URL via the priority chain documented in [site/README.md:40-49](../site/README.md). For local dev, no config needed.
- **Backend ↔ artifacts:** `UPSKIN_PROJECT_ROOT` must point at a folder containing `artifacts/versions/results_log.csv`. Auto-detection works from the repo root.
- **Backend ↔ Render / Vercel:** see [10_deployment.md](10_deployment.md).
- **No Supabase, no PostgreSQL, no Redis, no S3, no auth provider** to link. Confirmed from code: no client libraries for any of these in `requirements*.txt`.

## Common setup pitfalls
- **Missing artifacts.** Required by [upskin_api/model.py:140-150](../upskin_api/model.py) — message lists exactly which files are absent.
- **scikit-learn version mismatch.** Pickled with 1.8.0, loaded with 1.6.1 in some venvs → `InconsistentVersionWarning`. Not currently treated as failure. [issues.md H8](../issues.md).
- **MC samples too high for local dev.** Default 100 forward passes per request can take 30+ seconds on a cold M1 CPU; set `UPSKIN_MC_SAMPLES=3..10`.
- **Babel-in-browser compile time** can add a couple seconds to first paint locally. There's nothing to "rebuild" — refresh re-compiles. Confirmed from code: [site/index.html:107-115](../site/index.html).
- **CORS errors** if you serve the site on a port other than 5173 or 8080. Either add the origin to `UPSKIN_CORS_ORIGINS` or set it back to one of the defaults. [upskin_api/main.py:18-30](../upskin_api/main.py).
- **`?api=<url>` query override** in the browser silently redirects all traffic to that URL — useful for staging, but be careful sharing links. [issues.md M7](../issues.md).
- **Service is lazy-loaded.** The first request after `uvicorn` boot pays the model-load cost (~1 s locally). If artifacts are missing, the failure surfaces only on that first request. [issues.md M14](../issues.md).
