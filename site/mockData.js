// MOCK-ONLY data so the prototype runs as a static HTML file when no backend is available.
// In production, every call goes through the FastAPI backend (see api.js).
// Enable by setting `window.__UPSKIN_USE_MOCK = true` in index.html *before* loading api.js.

const PRODUCTS = [
  { product_id: "P503879", product_name: "Wake Up Honey Eye Cream with Brightening Vitamin C", brand_name: "Farmacy", category: "Eye Care / Eye Creams & Treatments", price_usd: 48, avg_product_rating: 4.51, loves_count: 312044 },
  { product_id: "P434548", product_name: "Honeymoon Glow AHA Resurfacing Night Serum", brand_name: "Farmacy", category: "Moisturizers / Night Creams", price_usd: 60, avg_product_rating: 4.31, loves_count: 177152 },
  { product_id: "P411924", product_name: "Confidence in a Cream Hydrating Moisturizer", brand_name: "IT Cosmetics", category: "Moisturizers / Face Creams", price_usd: 54, avg_product_rating: 4.37, loves_count: 254021 },
  { product_id: "P447212", product_name: "C-Firma Fresh Day Serum", brand_name: "Drunk Elephant", category: "Treatments / Face Serums", price_usd: 80, avg_product_rating: 4.22, loves_count: 414890 },
  { product_id: "P404338", product_name: "Watermelon Glow Niacinamide Dew Drops", brand_name: "Glow Recipe", category: "Treatments / Face Serums", price_usd: 35, avg_product_rating: 4.45, loves_count: 168290 },
  { product_id: "P471123", product_name: "Lala Retro Whipped Refillable Moisturizer", brand_name: "Drunk Elephant", category: "Moisturizers / Face Creams", price_usd: 64, avg_product_rating: 4.33, loves_count: 141004 },
  { product_id: "P480901", product_name: "Gentle Hydra-Gel Face Cleanser", brand_name: "Tatcha", category: "Cleansers / Face Wash & Cleansers", price_usd: 42, avg_product_rating: 4.41, loves_count: 92110 },
  { product_id: "P492234", product_name: "Rose Deep Hydration Toner", brand_name: "Fresh", category: "Treatments / Toners", price_usd: 45, avg_product_rating: 4.28, loves_count: 81050 },
  { product_id: "P509871", product_name: "Cloudberry Brightening Sleep Mask", brand_name: "Glow Recipe", category: "Masks / Sleeping Masks", price_usd: 49, avg_product_rating: 4.36, loves_count: 64012 },
  { product_id: "P513002", product_name: "Plum Plump Hyaluronic Acid Serum", brand_name: "Glow Recipe", category: "Treatments / Face Serums", price_usd: 39, avg_product_rating: 4.40, loves_count: 79221 },
];

const DEMO_USERS = [
  { author_id: "10000770719", liked_product_count: 9, rated_product_count: 9, mean_user_rating: 4.89, user_rating_count: 9, liked_product_ids: ["P404338", "P447212"] },
  { author_id: "10000412053", liked_product_count: 14, rated_product_count: 17, mean_user_rating: 4.41, user_rating_count: 17, liked_product_ids: ["P411924", "P480901"] },
  { author_id: "10000922117", liked_product_count: 6, rated_product_count: 8, mean_user_rating: 4.62, user_rating_count: 8, liked_product_ids: ["P503879"] },
  { author_id: "10001020498", liked_product_count: 22, rated_product_count: 28, mean_user_rating: 4.18, user_rating_count: 28, liked_product_ids: ["P471123", "P509871", "P492234"] },
  { author_id: "10001150832", liked_product_count: 11, rated_product_count: 12, mean_user_rating: 4.55, user_rating_count: 12, liked_product_ids: ["P513002"] },
];

const HEALTH = {
  status: "ok",
  run_id: "v001",
  best_model_rmse: 0.7636,
  model_type: "MC Dropout Bayesian Neural Network",
  product_count: PRODUCTS.length,
  demo_user_count: DEMO_USERS.length,
  uses_mf_proxy: true,
  mf_proxy_note: "Recommendation scoring uses a user/product mean MF proxy. The BNN ratings + uncertainty are real for the saved evaluation task; full MF candidate scorer not yet exported.",
};

const EXPLAIN = [
  "Sits in the same content neighborhood as your liked products — similar texture, gentle finish.",
  "Shares ingredient signals with what you've liked. The model maps it close in latent space.",
  "Profile matches the kind of formulas you tend to rate highly. Confidence is a touch lower because the brand is new to your history.",
  "Close cousin to one of your liked items — a quieter formulation in the same category.",
  "Smaller signal here, so the model leaves a wider interval. Worth a closer look if curious.",
];

const BUCKETS = ["high_confidence", "high_confidence", "medium_confidence", "medium_confidence", "low_confidence"];

function pick(arr, i) { return arr[i % arr.length]; }
function rand(seed) { const x = Math.sin(seed) * 10000; return x - Math.floor(x); }

function buildRecs(seed, top_n, exclude = []) {
  const pool = PRODUCTS.filter((p) => !exclude.includes(p.product_id));
  return pool.slice(0, top_n).map((p, i) => {
    const r = rand(seed + i);
    const score = +(3.6 + r * 1.35).toFixed(2);
    const unc = +(0.02 + r * 0.55).toFixed(3);
    const risk = +(score - 0.5 * unc).toFixed(2);
    const bucket = pick(BUCKETS, i + Math.floor(seed));
    const lower = +Math.max(1, score - 0.45 - r * 0.4).toFixed(2);
    const upper = +Math.min(5, score + 0.06 + r * 0.1).toFixed(2);
    return {
      ...p,
      predicted_score: score,
      risk_adjusted_score: risk,
      uncertainty: unc,
      confidence_bucket: bucket,
      predicted_interval: { lower, upper, level: "calibrated_95" },
      explanation: pick(EXPLAIN, i + Math.floor(seed)),
    };
  });
}

window.mockApi = {
  health: () => HEALTH,
  search: (q) => {
    const t = (q || "").trim().toLowerCase();
    if (!t) return PRODUCTS.slice(0, 8);
    return PRODUCTS.filter((p) =>
      p.product_name.toLowerCase().includes(t) ||
      p.brand_name.toLowerCase().includes(t) ||
      p.category.toLowerCase().includes(t)
    );
  },
  demoUsers: () => DEMO_USERS,
  recommendForUser: (id, top_n = 10) => {
    const seed = parseInt(String(id).slice(-4), 10) || 1;
    return {
      run_id: HEALTH.run_id,
      best_model_rmse: HEALTH.best_model_rmse,
      uses_mf_proxy: HEALTH.uses_mf_proxy,
      mf_proxy_note: HEALTH.mf_proxy_note,
      recommendations: buildRecs(seed, top_n),
    };
  },
  recommendCustom: (payload) => {
    const seed = (payload.liked_product_ids || []).reduce(
      (a, id) => a + (parseInt(String(id).slice(1), 10) || 0),
      7
    );
    let recs = buildRecs(seed, payload.top_n || 10, payload.liked_product_ids || []);
    if (payload.filters && payload.filters.max_price_usd) {
      recs = recs.filter((r) => r.price_usd <= payload.filters.max_price_usd);
    }
    if (payload.filters && payload.filters.secondary_categories && payload.filters.secondary_categories.length) {
      recs = recs.filter((r) =>
        payload.filters.secondary_categories.some((c) =>
          r.category.toLowerCase().includes(String(c).toLowerCase())
        )
      );
    }
    return {
      run_id: HEALTH.run_id,
      best_model_rmse: HEALTH.best_model_rmse,
      uses_mf_proxy: HEALTH.uses_mf_proxy,
      mf_proxy_note: HEALTH.mf_proxy_note,
      recommendations: recs,
    };
  },
};
