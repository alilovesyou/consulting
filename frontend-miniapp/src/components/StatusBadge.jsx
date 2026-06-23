export default function StatusBadge({ status }) {
  const value = status || "unknown";

  return (
    <span className={`statusBadge status-${value}`}>
      {value}
    </span>
  );
}