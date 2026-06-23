// components/Card.jsx
export default function Card({ title, subtitle, children, compact = false }) {
  return (
    <section className={compact ? "card compactCard" : "card"}>
      {(title || subtitle) && (
        <div className="cardHead">
          {title && <h2>{title}</h2>}
          {subtitle && <p className="muted">{subtitle}</p>}
        </div>
      )}

      {children}
    </section>
  );
}