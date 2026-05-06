# Issues Audit

## Project Intent and Artifact Map

Up Skin is a mixed class-demo ML product: a notebook-driven data/modeling pipeline, a FastAPI model-serving API, a static React/Babel frontend prototype, and a Docker packaging path. The project is trying to recommend skincare products from Sephora/Kaggle product and review data while exposing prediction confidence and lightweight explanation text.

The intended user is a demo visitor or class reviewer who can either choose a saved review-history profile or build a new profile by selecting liked products. The operator is a developer/modeler running notebooks, generating local artifacts, serving FastAPI, and hosting the static site separately.

Main workflows:

- Data/model workflow: raw `Datasets/*.csv` -> Ishita matrix notebook -> Viraj transformer notebook -> Viraj MC-dropout BNN notebook -> `artifacts/versions/v001/*`.
- API workflow: `upskin_api.main` exposes health, metrics, demo users, product search, demo recommendations, and custom recommendations.
- Frontend workflow: `site/index.html` loads React UMD, Babel standalone, local JSX files, `site/api.js`, and optional mock data.
- Deployment workflow: Docker copies `upskin_api`, docs, `stale.md`, and local `artifacts/` into an image.

Major source-of-truth files:

- Backend entry points: `upskin_api/main.py`, `upskin_api/recommender.py`, `upskin_api/model.py`, `upskin_api/artifacts.py`, `upskin_api/schemas.py`.
- Frontend entry points: `site/index.html`, `site/site.jsx`, `site/api.js`, `site/BuildProfileFlow.jsx`, `site/DemoProfileFlow.jsx`, `site/Recommendations.jsx`, `site/ModelTransparency.jsx`.
- Modeling notebooks: `ishita/notebooks/Matrix_completion.ipynb`, `viraj/notebooks/transformers.ipynb`, `viraj/notebooks/mc_bnn.ipynb`.
- Stale/experimental notebooks: `ishita/notebooks/Code.ipynb`, `viraj/notebooks/ishita-notebook-runs/Matrix_completion.ipynb`.
- Generated artifacts: local ignored `artifacts/`, especially `artifacts/versions/results_log.csv`, `artifacts/versions/v001/final_pipeline_summary.json`, `artifacts/versions/v001/step5_bnn/*`, `artifacts/versions/v001/step4_features/*`, `artifacts/transformer/*`, and `artifacts/matrix/*`.
- Data: local ignored `Datasets/*.csv`, about 504 MB.
- Docs: tracked `docs/backend_api_contract.md`, `docs/frontend_handoff_prompt.md`, `docs/proposal-STAT-542.pdf`; ignored local `docs/audit_4-28-26.md`.
- Deployment/config: `Dockerfile`, `.dockerignore`, `.gitignore`, `requirements.txt`, `requirements-api.txt`, two empty `package-lock.json` files.
- Tests: `tests/test_upskin_api.py`.

Current/stale/generated signals:

- Current source appears to be the FastAPI package and static frontend.
- Current model artifacts are local, ignored by git, and required by the API.
- `viraj/scripts/build_handoff_artifacts.py` is still documented as reproducible source-of-truth, but current artifact schemas and values do not match its outputs.
- `viraj/viraj.md` and `viraj/notes/01_workflow.md` contain stale matrix/transformer metrics.
- `site/mockData.js` and `site/mockExtras.js` intentionally hardcode fake data, but they are loaded by the production HTML entry point and activated by `?mock=1`.
- `docs/audit_4-28-26.md` contains a prior audit but is ignored by git.

Architectural assumptions driving risk:

- The API assumes local generated artifacts exist and are trustworthy.
- The serving model assumes the API-created feature frame is compatible with the notebook-trained preprocessor and BNN.
- The frontend assumes a live backend by default but keeps a runtime mock and API-base override available.
- The product story assumes personalization, uncertainty, and explanations are meaningful to users, while several serving paths use proxies or heuristics.

## Critical Issues

### C1. Train/serve skew in `mf_score`

- Severity: Critical
- Category: ML correctness / product logic
- Location: `upskin_api/recommender.py:343`, `upskin_api/recommender.py:344`, `upskin_api/recommender.py:351`; `stale.md:5`; `artifacts/versions/v001/step4_features/feature_schema.json:67`; `artifacts/handoff/bayesian_handoff_features.csv:1`
- Issue: The BNN feature named `mf_score` is trained/evaluated as a matrix-factorization score in handoff artifacts, but the live API constructs it as a user/product mean proxy.
- Evidence: `bayesian_handoff_features.csv` includes `mf_score` as a model feature. The API instead computes `global_mean + user offset + product offset` at `recommender.py:344-350`. `stale.md:5-17` explicitly says the full MF candidate scorer was not exported and the API uses a proxy.
- Impact: The served BNN predictions and uncertainty are not generated from the same feature distribution used for the reported `test_bnn_rmse`. This can silently produce wrong rankings while the UI shows model metrics that do not describe the live serving path.
- Suggested direction: Export the trained MF model/candidate scorer and use it at serving time, or retrain/evaluate the BNN on exactly the same proxy feature used by the API.

### C2. API does not enforce the notebook's final skincare exclusion filters

- Severity: Critical
- Category: Product logic / artifact discrepancy
- Location: `upskin_api/recommender.py:82`, `upskin_api/recommender.py:328`, `upskin_api/recommender.py:332`; `artifacts/versions/v001/final_pipeline_summary.json:1`; `artifacts/versions/v001/step6_recommendations/recommendation_metrics.json:32`; `artifacts/versions/v001/step4_features/feature_schema.json:203`; `artifacts/versions/v001/step4_features/feature_schema.json:230`
- Issue: Step 6 records exclusions for `High Tech Tools`, `Wellness`, `Hair Removal`, `Facial Cleansing Brushes`, `Facial Rollers`, `Holistic Wellness`, and `Teeth Whitening`, but the API reads `filter_report` from `final_pipeline_summary.json`, where that key is absent.
- Evidence: `recommender.py:82` sets `self.filter_report = self.bundle.best_run.summary.get("filter_report", {})`; `final_pipeline_summary.json` has no `filter_report`; `recommendation_metrics.json:32-50` contains the actual exclusion report. A read-only service check found 73 `High Tech Tools`, 74 `Wellness`, and all listed excluded tertiary categories still present in live candidate features for a demo profile.
- Impact: The API can recommend out-of-scope products that the notebook's final recommendation artifact explicitly removed, undermining the "skincare" product boundary and user trust.
- Suggested direction: Make the API read the Step 6 `recommendation_metrics.json` filter report, or copy the filter policy into the selected run summary during artifact export.

## High Issues

### H1. Documented reproducible pipeline is not the pipeline that produced current artifacts

- Severity: High
- Category: Project intent and artifact discrepancies
- Location: `viraj/notes/01_workflow.md:13`; `ishita/ishita.md:16`; `viraj/scripts/build_handoff_artifacts.py:250`; `viraj/scripts/build_handoff_artifacts.py:628`; `artifacts/matrix/split_sanity.json:2`
- Issue: Docs say the reproducible handoff comes from `viraj/scripts/build_handoff_artifacts.py`, but current artifacts have shapes/schemas matching notebook outputs instead.
- Evidence: The script's `make_split` is iterative and writes a `split_sanity.json` with keys like `no_missing_train_indices` at `build_handoff_artifacts.py:628-634`; the current artifact has `train_rows`, `test_rows`, `train_users`, and `min_train_ratings_per_user` at `artifacts/matrix/split_sanity.json:2-8`. Docs still instruct users to run the script.
- Impact: A collaborator following docs may overwrite current artifacts with a different split and invalidate the trained `v001` model/preprocessor contract.
- Suggested direction: Choose one canonical runner. Either retire the script and document notebook execution, or port the notebook behavior into the script and regenerate the model artifacts.

### H2. Workflow docs report stale matrix and transformer metrics as "current"

- Severity: High
- Category: Documentation / artifact discrepancy
- Location: `viraj/viraj.md:60`; `viraj/notes/01_workflow.md:39`; `artifacts/matrix/split_sanity.json:2`; `artifacts/matrix/metrics.json:10`; `artifacts/handoff/hybrid_metrics.json:15`
- Issue: The docs' "current run" values do not match local artifacts.
- Evidence: Docs report `train_df: (155597, 3)`, `test_df: (8448, 3)`, MF RMSE `0.8174`, and MF Hit Rate@10 `0.0149`. Artifacts show train rows `126691`, test rows `7017`, MF RMSE `0.7931829352149041`, and MF Hit Rate@10 `0.010118284167022944`.
- Impact: Reproducibility checks become misleading; reviewers may think their run is broken when it matches the artifacts but not the docs.
- Suggested direction: Mark those docs stale or regenerate them from the current artifact files.

### H3. Matrix holdout and active-user guarantees are broken in current artifacts

- Severity: High
- Category: Modeling correctness / evaluation validity
- Location: `ishita/notebooks/Matrix_completion.ipynb:1158`; `ishita/notebooks/Matrix_completion.ipynb:1258`; `artifacts/matrix/split_sanity.json:2`; `artifacts/matrix/split_sanity.json:8`
- Issue: The intended one-holdout-per-user and `MIN_USER_RATINGS = 10` story does not hold in the generated data.
- Evidence: `split_sanity.json` reports `test_rows: 7017` and `test_users: 6797`, so 220 extra holdout rows exist beyond one per user. It also reports `min_train_ratings_per_user: 5` despite `MIN_USER_RATINGS = 10`. A read-only CSV check found 1,222 train users with fewer than 10 ratings.
- Impact: Ranking metrics and user-history features are evaluated on a population that violates the stated split design.
- Suggested direction: Rebuild the split with verified one-row-per-user sampling and iterative filtering, then regenerate downstream artifacts.

### H4. Recommendations show weak personalization across demo users

- Severity: High
- Category: Product logic / ML validity
- Location: `artifacts/versions/v001/step6_recommendations/top10_recommendations.csv:1`; `artifacts/versions/v001/step6_recommendations/sample_user_reports.md:7`; `artifacts/versions/v001/step6_recommendations/sample_user_reports.md:59`; `artifacts/versions/v001/step6_recommendations/sample_user_reports.md:111`
- Issue: The sample top-10 recommendations are heavily repeated across users.
- Evidence: A read-only check of `top10_recommendations.csv` found 50 recommendation rows across 5 users but only 28 unique products. `Wake Up Honey Eye Cream` and `Truth Barrier Booster` appear in all 5 users' top-10 lists.
- Impact: The UX promises personalized recommendations, but the served rankings look dominated by globally strong products and user mean-rating shifts.
- Suggested direction: Add a user-specific collaborative signal at serving time, such as exported MF user/item vectors or a validated nearest-user/profile method.

### H5. Custom cold-start profiles turn liked product averages into user harshness

- Severity: High
- Category: Product logic / ML validity
- Location: `upskin_api/recommender.py:223`; `upskin_api/recommender.py:237`; `upskin_api/recommender.py:239`
- Issue: For a new visitor, the API infers `mean_user_rating` from the average ratings of liked products, not from the visitor's actual rating behavior.
- Evidence: `recommend_for_custom` builds `source_stats` from `product_rating_mean` or catalog `avg_product_rating`, then sets `mean_user_rating` and `mean_train_rating` to that inferred mean.
- Impact: A user who selects popular/highly rated products is treated like a high-rating historical user, increasing predicted scores and popularity bias rather than learning individual taste.
- Suggested direction: For custom users, separate product affinity from user harshness; blend unknown user mean toward the global mean or use a content-only cold-start ranker that is labeled as such.

### H6. Public recommendation endpoints have no rate limits or request-size bounds

- Severity: High
- Category: Security / abuse resistance / performance
- Location: `upskin_api/main.py:57`; `upskin_api/main.py:70`; `upskin_api/schemas.py:13`; `upskin_api/model.py:93`
- Issue: The most expensive endpoints are unauthenticated and lack rate limiting, body-size limits, and list-length bounds.
- Evidence: `/recommendations/{author_id}` and `/recommendations/custom` are public. `CustomRecommendationRequest.liked_product_ids` only has `min_length=1`, and filter lists have no maximum length. `predict_mc` loops over MC samples and batches for each request.
- Impact: A client can repeatedly trigger model inference and feature-frame construction, causing avoidable CPU pressure or denial of service on a small hosted backend.
- Suggested direction: Add API-layer rate limiting, request body size limits, maximum list lengths, and operational monitoring for recommendation calls.

### H7. "Optional filters" silently apply a default max-price filter

- Severity: High
- Category: UX / correctness
- Location: `site/BuildProfileFlow.jsx:13`; `site/BuildProfileFlow.jsx:111`; `site/BuildProfileFlow.jsx:54`; `site/BuildProfileFlow.jsx:58`
- Issue: The custom profile flow says filters are optional and "we'll keep it open," but it initializes `maxPrice` to 75 and always sends `filters.max_price_usd`.
- Evidence: `maxPrice` starts at `75`; `submit()` always includes `max_price_usd: maxPrice`.
- Impact: Users who do not intend to filter price still exclude products above $75, making recommendations narrower than the UI promise.
- Suggested direction: Represent an unset price filter as `null`, or add an explicit enable/disable control for max price.

### H8. Local runtime loads model artifacts with a mismatched scikit-learn version

- Severity: High
- Category: Deployment / ML serving reliability
- Location: `requirements.txt:115`; `requirements-api.txt:6`; `artifacts/versions/v001/step5_bnn/preprocessor.joblib`; `artifacts/versions/v001/step4_features/embedding_pca.joblib`
- Issue: The local `venv` has scikit-learn `1.6.1`, while the artifacts were pickled from scikit-learn `1.8.0`; requirements files also disagree.
- Evidence: Running the existing tests through `venv/bin/python` passed but emitted `InconsistentVersionWarning` for `SimpleImputer`, `StandardScaler`, `Pipeline`, `OneHotEncoder`, `ColumnTransformer`, and `PCA` loaded from version `1.8.0` under runtime `1.6.1`. `requirements.txt` pins `1.6.1`; `requirements-api.txt` pins `1.8.0`.
- Impact: Local tests may pass while serving different transformed features than the artifact author intended, and warnings are not treated as failures.
- Suggested direction: Pin training, API, Docker, and local venv instructions to the artifact-producing scikit-learn version, and fail tests on `InconsistentVersionWarning`.

### H9. Required runtime artifacts are ignored by git but copied by Docker

- Severity: High
- Category: Deployment / reproducibility
- Location: `.gitignore:6`; `Dockerfile:16`; `docs/backend_api_contract.md:138`
- Issue: `artifacts/` is ignored by git, yet `Dockerfile` requires `COPY artifacts /app/artifacts`.
- Evidence: `.gitignore` ignores `artifacts/`; Docker build expects a local artifact directory; the backend contract says artifacts must be attached at build/runtime.
- Impact: A clean clone or CI build cannot produce a working image without out-of-band local state.
- Suggested direction: Publish versioned model artifacts through a release/storage mechanism with checksums, or use Git LFS/explicit artifact download during build.

### H10. Model and preprocessing artifacts are loaded without integrity checks

- Severity: High
- Category: Security / supply chain
- Location: `upskin_api/model.py:149`; `upskin_api/model.py:165`; `upskin_api/model.py:166`; `upskin_api/recommender.py:95`; `docs/backend_api_contract.md:138`
- Issue: The backend loads PyTorch, joblib, and NPZ artifacts from disk with no hash, signature, or trusted-source verification.
- Evidence: `torch.load`, `joblib.load`, and `np.load(..., allow_pickle=True)` are used for runtime artifacts. Deployment docs suggest attaching artifacts at build/runtime.
- Impact: If a model/preprocessor artifact is replaced or sourced from an untrusted bucket, the backend may execute unsafe deserialization or silently serve tampered predictions.
- Suggested direction: Store expected hashes with each model version, verify them before loading, avoid `allow_pickle=True` unless necessary, and only load artifacts from a trusted immutable source.

### H11. The "production frontend" uses browser Babel, React development builds, and third-party scripts without SRI/CSP

- Severity: High
- Category: Security / performance / deployment
- Location: `site/index.html:40`; `site/index.html:41`; `site/index.html:43`; `site/README.md:3`
- Issue: The frontend is described as production, but it compiles JSX in the browser and loads React development UMD plus Babel standalone from `unpkg.com` without subresource integrity or a CSP.
- Evidence: `index.html` loads `react.development.js`, `react-dom.development.js`, and `@babel/standalone`, then loads local JSX with `type="text/babel"`.
- Impact: First load is slower and depends on external CDN availability. The lack of SRI/CSP increases supply-chain and script-injection risk.
- Suggested direction: Bundle the site with a build step, serve production React, add integrity/CSP headers, or clearly reframe the site as a prototype-only runtime.

### H12. Tests are contract-smoke tests only and do not guard model behavior

- Severity: High
- Category: Testing / maintainability
- Location: `tests/test_upskin_api.py:16`; `tests/test_upskin_api.py:25`; `tests/test_upskin_api.py:53`; `tests/test_upskin_api.py:71`
- Issue: The test suite verifies that endpoints return shapes and exclude already-seen demo products, but it does not validate model parity, filter enforcement, warning-free artifact loading, or stable recommendation outputs.
- Evidence: Existing assertions check `status`, `run_id`, response keys, score range, count, and seen-product exclusion. No test covers Step 6 exclusion filters, golden recommendation IDs, scikit-learn warnings, deterministic predictions, or serving-vs-notebook feature parity.
- Impact: Major regressions in recommendation logic can pass tests as long as the API shape remains intact.
- Suggested direction: Add golden tests for known demo users, filter policy tests, warning-as-error artifact loading, and a small feature-parity fixture from notebook outputs.

## Medium Issues

### M1. Public model-quality claims are stronger than the evidence supports

- Severity: Medium
- Category: ML validity / UX trust
- Location: `artifacts/versions/results_log.csv:1`; `artifacts/versions/v001/step5_bnn/all_metrics.json:72`; `site/ModelTransparency.jsx:91`; `site/Recommendations.jsx:157`
- Issue: The UI and artifacts present `BNN beats MF` and `best RMSE 0.7636` without confidence intervals, statistical tests, or product-ranking baselines.
- Evidence: `all_metrics.json` reports BNN RMSE `0.7636` vs MF RMSE `0.7786` on 1,046 test rows; the UI renders binary "BNN beats MF" copy and result-stamp RMSE.
- Impact: Users and reviewers may overtrust a small rating-RMSE delta that may not translate to live ranking quality, especially with the train/serve skew in C1.
- Suggested direction: Label metrics by split and row count, add bootstrap confidence intervals, and include ranking baselines such as popularity and product average rating.

### M2. Calibrated 95 percent intervals are too wide to be useful as precision signals

- Severity: Medium
- Category: ML uncertainty / UX trust
- Location: `artifacts/versions/v001/step5_bnn/all_metrics.json:79`; `artifacts/versions/v001/step5_bnn/all_metrics.json:226`; `site/Recommendations.jsx:12`
- Issue: The model uses an uncertainty interval multiplier of `15.702887231072898`, producing mean calibrated interval widths around 1.8 points on a 1-5 scale.
- Evidence: `all_metrics.json` shows validation mean calibrated width `1.8710` and test mean calibrated width `1.8353`. The UI renders these as precise interval bars.
- Impact: Wide intervals can imply scientific confidence while often saying little beyond "somewhere in a large part of the rating scale."
- Suggested direction: Surface interval width honestly, add copy for degenerate/wide intervals, and consider uncertainty methods calibrated for useful ranking decisions.

### M3. Transformer cosine similarity is mapped to ratings with an arbitrary formula

- Severity: Medium
- Category: ML validity
- Location: `viraj/scripts/build_handoff_artifacts.py:452`; `upskin_api/recommender.py:341`; `artifacts/handoff/hybrid_metrics.json:15`
- Issue: `content_rating_score = 1 + 4 * clipped(content_score)` is not learned or calibrated.
- Evidence: The script and API both map cosine scores directly onto the rating scale. `hybrid_metrics.json` reports content-only RMSE/MAE as if this mapping were a calibrated rating model.
- Impact: Content-vs-MF metric comparisons and hybrid feature values are partly artifacts of an arbitrary scale transform.
- Suggested direction: Learn a calibration layer from validation data or treat content similarity as a ranking/feature signal rather than a direct rating predictor.

### M4. Hybrid alpha is a fixed serving rule, not a validated model parameter

- Severity: Medium
- Category: ML validity / maintainability
- Location: `artifacts/run_config.json:4`; `upskin_api/recommender.py:69`; `viraj/scripts/build_handoff_artifacts.py:50`
- Issue: `hybrid_alpha` is hardcoded to `0.7` and used at serving time, but there is no current artifact proving this value is optimal for the deployed objective.
- Evidence: `run_config.json` pins `hybrid_alpha: 0.7`; `recommender.py` uses it for `hybrid_score`.
- Impact: The BNN and rankings inherit an untuned convex-combination choice.
- Suggested direction: Tune alpha on validation ranking metrics or mark it clearly as a heuristic serving parameter.

### M5. Explanations are heuristic keyword/content text, not model attribution

- Severity: Medium
- Category: UX trust / ML explainability
- Location: `upskin_api/recommender.py:395`; `upskin_api/recommender.py:409`; `stale.md:37`; `docs/proposal-STAT-542.pdf`
- Issue: Recommendation explanations sound model-derived but are generated from product text similarity and ingredient keyword matches.
- Evidence: `_explain` and `_ingredient_signals` use category strings, product text similarity phrasing, and hardcoded ingredient term groups. `stale.md` acknowledges this is not SHAP, attention attribution, or learned explanation.
- Impact: Users may interpret explanations as causal reasons for the BNN score when they are metadata highlights.
- Suggested direction: Rename this to "ingredient/content highlights" or add real attribution and validate explanation quality.

### M6. Demo profiles are called anonymized while raw `author_id` is returned and displayed

- Severity: Medium
- Category: Privacy / UX honesty
- Location: `upskin_api/recommender.py:157`; `site/DemoProfileFlow.jsx:45`; `site/DemoProfileFlow.jsx:86`; `docs/frontend_handoff_prompt.md:143`
- Issue: The demo flow claims each profile is anonymized, but the API returns raw author IDs and the UI displays them.
- Evidence: `DemoProfileFlow` says "Each profile is anonymized" and then renders `{u.author_id}`. The API returns `author_id` directly.
- Impact: Public review IDs are tied to skincare preferences in the demo despite the anonymization claim.
- Suggested direction: Display local aliases only, and keep real IDs internal or hashed.

### M7. Query-string API override can redirect user preference traffic to arbitrary origins

- Severity: Medium
- Category: Security / privacy
- Location: `site/index.html:27`; `site/index.html:30`; `site/api.js:13`; `site/api.js:31`
- Issue: `?api=<url>` sets `window.__UPSKIN_API_URL`, and all frontend requests then go to that origin.
- Evidence: `index.html` copies the query param into `__UPSKIN_API_URL`; `api.js` uses it as `RUNTIME_BASE` for `fetch`.
- Impact: A shared link to the trusted frontend can make a visitor send liked product IDs and profile actions to an attacker-controlled CORS-enabled API.
- Suggested direction: Restrict runtime API overrides to known hosts in production, or disable query-string override outside local/staging builds.

### M8. Mock data is shipped and activatable in the production HTML path

- Severity: Medium
- Category: Project artifact discrepancy / UX trust
- Location: `site/README.md:8`; `site/README.md:118`; `site/index.html:33`; `site/index.html:45`; `site/mockData.js:5`; `site/mockExtras.js:3`
- Issue: The README says production uses live data and the mock is offline-only, but `index.html` always loads mock scripts and activates them with `?mock=1`.
- Evidence: `index.html` loads `mockData.js` and `mockExtras.js`; `mockExtras.js` hardcodes `v001` metrics; a read-only catalog check found 6 of the 10 mock product IDs absent from the real product catalog.
- Impact: A production-hosted page can show fake products/metrics, and mock data can drift from real API contracts.
- Suggested direction: Keep mock scripts out of production deploys or gate them behind a build-time environment flag.

### M9. Recommendation cards do not show prices even though users can filter by price

- Severity: Medium
- Category: UX / product logic
- Location: `site/BuildProfileFlow.jsx:120`; `site/Recommendations.jsx:76`; `upskin_api/schemas.py:35`; `upskin_api/recommender.py:377`
- Issue: The custom flow lets users set max price, and `Recommendations.jsx` can render `rec.price_usd`, but the backend recommendation schema/payload never include `price_usd`.
- Evidence: `RecommendationItem` lacks price fields; `_recommendation_payload` returns score, uncertainty, category, and explanation only.
- Impact: Users cannot verify that price filters were applied or compare recommendations by price.
- Suggested direction: Include price and key product metadata in recommendation responses, or remove the price metric condition from the card until supported.

### M10. Category filter chips are not keyboard-accessible controls

- Severity: Medium
- Category: Accessibility / UX
- Location: `site/components.jsx:53`; `site/components.jsx:55`; `site/BuildProfileFlow.jsx:153`
- Issue: Clickable category chips are rendered as `<span onClick>` rather than buttons or checkbox controls.
- Evidence: `Chip` returns a `span` when `onClick` is passed, and category filters use `Chip` with `onClick`.
- Impact: Keyboard and assistive-technology users may not be able to operate category filters reliably.
- Suggested direction: Render clickable chips as `<button>` with `aria-pressed`, or use checkbox inputs styled as chips.

### M11. Empty recommendation results do not explain the failure reason

- Severity: Medium
- Category: UX / error handling
- Location: `upskin_api/recommender.py:283`; `upskin_api/recommender.py:304`; `site/site.jsx:74`
- Issue: If filters remove all candidates, the API returns an empty list with no structured reason and the UI shows generic "No recommendations came back."
- Evidence: `_recommend` sets `recommendations = []` when candidates are empty and returns the same response shape. The UI advises removing filters but cannot identify which filter caused the empty set.
- Impact: Users may keep retrying without knowing whether price, category, stock, or invalid liked products caused the issue.
- Suggested direction: Return a structured empty-state reason and counts after each filter.

### M12. Public metrics leak local filesystem paths

- Severity: Medium
- Category: Security / privacy / artifact hygiene
- Location: `upskin_api/recommender.py:146`; `artifacts/versions/v001/final_pipeline_summary.json:34`; `artifacts/versions/v001/final_pipeline_summary.json:37`
- Issue: Public metrics and saved summaries include absolute local paths.
- Evidence: `/model/metrics` includes `stale_notes_file` from `self.project_root`; `final_pipeline_summary.json` stores `/Users/veerr_89/Work/projects/up-skin/...` artifact paths.
- Impact: Hosted responses or shared artifacts can reveal local usernames and machine paths, and the paths are stale outside the original workstation.
- Suggested direction: Return relative artifact identifiers or URLs, not local absolute paths.

### M13. No environment example or deployment manifest defines required runtime variables

- Severity: Medium
- Category: Deployment / operations
- Location: `docs/backend_api_contract.md:14`; `docs/backend_api_contract.md:21`; `site/README.md:109`; repository root
- Issue: The project relies on `UPSKIN_CORS_ORIGINS`, `UPSKIN_MC_SAMPLES`, `UPSKIN_PROJECT_ROOT`, and a frontend API URL, but no `.env.example`, `render.yaml`, `vercel.json`, or CI deployment config exists.
- Evidence: Docs describe env vars and hosting, but repository search found no env example and no deploy manifests beyond `Dockerfile`.
- Impact: Operators must infer production config manually, increasing CORS, artifact, and frontend/backend URL drift.
- Suggested direction: Add an environment contract file and deployment manifests for the intended static host and backend host.

### M14. The API does not load artifacts at process startup despite docs saying it fails fast

- Severity: Medium
- Category: Deployment / operations
- Location: `docs/backend_api_contract.md:138`; `upskin_api/main.py:34`; `upskin_api/recommender.py:427`
- Issue: The app object can import and Uvicorn can start before artifacts are loaded; loading happens on first route call through `get_service()`.
- Evidence: Routes call `get_service()` at request time, and `get_service` is lazily cached with `lru_cache`.
- Impact: A deployment can appear started while model/artifact failures surface only on the first health or recommendation request.
- Suggested direction: Add a startup readiness check that constructs the service and fails the process if required artifacts cannot load.

### M15. Generated feature artifacts include evaluation columns and raw ID lists

- Severity: Medium
- Category: Data / ML leakage risk
- Location: `artifacts/handoff/bayesian_handoff_features.csv:1`; `artifacts/versions/v001/step4_features/model_features.csv:1`; `artifacts/versions/v001/step4_features/feature_schema.json:66`
- Issue: Files named as model feature handoffs include `mf_abs_error`, `content_abs_error`, `rated_product_ids`, and `liked_product_ids`, even though the feature schema excludes them.
- Evidence: CSV headers include evaluation error columns and pipe-separated product ID lists; `feature_schema.json` lists the actual model columns separately.
- Impact: Future notebooks or scripts could accidentally include target-derived error columns or raw profile lists as features.
- Suggested direction: Save clean model-input tables separately from diagnostic/evaluation tables.

### M16. MC-dropout predictions are stochastic with no request-level seed

- Severity: Medium
- Category: Correctness / reproducibility
- Location: `upskin_api/model.py:93`; `upskin_api/model.py:95`; `upskin_api/model.py:111`
- Issue: The model switches to train mode for dropout sampling and runs random MC passes without setting a deterministic seed.
- Evidence: `predict_mc` calls `self.model.train()` and loops over `mc_samples`, then returns sample means/intervals.
- Impact: The same profile can receive slightly different scores, intervals, and confidence buckets across requests, complicating debugging and demos.
- Suggested direction: Seed per request/profile for reproducible demos, or document stochasticity and expose a request seed in diagnostics.

### M17. Health, metrics, and demo-user endpoints lack response models

- Severity: Medium
- Category: API maintainability / contract stability
- Location: `upskin_api/main.py:34`; `upskin_api/main.py:39`; `upskin_api/main.py:44`; `docs/backend_api_contract.md:49`
- Issue: Several documented contract endpoints return raw `dict`/`list[dict]` without Pydantic response models.
- Evidence: Only product search and recommendation endpoints declare `response_model`; docs specify health, metrics, and demo-user shapes.
- Impact: Contract drift can reach the frontend without schema validation or tests catching field changes.
- Suggested direction: Add Pydantic response models for all documented endpoints.

## Low Issues

### L1. Empty package-lock files imply a Node project that does not exist

- Severity: Low
- Category: Stale config / maintainability
- Location: `package-lock.json:1`; `site/package-lock.json:1`; repository root
- Issue: Two `package-lock.json` files exist with empty `packages` objects, but there is no `package.json`.
- Evidence: Both lockfiles contain only `name`, `lockfileVersion`, `requires`, and `{}` packages.
- Impact: Developers may expect npm scripts/builds that do not exist.
- Suggested direction: Remove empty lockfiles or scaffold a real frontend package/build if the site should be productionized.

### L2. Duplicate and deprecated notebooks remain beside the canonical notebook flow

- Severity: Low
- Category: Stale / dead code
- Location: `ishita/notebooks/Code.ipynb:20`; `ishita/notebooks/Code.ipynb:2529`; `viraj/notebooks/ishita-notebook-runs/Matrix_completion.ipynb:258`; `.gitignore:8`
- Issue: An older SVD/random-split notebook and a duplicate Matrix Completion notebook remain in the repo.
- Evidence: `Code.ipynb` imports `train_test_split` and uses random row splitting. `viraj/notebooks/ishita-notebook-runs/Matrix_completion.ipynb` is ignored by `.gitignore` but is still present locally and uses a different relative dataset path.
- Impact: Reviewers can run the wrong notebook and produce incompatible artifacts.
- Suggested direction: Archive deprecated notebooks with clear top-cell warnings or remove duplicates from the working tree.

### L3. Ignored prior audit contains useful findings that collaborators will not see

- Severity: Low
- Category: Documentation / stale artifacts
- Location: `.gitignore:9`; `docs/audit_4-28-26.md:1`
- Issue: `docs/audit_4-28-26.md` exists locally and contains a prior audit, but `docs/` is ignored, and the file is not tracked.
- Evidence: `git status --ignored` reports `!! docs/audit_4-28-26.md`; `.gitignore` ignores `docs/`.
- Impact: Important audit context can disappear across clones and branches.
- Suggested direction: Keep audits in a tracked location or explicitly mark local audits as disposable.

### L4. Cached service prevents artifact reload without process restart

- Severity: Low
- Category: Operations / maintainability
- Location: `upskin_api/recommender.py:427`
- Issue: `get_service()` is cached forever within the process.
- Evidence: `@lru_cache(maxsize=1)` wraps service construction.
- Impact: Updated artifacts or env changes do not take effect until the process restarts, which is easy to miss during demos.
- Suggested direction: Document restart requirements or add an operator-only reload path.

### L5. Candidate embedding lookup depends on DataFrame index alignment

- Severity: Low
- Category: Maintainability / latent correctness
- Location: `upskin_api/recommender.py:91`; `upskin_api/recommender.py:339`
- Issue: The API uses `df.index.to_numpy()` to select rows from `product_embeddings`.
- Evidence: The catalog is reset to match embedding order at load time, and filters currently preserve original indices before lookup.
- Impact: A future `reset_index(drop=True)` in the filtering path would silently score candidates with the wrong embeddings.
- Suggested direction: Join embeddings by `product_id` instead of relying on DataFrame index labels.

### L6. Empty product search defaults to popularity and can bias profile creation

- Severity: Low
- Category: UX / recommendation quality
- Location: `upskin_api/recommender.py:167`; `upskin_api/recommender.py:181`; `site/BuildProfileFlow.jsx:17`
- Issue: The custom flow starts with an empty query, and the API returns products sorted by `loves_count` then average rating.
- Evidence: `search_products` sorts by popularity on empty query; `BuildProfileFlow` immediately calls search with an empty initial `query`.
- Impact: New users are nudged to select popular products, reinforcing popularity bias in custom recommendations.
- Suggested direction: Use a diversified/category-balanced starter set or require an explicit search before showing products.

### L7. Mock recommendation route ignores requested `top_n` for demo users

- Severity: Low
- Category: Mock/data contract drift
- Location: `site/api.js:74`; `site/api.js:76`; `site/mockData.js:84`
- Issue: The real API client encodes `top_n`, but the mock route always calls `recommendForUser(id, 10)`.
- Evidence: `mockRoute` discards the query param and passes `10`.
- Impact: Design-preview behavior can disagree with live API behavior when testing 5 or 20 recommendations.
- Suggested direction: Parse `top_n` in mock routing or route through the same API-client parameter handling.

### L8. Docker image has no non-root user or healthcheck

- Severity: Low
- Category: Deployment / security hardening
- Location: `Dockerfile:1`; `Dockerfile:20`
- Issue: The Dockerfile uses the base image default user and defines no container healthcheck.
- Evidence: There is no `USER` or `HEALTHCHECK` instruction.
- Impact: This is a hardening and observability gap for a hosted public API.
- Suggested direction: Run as a non-root user and add a healthcheck that calls `/health` after startup service loading is fixed.

### L9. Local workspace contains very large ignored runtime state

- Severity: Low
- Category: Performance / repository hygiene
- Location: `.gitignore:1`; `.gitignore:3`; `.gitignore:6`; `.dockerignore:1`; `.dockerignore:5`
- Issue: The local workspace includes ignored `venv/`, `Datasets/`, and `artifacts/` directories totaling roughly 2.0 GB.
- Evidence: Read-only size check showed `venv` about 1.5 GB, `Datasets` about 504 MB, and `artifacts` about 47 MB.
- Impact: Local searches and accidental Docker contexts can become slow or misleading if tools do not honor ignore rules.
- Suggested direction: Keep large runtime state outside the repo root or document it as local-only workspace data.

### L10. Product catalog artifact carries notebook scratch columns

- Severity: Low
- Category: Generated artifact hygiene
- Location: `artifacts/transformer/product_catalog.csv:1`; `viraj/scripts/build_handoff_artifacts.py:373`
- Issue: The API catalog includes `product_text`, `product_text_length`, `transformer_text`, and `transformer_text_length`, while the script version would drop `product_text`.
- Evidence: The CSV header includes scratch text columns. The script's save path drops `product_text` before writing the catalog.
- Impact: Artifact bloat and confusion about which text field is canonical.
- Suggested direction: Export a clean serving catalog and keep diagnostic text in a separate artifact.

## Project Logic and Correctness

Findings in this pass: C1, C2, H3, H4, H5, H7, M3, M4, M11, M16, L5, L6.

The highest-risk correctness issues are the `mf_score` train/serve skew, the missing final exclusion filters in API serving, and custom-profile logic that converts selected product averages into user-rating behavior.

## Security and Privacy

Findings in this pass: H6, H10, H11, M6, M7, M12, L8.

No secrets, private keys, service-role tokens, or committed `.env` files were found. The concrete security risks are instead artifact deserialization trust, public expensive endpoints, unguarded API-base override, raw author ID exposure, path leakage, CDN/script hardening, and Docker hardening gaps.

## UX and App Behavior

Findings in this pass: H7, H11, M1, M2, M5, M6, M8, M9, M10, M11, L6, L7.

The biggest UX trust gaps are: "optional" filters applying by default, model metrics displayed as stronger evidence than they are, heuristic explanations presented near model confidence, and production HTML retaining a mock mode.

## Performance and Efficiency

Findings in this pass: H6, H11, L9.

Measured local service construction was about 1.1 seconds and a default 100-sample demo recommendation call was about 0.28 seconds on this machine, so no local latency blocker was proven. The performance risks are mainly public abuse, runtime browser compilation, CDN dependency, and large ignored local state.

## Stale, Dead, or Debug Code

Findings in this pass: H1, H2, M8, L1, L2, L3, L7, L10.

The stale-code pattern is not just cleanup: stale notebooks/docs and the non-canonical build script can regenerate incompatible artifacts.

## Maintainability and Testing

Findings in this pass: H1, H8, H12, M13, M15, M17, L1, L2, L4, L5, L10.

Tests passed only when run through `venv/bin/python`; the default `pytest` on this machine used Python 3.14 and failed collection because FastAPI was not installed. The passing venv run still emitted scikit-learn artifact version warnings.

## Deployment and Operational Risks

Findings in this pass: H8, H9, H10, H11, M13, M14, L4, L8, L9.

No CI, no Vercel/static-host config, no `.env.example`, and no backend hosting manifest were found. Docker packaging depends on ignored local artifacts.

## Data, Notebook, and ML Issues

Findings in this pass: C1, C2, H1, H2, H3, H4, H5, H8, M1, M2, M3, M4, M5, M15, M16, L2, L10.

The main ML validity risks are train/serve skew, weak personalization, fragile evaluation claims, stale docs, and multiple generated artifact families that disagree about the canonical run.

## Open Questions Needing Human Confirmation

1. Was `viraj/scripts/build_handoff_artifacts.py` intended to be the canonical reproducible runner, or is it now obsolete?
2. Should the Step 6 exclusion policy be a production policy for all API recommendations?
3. Is the product priority rating prediction (`RMSE/MAE`) or top-N ranking quality (`Hit Rate`, NDCG, precision@K)?
4. Should demo `author_id` values be treated as sensitive enough to hide/hash?
5. Was `v001` intentionally produced under scikit-learn `1.8.0`, and should the local venv be rebuilt to match it?
6. Are mock files intended to be deployed, or should they be stripped from any public host?
7. What artifact distribution mechanism should a clean CI/Docker build use?
8. Is stochastic MC-dropout variability acceptable in demos, or should recommendations be deterministic per profile?

## Audit Coverage Notes

Inspected:

- Repository layout, tracked files, ignored files, and recent git state.
- Backend API, schemas, artifact resolver, recommendation service, and model loader.
- Static frontend entry point, API client, main flows, recommendation cards, model sheet, mocks, and CSS.
- Dockerfile, `.dockerignore`, `.gitignore`, Python requirements, lockfiles, docs, prior ignored audit, and proposal PDF text.
- Main notebooks via targeted search for split logic, path assumptions, MC-dropout, and filter policy.
- Local generated artifacts under `artifacts/`, including matrix metrics, handoff metrics, feature schemas, BNN metrics, summary JSON, and Step 6 recommendation outputs.
- Existing tests with cache and bytecode disabled.

Read-only checks performed:

- `pytest` with system Python failed collection due missing FastAPI.
- `venv/bin/python -m pytest` passed 4 tests but emitted 6 scikit-learn version warnings.
- CSV/JSON checks confirmed current shapes, stale docs, split anomalies, missing API filter report, catalog absence of image URLs, missing mock IDs, repeated top recommendations, and feature-file leakage columns.

Not covered:

- Full notebook re-execution.
- Docker image build.
- Browser visual/responsive verification.
- Live hosted deployment behavior.
- External dependency CVE audit.
