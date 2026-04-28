// Extends the offline mockApi with /model/metrics so the transparency panel runs offline.
window.mockApi = window.mockApi || {};
window.mockApi.metrics = () => ({
  run_id: "v001",
  best_model: {
    model_type: "MC Dropout Bayesian Neural Network",
    best_epoch: 7,
    test_bnn_rmse: 0.7636,
    test_bnn_mae: 0.4956,
    test_mf_rmse: 0.7786,
    test_mf_mae: 0.4888,
    test_hybrid_rmse: 0.7922,
    test_hybrid_mae: 0.5726,
    bnn_beats_mf_rmse: true,
    bnn_beats_hybrid_rmse: true,
  },
  uncertainty: {
    mc_samples: 100,
    test_uncertainty_abs_error_corr: 0.3949,
    test_calibrated_interval_coverage: 0.9465,
  },
  uses_mf_proxy: true,
  mf_proxy_note:
    "Recommendation scoring uses a user/product mean MF proxy. The BNN ratings + uncertainty are real for the saved evaluation task; full MF candidate scorer not yet exported.",
  stale_notes: [
    { title: "Explanations are heuristic", body: "Card explanations are derived from product metadata, ingredient keyword groups, and content similarity — not SHAP or learned attribution." },
    { title: "Risk adjustment is a fixed penalty", body: "risk_adjusted_score = predicted_score − 0.5 × uncertainty. The 0.5 weight is a serving rule, not a tuned parameter." },
    { title: "Custom profiles are content-based", body: "For brand-new visitors, liked product IDs build a content profile from transformer embeddings — not a trained historical user profile." },
    { title: "Medical / allergy safety is not modeled", body: "The recommender ranks by ratings + content similarity + uncertainty. It does not screen ingredients for allergies or treat skin conditions." },
  ],
});
