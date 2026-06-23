import { useState } from "react";

import SuperAdminDashboard from "./SuperAdminDashboard";
import AdminDashboard from "../admin/AdminDashboard";
import AccountantDashboard from "../accountant/AccountantDashboard";
import { t } from "../../i18n";

export default function SuperAdminPortal({ api, profile, lang = "uz" }) {
  const [activePanel, setActivePanel] = useState("home");

  function renderBackHeader(title, subtitle) {
    return (
      <div className="sectionHeader">
        <button
          className="backButton"
          type="button"
          onClick={() => setActivePanel("home")}
        >
          {t("back", lang)}
        </button>

        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
      </div>
    );
  }

  if (activePanel === "superadmin") {
    return (
      <>
        {renderBackHeader(
          t("superadmin", lang),
          t("superadminDesc", lang)
        )}
        <SuperAdminDashboard api={api} profile={profile} lang={lang} />
      </>
    );
  }

  if (activePanel === "admin") {
    return (
      <>
        {renderBackHeader(
          t("adminFunctions", lang),
          t("adminFunctionsDesc", lang)
        )}
        <AdminDashboard api={api} profile={profile} lang={lang} />
      </>
    );
  }

  if (activePanel === "accounting") {
    return (
      <>
        {renderBackHeader(
          t("accounting", lang),
          t("accountingDesc", lang)
        )}
        <AccountantDashboard api={api} profile={profile} lang={lang} />
      </>
    );
  }

  return (
    <>
      <section className="profilePanel">
        <div>
          <p className="eyebrow">{t("superadmin", lang)}</p>
          <h2>{profile.full_name || "-"}</h2>
          <p className="profileMeta">
            {t("telegramId", lang)}: {profile.telegram_id}
          </p>
        </div>
      </section>

      <section className="menuGrid">
        <button
          className="menuTile icon-role"
          type="button"
          onClick={() => setActivePanel("superadmin")}
        >
          <span className="menuIcon"></span>
          <b>{t("superadmin", lang)}</b>
          <small>{t("superadminDesc", lang)}</small>
        </button>

        <button
          className="menuTile icon-manage"
          type="button"
          onClick={() => setActivePanel("admin")}
        >
          <span className="menuIcon"></span>
          <b>{t("adminFunctions", lang)}</b>
          <small>{t("adminFunctionsDesc", lang)}</small>
        </button>

        <button
          className="menuTile icon-payments wideTile"
          type="button"
          onClick={() => setActivePanel("accounting")}
        >
          <span className="menuIcon"></span>
          <b>{t("accounting", lang)}</b>
          <small>{t("accountingDesc", lang)}</small>
        </button>
      </section>
    </>
  );
}