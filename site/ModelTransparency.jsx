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

const FALLBACK_STALE_NOTES = [
  { title: "Explanations are heuristic", body: "Card explanations are derived from product metadata, ingredient keyword groups, and content similarity — not SHAP or learned attribution." },
  { title: "Risk adjustment is a fixed penalty", body: "risk_adjusted_score = predicted_score − 0.5 × uncertainty. The 0.5 weight is a serving rule, not a tuned parameter." },
  { title: "Custom profiles are content-based", body: "For brand-new visitors, liked product IDs build a content profile from transformer embeddings — not a trained historical user profile." },
  { title: "Medical / allergy safety is not modeled", body: "The recommender ranks by ratings + content similarity + uncertainty. It does not screen ingredients for allergies or treat skin conditions." },
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
  const staleNotes = (data && data.stale_notes && data.stale_notes.length)
    ? data.stale_notes
    : FALLBACK_STALE_NOTES;

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
          The model behind Up Skin is an MC-Dropout Bayesian Neural Network. It predicts a rating for each candidate
          and reports how sure it is — never how safe a product is for your skin.
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
                <MetricRow label="MF RMSE" value={fmtNumber(best.test_mf_rmse, 4)}/>
                <MetricRow label="Hybrid RMSE" value={fmtNumber(best.test_hybrid_rmse, 4)}/>
                {best.bnn_beats_mf_rmse !== undefined && best.bnn_beats_hybrid_rmse !== undefined ? (
                  <p className="metric-blurb">
                    {best.bnn_beats_mf_rmse ? "BNN beats MF" : "MF beats BNN"} {" · "}
                    {best.bnn_beats_hybrid_rmse ? "BNN beats hybrid" : "Hybrid beats BNN"} on test RMSE.
                  </p>
                ) : null}
              </div>
            ) : null}

            {unc ? (
              <div className="metric-section">
                <Eyebrow>Uncertainty · MC dropout</Eyebrow>
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

            {data.uses_mf_proxy ? (
              <div className="proxy-note proxy-note-sheet">
                <Icon name="info" size={14}/>
                <span>{data.mf_proxy_note}</span>
              </div>
            ) : null}

            <div className="metric-section">
              <Eyebrow>Prototype limitations</Eyebrow>
              <ul className="stale-list">
                {staleNotes.map((n) => (
                  <li key={n.title}><strong>{n.title}.</strong> {n.body}</li>
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
