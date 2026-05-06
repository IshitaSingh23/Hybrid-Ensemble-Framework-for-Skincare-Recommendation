# MC-BNN Version Results Log

Best run so far by test BNN RMSE: `v001` with RMSE `0.7636`.

| run_id | created_at | model_type | best_epoch | mc_samples | dropout_rate | test_mf_rmse | test_hybrid_rmse | test_bnn_rmse | test_mf_mae | test_hybrid_mae | test_bnn_mae | bnn_beats_test_mf_rmse | bnn_beats_test_hybrid_rmse | test_uncertainty_abs_error_corr | test_calibrated_interval_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v001 | 2026-04-27T15:46:49 | MC Dropout Bayesian Neural Network | 7 | 100 | 0.2000 | 0.7786 | 0.7922 | 0.7636 | 0.4888 | 0.5726 | 0.4956 | True | True | 0.3949 | 0.9465 |
| v002 | 2026-05-05T23:38:36 | MC Dropout Bayesian Neural Network | 15 | 100 | 0.2000 | 0.7807 | 0.8040 | 0.7793 | 0.4912 | 0.5770 | 0.4687 | True | True | 0.4994 | 0.9444 |
