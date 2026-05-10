/* @jsx React.createElement */
const { useState: useMtState, useEffect: useMtEffect } = React;

function MetricRow({ label, value, hint, emphasis }) {
  return (
    <div className={"metric-row" + (emphasis ? " metric-emphasis" : "")}>
      <div className="metric-label">
        <span>{label}</span>
        {hint ? <span className="metric-hint">{hint}</span> : null}
      </div>
      <div className="metric-value">{value}</div>
    </div>
  );
}

const MODEL_NOTES = [
  "Scores estimate preference, not medical or allergy safety.",
  "Uncertainty reflects how consistent the model's MC-dropout predictions were.",
  "Explanations summarize product metadata, ingredients, and similarity signals.",
];

function fmtNumber(value, digits) {
  return typeof value === "number" ? value.toFixed(digits) : "—";
}

function ModelTransparency({ open, onClose }) {
  const [data, setData] = useMtState(null);
  const [err, setErr] = useMtState(null);

  const load = () => {
    setErr(null);
    setData(null);
    window.upskinApi.metrics().then(setData).catch(setErr);
  };

  useMtEffect(() => {
    if (!open) return;
    load();
  }, [open]);

  if (!open) return null;

  const best = data && data.best_model ? data.best_model : null;
  const unc = data && data.uncertainty ? data.uncertainty : null;
  const modelConfig = data && data.model_config ? data.model_config : {};
  const matrixLabel = data && data.canonical_matrix_model === "ridge_ensemble"
    ? "Ridge matrix"
    : "Matrix";

  return (
    <div className="sheet-scrim" onClick={onClose}>
      <aside className="sheet" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="sheet-title">
        <div className="sheet-head">
          <Eyebrow>How this works</Eyebrow>
          <button className="sheet-close" onClick={onClose} aria-label="Close">
            <Icon name="x" size={14}/>
          </button>
        </div>
        <h2 id="sheet-title" className="sheet-title">Model notes</h2>
        <p className="sheet-lede">
          Up Skin uses model-backed recommendations to estimate product preference and show confidence clearly. It does not provide medical, allergy, or dermatology advice.
        </p>

        {err ? (
          <ErrorState
            title="Couldn't load metrics."
            body={err.detail || "The /model/metrics endpoint isn't responding."}
            onRetry={load}
          />
        ) : null}

        {!data && !err ? (
          <div className="metric-skel">
            <SkelLine w="60%" h={14}/>
            <SkelLine w="100%" h={10}/>
            <SkelLine w="100%" h={10}/>
            <SkelLine w="80%" h={10}/>
          </div>
        ) : null}

        {data ? (
          <>
            {best ? (
              <div className="metric-section">
                <Eyebrow>Best model · {best.model_type}</Eyebrow>
                <MetricRow label="BNN RMSE" value={fmtNumber(best.test_bnn_rmse, 4)} hint="lower is better" emphasis/>
                <MetricRow label="BNN MAE" value={fmtNumber(best.test_bnn_mae, 4)}/>
                <MetricRow label={matrixLabel + " RMSE"} value={fmtNumber(best.test_mf_rmse, 4)}/>
                <MetricRow label={matrixLabel + " MAE"} value={fmtNumber(best.test_mf_mae, 4)}/>
                <MetricRow label="Hybrid RMSE" value={fmtNumber(best.test_hybrid_rmse, 4)}/>
                <MetricRow label="Hybrid MAE" value={fmtNumber(best.test_hybrid_mae, 4)}/>
                {best.bnn_beats_mf_rmse !== undefined && best.bnn_beats_hybrid_rmse !== undefined ? (
                  <p className="metric-blurb">
                    {best.bnn_beats_mf_rmse ? "BNN beats " + matrixLabel : matrixLabel + " beats BNN"} {" · "}
                    {best.bnn_beats_hybrid_rmse ? "BNN beats hybrid" : "Hybrid beats BNN"} on test RMSE.
                  </p>
                ) : null}
              </div>
            ) : null}

            {unc ? (
              <div className="metric-section">
                <Eyebrow>Uncertainty · MC dropout</Eyebrow>
                <MetricRow label="Best epoch" value={best && best.best_epoch != null ? best.best_epoch : "—"}/>
                <MetricRow label="Input dimension" value={modelConfig.input_dim != null ? modelConfig.input_dim : "138"}/>
                <MetricRow
                  label="Dropout rate"
                  value={typeof modelConfig.dropout_rate === "number" ? modelConfig.dropout_rate.toFixed(2) : "0.20"}
                />
                <MetricRow label="MC samples" value={unc.mc_samples != null ? unc.mc_samples : "—"}/>
                <MetricRow
                  label="Uncertainty ↔ error correlation"
                  value={fmtNumber(unc.test_uncertainty_abs_error_corr, 4)}
                  hint="how well doubt tracks errors"
                />
                <MetricRow
                  label="Calibrated 95% coverage"
                  value={typeof unc.test_calibrated_interval_coverage === "number"
                    ? (unc.test_calibrated_interval_coverage * 100).toFixed(1) + "%"
                    : "—"}
                  hint="should sit near 95%"
                />
              </div>
            ) : null}

            <div className="metric-section">
              <Eyebrow>Model notes</Eyebrow>
              <ul className="notes-list">
                {MODEL_NOTES.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </div>

            {data.run_id ? <p className="run-stamp mono">run {data.run_id}</p> : null}
          </>
        ) : null}
      </aside>
    </div>
  );
}

window.ModelTransparency = ModelTransparency;
