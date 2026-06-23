export default function EmptyState({ title, text }) {
  return (
    <div className="emptyState">
      <h3>{title}</h3>
      {text && <p>{text}</p>}
    </div>
  );
}