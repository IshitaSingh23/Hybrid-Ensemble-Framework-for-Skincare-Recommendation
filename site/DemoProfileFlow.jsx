/* @jsx React.createElement */
const { useState: useDemoState, useEffect: useDemoEffect } = React;

function DemoProfileFlow({ onBack, onPick }) {
  const [users, setUsers] = useDemoState([]);
  const [selected, setSelected] = useDemoState(null);
  const [loading, setLoading] = useDemoState(true);
  const [error, setError] = useDemoState(null);

  useDemoEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    window.upskinApi.demoUsers()
      .then((u) => { if (!cancelled) { setUsers(u); setLoading(false); } })
      .catch((e) => { if (!cancelled) { setError(e); setLoading(false); } });
    return () => { cancelled = true; };
  }, []);

  if (error) {
    return (
      <section className="flow">
        <button className="back-link" onClick={onBack}>
          <Icon name="arrowLeft" size={14}/> back
        </button>
        <ErrorState
          title="We couldn't load saved profiles."
          body={error.detail || "The backend may be waking up. Give it a moment, then try again."}
          onRetry={() => {
            setError(null); setLoading(true);
            window.upskinApi.demoUsers()
              .then((u) => { setUsers(u); setLoading(false); })
              .catch((e) => { setError(e); setLoading(false); });
          }}
        />
      </section>
    );
  }

  return (
    <section className="flow">
      <button className="back-link" onClick={onBack}>
        <Icon name="arrowLeft" size={14}/> back
      </button>
      <StepHeader
        step={1}
        total={2}
        title="Pick a saved profile"
        sub="Each profile is anonymized. We use its rating history to seed recommendations — nothing personal is shown."
      />
      {loading ? <LoadingState title="Loading profiles…" showAfter={2}/> : null}
      <div className="profile-grid">
        {loading && Array.from({ length: 6 }).map((_, i) => <SkelProfile key={i}/>)}
        {!loading && users.length === 0 && (
          <EmptyState
            title="No demo profiles available."
            body="The backend returned an empty profile list. Try the build-my-profile path instead."
          />
        )}
        {!loading && users.map((u, i) => {
          const num = String(i + 1).padStart(2, "0");
          const isSel = selected === u.author_id;
          const mean = (typeof u.mean_user_rating === "number" ? u.mean_user_rating : 0).toFixed(2);
          return (
            <button
              key={u.author_id}
              className={"profile-card" + (isSel ? " profile-selected" : "")}
              onClick={() => setSelected(u.author_id)}
            >
              <div className="profile-num">Profile {num}</div>
              <div className="profile-stats">
                <div>
                  <span className="profile-stat-num">{u.liked_product_count}</span>
                  <span className="profile-stat-label">liked</span>
                </div>
                <div className="profile-stat-divider"/>
                <div>
                  <span className="profile-stat-num">{u.user_rating_count}</span>
                  <span className="profile-stat-label">rated</span>
                </div>
                <div className="profile-stat-divider"/>
                <div>
                  <span className="profile-stat-num">{mean}</span>
                  <span className="profile-stat-label">mean</span>
                </div>
              </div>
              <div className="profile-id mono">{u.author_id}</div>
              {isSel ? <div className="profile-check"><Icon name="check" size={14}/></div> : null}
            </button>
          );
        })}
      </div>
      <div className="step-actions">
        <PrimaryBtn disabled={!selected} onClick={() => onPick(selected)}>
          See recommendations <Icon name="arrowRight" size={14}/>
        </PrimaryBtn>
      </div>
    </section>
  );
}

window.DemoProfileFlow = DemoProfileFlow;
