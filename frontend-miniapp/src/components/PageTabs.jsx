export default function PageTabs({ tabs, activeTab, onChange }) {
  return (
    <div className="tabsWrap">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          className={activeTab === tab.key ? "tabBtn active" : "tabBtn"}
          onClick={() => onChange(tab.key)}
          type="button"
        >
          {tab.icon && <span>{tab.icon}</span>}
          {tab.label}
        </button>
      ))}
    </div>
  );
}