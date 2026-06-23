export default function SearchBox({
  value,
  onChange,
  placeholder = "Qidirish...",
}) {
  return (
    <div className="searchBox">
      <span>🔎</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  );
}