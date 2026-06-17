export default function Layout({ profile, title, children }) {
  return (
    <div className="page">
      <header className="appHeader">
        <div>
          <p className="muted">Visa & Language Consulting</p>
          <h1>{title}</h1>
        </div>
        <div className="roleBadge">{profile?.role}</div>
      </header>

      {children}
    </div>
  );
}