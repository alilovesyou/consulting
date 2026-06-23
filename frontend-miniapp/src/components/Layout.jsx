function getInitial(name) {
  if (!name) return "V";
  return String(name).trim().charAt(0).toUpperCase();
}

function roleLabel(role) {
  const labels = {
    student: "Student",
    teacher: "Teacher",
    admin: "Admin",
    accountant: "Accounting",
    superadmin: "Superadmin",
    user: "User",
  };

  return labels[role] || role || "User";
}

export default function Layout({ profile, title, children }) {
  const fullName = profile?.full_name || "Visa & Language";
  const role = profile?.role || "user";

  return (
    <div className="mobileFrame">
      <header className="simpleHeader">
        <div className="simpleUser">
          <div className="simpleAvatar">{getInitial(fullName)}</div>

          <div className="simpleUserText">
            <p>{fullName}</p>
            <span>{title}</span>
          </div>
        </div>

        <div className={`simpleRole role-${role}`}>
          {roleLabel(role)}
        </div>
      </header>

      <main className="simpleContent">{children}</main>
    </div>
  );
}