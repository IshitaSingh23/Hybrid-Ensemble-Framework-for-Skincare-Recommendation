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

window.ErrorState = ErrorState;
window.EmptyState = EmptyState;
