// Extends the offline preview API with /model/metrics so the transparency panel runs without a backend.
window.mockApi = window.mockApi || {};
window.mockApi.metrics = () => ({
  run_id: "v002",
  best_model: {
    model_type: "MC Dropout Bayesian Neural Network",
    best_epoch: 15,
    test_bnn_rmse: 0.7793,
    test_bnn_mae: 0.4687,
    test_mf_rmse: 0.7807,
    test_mf_mae: 0.4912,
    test_hybrid_rmse: 0.8040,
    test_hybrid_mae: 0.5770,
    bnn_beats_mf_rmse: true,
    bnn_beats_hybrid_rmse: true,
  },
  model_config: {
    input_dim: 138,
    dropout_rate: 0.20,
  },
  uncertainty: {
    mc_samples: 100,
    test_uncertainty_abs_error_corr: 0.4994,
    test_calibrated_interval_coverage: 0.9444,
  },
});
