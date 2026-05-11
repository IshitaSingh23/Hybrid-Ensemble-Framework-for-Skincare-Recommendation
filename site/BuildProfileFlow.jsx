/* @jsx React.createElement */
const { useState: useBuildState, useMemo: useBuildMemo, useEffect: useBuildEffect } = React;

function BuildProfileFlow({ onBack, onSubmit }) {
  const [step, setStep] = useBuildState(1);
  const [query, setQuery] = useBuildState("");
  const [results, setResults] = useBuildState([]);
  const [searching, setSearching] = useBuildState(true);
  const [searchError, setSearchError] = useBuildState(null);
  const [searchNonce, setSearchNonce] = useBuildState(0);

  const [liked, setLiked] = useBuildState([]);
  const [maxPrice, setMaxPrice] = useBuildState(75);
  const [topN, setTopN] = useBuildState(10);
  const [activeCats, setActiveCats] = useBuildState([]);

  useBuildEffect(() => {
    let cancelled = false;
    setSearching(true);
    setSearchError(null);
    const t = setTimeout(() => {
      window.upskinApi.searchProducts(query)
        .then((r) => { if (!cancelled) { setResults(r); setSearching(false); } })
        .catch((e) => { if (!cancelled) { setSearchError(e); setSearching(false); } });
    }, query ? 220 : 0);
    return () => { cancelled = true; clearTimeout(t); };
  }, [query, searchNonce]);

  const isLiked = (id) => liked.some((p) => p.product_id === id);
  const toggleLike = (p) => {
    if (isLiked(p.product_id)) {
      setLiked(liked.filter((x) => x.product_id !== p.product_id));
    } else {
      setLiked([...liked, p]);
    }
  };
  const removeLike = (id) => setLiked(liked.filter((x) => x.product_id !== id));

  // Derive category chips from selected/searched products (per the brief — never hardcode).
  const categoryOptions = useBuildMemo(() => {
    const set = new Set();
    [...liked, ...results].forEach((p) => {
      if (!p.category) return;
      const top = p.category.split(" / ")[0];
      if (top) set.add(top);
    });
    return [...set].slice(0, 6);
  }, [liked, results]);

  const toggleCat = (c) => {
    setActiveCats(activeCats.includes(c) ? activeCats.filter((x) => x !== c) : [...activeCats, c]);
  };

  const submit = () => {
    onSubmit({
      liked_product_ids: liked.map((p) => p.product_id),
      top_n: topN,
      filters: {
        secondary_categories: activeCats,
        max_price_usd: maxPrice,
        exclude_product_ids: [],
        include_out_of_stock: false,
      },
    });
  };

  return (
    <section className="flow">
      <button className="back-link" onClick={() => (step === 1 ? onBack() : setStep(step - 1))}>
        <Icon name="arrowLeft" size={14}/> back
      </button>

      {step === 1 && (
        <>
          <StepHeader
            step={1}
            total={2}
            title="What have you loved lately?"
            sub="Tell us 3–8 products you've genuinely liked. We'll find more in their neighborhood."
          />
          <SearchInput value={query} onChange={setQuery} autoFocus/>
          {searching ? <LoadingState title="Loading catalog…" showAfter={2}/> : null}
          <div className="results-grid">
            {searching && Array.from({ length: 6 }).map((_, i) => <SkelTile key={i}/>)}
            {!searching && searchError && (
              <ErrorState
                title="Search isn't responding."
                body={searchError.detail || "The backend may be waking up. Try again in a moment."}
                onRetry={() => setSearchNonce((n) => n + 1)}
              />
            )}
            {!searching && !searchError && results.length === 0 ? (
              <div className="empty">
                No matches. Try searching by product, brand, or category.
              </div>
            ) : null}
            {!searching && !searchError && results.map((p) => (
              <ProductTile
                key={p.product_id}
                product={p}
                selected={isLiked(p.product_id)}
                onAdd={() => toggleLike(p)}
                onRemove={() => toggleLike(p)}
              />
            ))}
          </div>
        </>
      )}

      {step === 2 && (
        <>
          <StepHeader
            step={2}
            total={2}
            title="Optional filters"
            sub="Tighten the recommendation set if you'd like. You can skip this and we'll keep it open."
          />
          <div className="filters-panel">
            <div className="filter-row">
              <div className="filter-label">
                <span className="filter-name">Max price</span>
                <span className="filter-value">${maxPrice}</span>
              </div>
              <input
                type="range" min="20" max="200" step="5"
                value={maxPrice} onChange={(e) => setMaxPrice(+e.target.value)}
                className="slider" aria-label="Max price"
              />
            </div>
            <div className="filter-row">
              <div className="filter-label">
                <span className="filter-name">How many to show</span>
              </div>
              <div className="seg" role="tablist">
                {[5, 10, 20].map((n) => (
                  <button
                    key={n}
                    className={"seg-btn" + (topN === n ? " seg-active" : "")}
                    onClick={() => setTopN(n)}
                    aria-pressed={topN === n}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
            {categoryOptions.length > 0 && (
              <div className="filter-row">
                <div className="filter-label">
                  <span className="filter-name">Categories</span>
                  <span className="filter-hint">Drawn from your likes — not a fixed list.</span>
                </div>
                <div className="chip-row">
                  {categoryOptions.map((c) => (
                    <Chip
                      key={c}
                      selected={activeCats.includes(c)}
                      onClick={() => toggleCat(c)}
                    >
                      {c}
                    </Chip>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}

      <aside className="likes-tray" aria-live="polite">
        <div className="likes-tray-head">
          <Eyebrow>You've liked</Eyebrow>
          <span className="likes-count">{liked.length}</span>
        </div>
        {liked.length === 0 ? (
          <p className="likes-empty">
            Pick at least one product to continue. Three or more sharpens the model.
          </p>
        ) : (
          <div className="chip-row">
            {liked.map((p) => (
              <Chip key={p.product_id} onRemove={() => removeLike(p.product_id)}>
                {p.product_name && p.product_name.length > 28
                  ? p.product_name.slice(0, 28) + "…"
                  : p.product_name}
              </Chip>
            ))}
          </div>
        )}
      </aside>

      <div className="step-actions">
        {step === 1 ? (
          <PrimaryBtn disabled={liked.length === 0} onClick={() => setStep(2)}>
            Continue <Icon name="arrowRight" size={14}/>
          </PrimaryBtn>
        ) : (
          <PrimaryBtn onClick={submit}>
            Generate recommendations <Icon name="arrowRight" size={14}/>
          </PrimaryBtn>
        )}
      </div>
    </section>
  );
}

window.BuildProfileFlow = BuildProfileFlow;
