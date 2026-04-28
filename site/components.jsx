/* @jsx React.createElement */
const { useState } = React;

function assetPath(rel) {
  return (window.UPSKIN_ASSETS || "./assets") + rel;
}

// ---------- Buttons ----------
function PrimaryBtn({ children, onClick, disabled, type = "button" }) {
  return <button type={type} onClick={onClick} disabled={disabled} className="btn btn-primary">{children}</button>;
}
function SecondaryBtn({ children, onClick, disabled, type = "button" }) {
  return <button type={type} onClick={onClick} disabled={disabled} className="btn btn-secondary">{children}</button>;
}
function GhostBtn({ children, onClick }) {
  return <button onClick={onClick} className="btn btn-ghost">{children}</button>;
}
function LinkBtn({ children, onClick }) {
  return <button onClick={onClick} className="btn btn-link">{children}</button>;
}

// ---------- Eyebrow / Step ----------
function Eyebrow({ children, tone }) {
  return <div className={"eyebrow" + (tone ? " eyebrow-" + tone : "")}>{children}</div>;
}
function StepHeader({ step, total, title, sub }) {
  return (
    <div className="step-header">
      <Eyebrow tone="rose">Step {step} of {total}</Eyebrow>
      <h2 className="step-title">{title}</h2>
      {sub ? <p className="step-sub">{sub}</p> : null}
    </div>
  );
}

// ---------- Inputs ----------
function SearchInput({ value, onChange, placeholder, autoFocus }) {
  return (
    <label className="search-input">
      <Icon name="search" size={16} />
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder || "Search a product, brand, or category…"}
        autoFocus={autoFocus}
      />
    </label>
  );
}

// ---------- Chip ----------
function Chip({ children, onRemove, selected, onClick }) {
  return (
    <span
      className={"chip" + (selected ? " chip-selected" : "") + (onClick ? " chip-clickable" : "")}
      onClick={onClick}
    >
      {children}
      {onRemove ? (
        <button className="chip-x" onClick={(e) => { e.stopPropagation(); onRemove(); }} aria-label="Remove">
          <Icon name="x" size={10} />
        </button>
      ) : null}
    </span>
  );
}

// ---------- ProductTile (search result + selected) ----------
function ProductTile({ product, onAdd, onRemove, selected }) {
  const imgSrc = product.image_url || assetPath("/placeholder-product.svg");
  return (
    <div className="product-tile">
      <div className="product-thumb">
        <img src={imgSrc} alt="" loading="lazy"/>
      </div>
      <div className="product-meta">
        <div className="product-brand">{product.brand_name}</div>
        <div className="product-name">{product.product_name}</div>
        <div className="product-cat">{product.category}</div>
      </div>
      <div className="product-aside">
        {product.price_usd != null ? <div className="product-price">${product.price_usd.toFixed(0)}</div> : null}
        {selected ? (
          <button className="tile-btn tile-btn-remove" onClick={onRemove}>Remove</button>
        ) : (
          <button className="tile-btn tile-btn-add" onClick={onAdd}>+ Like</button>
        )}
      </div>
    </div>
  );
}

// ---------- Icon (inline svg, lucide-style strokes) ----------
const ICONS = {
  search: <><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></>,
  x: <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>,
  arrowRight: <><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></>,
  arrowLeft: <><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></>,
  heart: <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.29 1.51 4.04 3 5.5l7 7Z"/>,
  sparkles: <><path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.582a.5.5 0 0 1 0 .962L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/></>,
  circleDot: <><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/></>,
  circleDashed: <><path d="M10.1 2.18a9.93 9.93 0 0 1 3.8 0"/><path d="M17.6 3.71a9.95 9.95 0 0 1 2.69 2.7"/><path d="M21.82 10.1a9.93 9.93 0 0 1 0 3.8"/><path d="M20.29 17.6a9.95 9.95 0 0 1-2.7 2.69"/><path d="M13.9 21.82a9.94 9.94 0 0 1-3.8 0"/><path d="M6.4 20.29a9.95 9.95 0 0 1-2.69-2.7"/><path d="M2.18 13.9a9.93 9.93 0 0 1 0-3.8"/><path d="M3.71 6.4a9.95 9.95 0 0 1 2.7-2.69"/></>,
  sliders: <><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="2" y1="14" x2="6" y2="14"/><line x1="10" y1="8" x2="14" y2="8"/><line x1="18" y1="16" x2="22" y2="16"/></>,
  user: <><circle cx="12" cy="8" r="5"/><path d="M3 21a9 9 0 0 1 18 0"/></>,
  info: <><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></>,
  check: <polyline points="20 6 9 17 4 12"/>,
};
function Icon({ name, size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      {ICONS[name]}
    </svg>
  );
}

Object.assign(window, {
  PrimaryBtn, SecondaryBtn, GhostBtn, LinkBtn,
  Eyebrow, StepHeader,
  SearchInput, Chip, ProductTile, Icon,
  assetPath,
});
