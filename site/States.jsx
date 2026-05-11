/* @jsx React.createElement */

function ErrorState({ title, body, onRetry }) {
  return (
    <div className="state state-error">
      <div className="state-art" aria-hidden="true">
        <img src={assetPath("/motifs/drop.svg")} alt=""/>
      </div>
      <Eyebrow>Something's off</Eyebrow>
      <h3 className="state-title">{title || "We couldn't reach the model right now."}</h3>
      <p className="state-body">{body || "The backend may be waking up. Give it a moment, then try again."}</p>
      {onRetry ? <PrimaryBtn onClick={onRetry}>Try again</PrimaryBtn> : null}
    </div>
  );
}

function EmptyState({ title, body, action }) {
  return (
    <div className="state state-empty">
      <div className="state-art" aria-hidden="true">
        <img src={assetPath("/motifs/petal.svg")} alt=""/>
      </div>
      <Eyebrow>Nothing here yet</Eyebrow>
      <h3 className="state-title">{title}</h3>
      <p className="state-body">{body}</p>
      {action}
    </div>
  );
}

function LoadingState({ title, body, showAfter = 0 }) {
  const [elapsed, setElapsed] = React.useState(0);
  const [visible, setVisible] = React.useState(showAfter === 0);

  React.useEffect(() => {
    const t0 = Date.now();
    const tick = setInterval(() => {
      const s = Math.floor((Date.now() - t0) / 1000);
      setElapsed(s);
      if (s >= showAfter) setVisible(true);
    }, 500);
    return () => clearInterval(tick);
  }, [showAfter]);

  if (!visible) return null;

  let reason = "";
  if (elapsed >= 5) reason = "Backend waking…";
  if (elapsed >= 15) reason = "Cold start (~30–60s).";
  if (elapsed >= 75) reason = "Service may be down.";

  return (
    <div className="loading-state" role="status" aria-live="polite">
      <div className="loading-spinner" aria-hidden="true"/>
      <div className="loading-text">
        <div className="loading-title">{title || "Loading…"}</div>
        {reason ? <div className="loading-reason">{reason}</div> : null}
        <div className="loading-elapsed mono">{elapsed}s</div>
      </div>
    </div>
  );
}

window.ErrorState = ErrorState;
window.EmptyState = EmptyState;
window.LoadingState = LoadingState;
