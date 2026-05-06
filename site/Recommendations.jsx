/* @jsx React.createElement */
const { useState: useRecState } = React;

function bucketCopy(b) {
  if (b === "high_confidence") return { eyebrow: "Confident pick", body: "The model is fairly sure you'll like this.", tone: "high" };
  if (b === "medium_confidence") return { eyebrow: "Good lead", body: "A reasonable match — worth a closer look.", tone: "med" };
  return { eyebrow: "Soft suggestion", body: "The model is less sure here. Take it lightly.", tone: "low" };
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function IntervalBar({ score, lower, upper }) {
  const min = 1, max = 5;
  const pct = (v) => (clamp(v, min, max) - min) / (max - min) * 100;
  const fmt = (v) => (typeof v === "number" ? v.toFixed(2) : "—");
  return (
    <div className="interval">
      <div className="interval-track">
        <div
          className="interval-band"
          style={{ left: pct(lower) + "%", width: (pct(upper) - pct(lower)) + "%" }}
        />
        <div className="interval-mark" style={{ left: pct(score) + "%" }}/>
      </div>
      <div className="interval-labels">
        <span>1.0</span>
        <span className="interval-mid">predicted {fmt(score)} · interval {fmt(lower)}–{fmt(upper)}</span>
        <span>5.0</span>
      </div>
    </div>
  );
}

function RecCard({ rec, idx, expanded, onToggle, usesMfProxy }) {
  const c = bucketCopy(rec.confidence_bucket);
  const interval = rec.predicted_interval || { lower: rec.predicted_score, upper: rec.predicted_score };
  const imgSrc = rec.image_url || assetPath("/placeholder-product.svg");
  return (
    <article
      className={"rec-card rec-tone-" + c.tone}
      style={{ animationDelay: idx * 60 + "ms" }}
    >
      <div className="rec-thumb">
        <img src={imgSrc} alt="" loading="lazy"/>
      </div>
      <div className="rec-body">
        <div className="rec-head">
          <Eyebrow tone={c.tone}>{c.eyebrow}</Eyebrow>
          <span className="rec-score">
            {typeof rec.predicted_score === "number" ? rec.predicted_score.toFixed(2) : "—"}
          </span>
        </div>
        <div className="rec-brand">{rec.brand_name}</div>
        <h3 className="rec-name">{rec.product_name}</h3>
        <div className="rec-cat">{rec.category}</div>

        <IntervalBar
          score={rec.predicted_score}
          lower={interval.lower}
          upper={interval.upper}
        />

        <div className="rec-metrics">
          <div className="rec-metric">
            <span className="rec-metric-num">
              {typeof rec.risk_adjusted_score === "number" ? rec.risk_adjusted_score.toFixed(2) : "—"}
            </span>
            <span className="rec-metric-label">risk-adj.</span>
          </div>
          <div className="rec-metric">
            <span className="rec-metric-num">
              {typeof rec.uncertainty === "number" ? rec.uncertainty.toFixed(3) : "—"}
            </span>
            <span className="rec-metric-label">uncertainty</span>
          </div>
          {typeof rec.price_usd === "number" ? (
            <div className="rec-metric">
              <span className="rec-metric-num">${rec.price_usd.toFixed(0)}</span>
              <span className="rec-metric-label">price</span>
            </div>
          ) : null}
        </div>

        <p className={"rec-explain" + (expanded ? " open" : "")}>
          {c.body} {rec.explanation}
        </p>
        <button className="btn btn-link rec-toggle" onClick={onToggle}>
          {expanded ? "Show less" : "Why this?"}
        </button>

        {usesMfProxy ? (
          <span className="rec-mfproxy" title="Scoring uses a proxy ranker on this card">
            <Icon name="info" size={12}/>
            <span>matrix-proxy score · class-demo</span>
          </span>
        ) : null}
      </div>
    </article>
  );
}

function Recommendations({ data, onRestart, onOpenNotes }) {
  const [expanded, setExpanded] = useRecState({});

  if (!data) {
    return (
      <section className="results">
        <div className="results-head">
          <Eyebrow>Today's picks</Eyebrow>
          <h2 className="results-title">Pulling a few you might love…</h2>
          <p className="results-sub">The model is sampling — a moment.</p>
        </div>
        <div className="rec-grid">
          {Array.from({ length: 6 }).map((_, i) => <SkelRecCard key={i}/>)}
        </div>
      </section>
    );
  }

  const recs = Array.isArray(data.recommendations) ? data.recommendations : [];

  return (
    <section className="results">
      <div className="results-head">
        <Eyebrow>Today's picks</Eyebrow>
        <h2 className="results-title">In your neighborhood.</h2>
        <p className="results-sub">
          {recs.length} recommendation{recs.length === 1 ? "" : "s"} from the live model. Confidence is shown honestly.
        </p>
        {data.uses_mf_proxy ? (
          <div className="proxy-note">
            <Icon name="info" size={14}/>
            <span>
              {data.mf_proxy_note ||
                "Heads up — this is a class-demo. Some scores use a proxy ranker until the full matrix-factorization model ships."}
            </span>
          </div>
        ) : null}
      </div>

      <div className="rec-grid">
        {recs.map((r, i) => (
          <RecCard
            key={r.product_id}
            rec={r}
            idx={i}
            expanded={!!expanded[r.product_id]}
            onToggle={() => setExpanded((s) => ({ ...s, [r.product_id]: !s[r.product_id] }))}
            usesMfProxy={!!data.uses_mf_proxy}
          />
        ))}
      </div>

      <div className="results-foot">
        {onRestart ? <SecondaryBtn onClick={onRestart}>Start a new profile</SecondaryBtn> : null}
        {onOpenNotes ? <LinkBtn onClick={onOpenNotes}>How this works</LinkBtn> : null}
        {data.run_id || data.best_model_rmse != null ? (
          <span className="model-stamp mono">
            {data.run_id ? "run " + data.run_id : ""}
            {data.run_id && data.best_model_rmse != null ? " · " : ""}
            {data.best_model_rmse != null ? "best RMSE " + Number(data.best_model_rmse).toFixed(4) : ""}
          </span>
        ) : null}
      </div>
    </section>
  );
}

window.Recommendations = Recommendations;
