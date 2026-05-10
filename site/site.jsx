/* @jsx React.createElement */
const { useState: useSiteState, useEffect: useSiteEffect } = React;

function Site() {
  const [view, setView] = useSiteState("welcome");
  const [results, setResults] = useSiteState(null);
  const [error, setError] = useSiteState(null);
  const [sheet, setSheet] = useSiteState(false);
  const [health, setHealth] = useSiteState(null);

  useSiteEffect(() => {
    let cancelled = false;
    window.upskinApi.health()
      .then((h) => { if (!cancelled) setHealth(h); })
      .catch(() => { if (!cancelled) setHealth({ status: "down" }); });
    return () => { cancelled = true; };
  }, []);

  const restart = () => { setResults(null); setError(null); setView("welcome"); };

  const runDemo = (id, top_n = 10) => {
    setView("loading"); setError(null);
    window.upskinApi.recommendForUser(id, top_n)
      .then((d) => { setResults(d); setView("results"); })
      .catch((e) => { setError(e); setView("error"); });
  };
  const runCustom = (payload) => {
    setView("loading"); setError(null);
    window.upskinApi.recommendCustom(payload)
      .then((d) => {
        if (!d || !d.recommendations || d.recommendations.length === 0) {
          setResults(d); setView("noresults"); return;
        }
        setResults(d); setView("results");
      })
      .catch((e) => { setError(e); setView("error"); });
  };

  const statusClass = !health
    ? "status-checking"
    : health.status === "ok"
      ? "status-ok"
      : "status-down";
  const statusLabel = !health
    ? "Live model checking…"
    : window.upskinApi.usingMock
      ? "Offline preview"
      : "Live model " + (health.status || "unknown");

  return (
    <div className="page">
      <header className="topbar">
        <a
          href="#"
          className="brand"
          onClick={(e) => { e.preventDefault(); restart(); }}
          aria-label="Up Skin home"
        >
          <img src={assetPath("/wordmark.svg")} alt="Up Skin"/>
        </a>
        <nav className="topnav">
          <button className="topnav-link" onClick={() => setSheet(true)}>How this works</button>
          <span className={"status-pip " + statusClass} title={statusLabel} aria-label={statusLabel}/>
        </nav>
      </header>

      <main className="main">
        <div className="view-stack" key={view}>
          {view === "welcome" && <Welcome onChoose={(p) => setView(p)}/>}
          {view === "demo" && <DemoProfileFlow onBack={restart} onPick={runDemo}/>}
          {view === "custom" && <BuildProfileFlow onBack={restart} onSubmit={runCustom}/>}
          {view === "loading" && <Recommendations data={null}/>}
          {view === "results" && (
            <Recommendations data={results} onRestart={restart} onOpenNotes={() => setSheet(true)}/>
          )}
          {view === "noresults" && (
            <EmptyState
              title="No recommendations came back."
              body="Try removing a filter, raising the max price, or selecting more liked products. The model needs a little more signal."
              action={<PrimaryBtn onClick={restart}>Start over</PrimaryBtn>}
            />
          )}
          {view === "error" && (
            <ErrorState
              title="We couldn't reach the recommender."
              body={error?.detail || "The model service may be waking up. Try again in a moment."}
              onRetry={restart}
            />
          )}
        </div>
      </main>

      <footer className="footer">
        <span className="footer-disclaimer">
          Up Skin recommends based on rating patterns and product similarity. It does not provide medical, allergy, or dermatology advice.
        </span>
        <button className="footer-link" onClick={() => setSheet(true)}>Model notes</button>
      </footer>

      <ModelTransparency open={sheet} onClose={() => setSheet(false)}/>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<Site/>);
