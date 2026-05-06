# Up Skin Frontend

The Up Skin design system implemented as the production frontend for the FastAPI
recommender backend. Soft beauty-editorial: cream canvas, petal accents, calm motion.

The design tokens, components, and flow come from the Claude Design handoff bundle
(`up-skin-design-system`). All live data — products, demo users, recommendations,
model metrics — comes from the FastAPI backend at runtime. The mock layer ships
only as an offline design preview; production never sees it.

## Run locally

Two processes: the FastAPI backend, and a static file server for `site/`.

### 1. Backend (FastAPI)

```bash
cd /Users/veerr_89/Work/projects/up-skin
source venv/bin/activate
python -m pip install -r requirements-api.txt   # first time only
uvicorn upskin_api.main:app --reload --host 0.0.0.0 --port 8000
```

Verify: <http://localhost:8000/health> should return `{"status": "ok", ...}`.

### 2. Frontend (static)

The site is a static HTML/JSX bundle compiled in the browser via Babel-standalone.
Serve `site/` with any static server, e.g.:

```bash
# from the repo root, in a second terminal
python -m http.server 5173 --directory site
```

Then open <http://localhost:5173/>. The page calls `http://localhost:8000` by default.

### Configuring the API URL

The base URL is resolved in this order (first match wins):

1. `window.__UPSKIN_API_URL` (set in `index.html` or a wrapper script at runtime).
2. `window.__UPSKIN_RUNTIME_CONFIG.apiUrl` from `runtime-config.js`.
3. `process.env.NEXT_PUBLIC_UPSKIN_API_URL` if the site is bundled into a Next/Vite app.
4. `?api=<url>` query string on the page (handy for staging).
5. Default: `http://localhost:8000`.

For Render Static Sites, update `runtime-config.js` after the backend URL exists:

```js
window.__UPSKIN_RUNTIME_CONFIG = {
  apiUrl: "https://<your-backend>.onrender.com"
};
```

### Offline design-preview mode

Pass `?mock=1` on the URL (or set `window.__UPSKIN_USE_MOCK = true` before `api.js`
loads) to use the in-bundle `mockData.js` / `mockExtras.js` layer. The mock returns
plausible-but-fake products, demo users, recommendations, and metrics, so the visual
design can be reviewed without the FastAPI backend running. The mock is **never**
used when the page is loaded normally.

## File map

| File | Role |
|---|---|
| `index.html` | Entrypoint — wires React, Babel, and all scripts. |
| `colors_and_type.css` | Design tokens (color, type, spacing, radii, shadows, motion). |
| `style.css` | Component styles (buttons, chips, cards, layout). Imports tokens. |
| `site.css` | Site-level extensions (sheet, skeletons, states, mobile). Imports `style.css`. |
| `api.js` | Single API client. Real FastAPI by default; opt-in mock via `__UPSKIN_USE_MOCK`. |
| `mockData.js` | Offline-only mock layer (`/health`, `/demo-users`, `/products/search`, `/recommendations/*`). |
| `mockExtras.js` | Offline-only mock layer for `/model/metrics`. |
| `components.jsx` | Buttons, chips, eyebrow, step header, search input, product tile, icons. |
| `Welcome.jsx` | Welcome / onboarding screen. |
| `DemoProfileFlow.jsx` | Anonymized demo profile chooser. |
| `BuildProfileFlow.jsx` | Search → likes → optional filters. |
| `Recommendations.jsx` | Results grid, recommendation cards, interval bars. |
| `Skeletons.jsx` | Shimmer skeletons for loading states. |
| `States.jsx` | `ErrorState` / `EmptyState` panels with motif art. |
| `ModelTransparency.jsx` | Slide-in "How this works" sheet pulling from `/model/metrics`. |
| `site.jsx` | Top-level shell: header, view-stack, footer, model sheet. |
| `assets/wordmark.svg` | Up Skin wordmark. |
| `assets/placeholder-product.svg` | Reserved product photo placeholder. |
| `assets/motifs/*.svg` | Decorative botanicals (petal, drop, branch, bottle). |

## Endpoints consumed

The frontend calls only the documented endpoints. All shapes are described in
`docs/backend_api_contract.md`.

| Endpoint | Used by |
|---|---|
| `GET /health` | header status pip |
| `GET /model/metrics` | `ModelTransparency` sheet |
| `GET /demo-users` | `DemoProfileFlow` |
| `GET /products/search?q=` | `BuildProfileFlow` (search) |
| `GET /recommendations/{author_id}?top_n=` | `DemoProfileFlow` → results |
| `POST /recommendations/custom` | `BuildProfileFlow` → results |

## Hard rules baked into the build

- **No hardcoded products, users, metrics, or recommendations.** Live data only,
  except in the explicit `mockData.js` / `mockExtras.js` design-preview layer.
- **No medical / dermatologist / allergy / acne / condition-treatment claims.**
  Phrasing is "may fit your preferences" and "the model is more / less confident".
- **MF-proxy disclosure is not optional.** When the API returns `uses_mf_proxy: true`,
  the cards and the transparency sheet both surface it.
- **Image slots are reserved.** The API does not yet return `image_url`. Cards and
  tiles use the placeholder SVG; if the API later returns `image_url`, components
  pick it up automatically.
- **`prefers-reduced-motion` is respected** — staggered reveals and shimmer collapse
  to instant.

## Deployment notes

- Host this directory as static files on Vercel (or any static host). Set
  `NEXT_PUBLIC_UPSKIN_API_URL` to the deployed FastAPI URL — or, since this is
  framework-free static HTML, point a wrapper script that sets
  `window.__UPSKIN_API_URL = "https://<your-api-host>"` before `api.js` loads.
- Configure the backend with `UPSKIN_CORS_ORIGINS` so the hosted frontend can
  call it, for example:
  `UPSKIN_CORS_ORIGINS="https://your-frontend.vercel.app"`.
- To deploy the latest Ridge-backed run, set `UPSKIN_MODEL_RUN_ID=v002` on the
  backend. Without this, the API selects the saved run with the lowest BNN RMSE.
- The backend is a Dockerized FastAPI service (Render / Railway recommended in
  `docs/backend_api_contract.md`). Don't put the model on Vercel serverless.
- Don't ship `mockData.js` / `mockExtras.js` to a production host if you want to
  guarantee no fallback path. They're harmless when `__UPSKIN_USE_MOCK` is unset,
  but you can remove the `<script src="./mockData.js">` tags from `index.html`
  before deploying.
