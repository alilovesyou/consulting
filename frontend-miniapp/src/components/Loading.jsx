// components/Loading.jsx
import { t } from "../i18n";

export default function Loading({ lang = "uz" }) {
  return (
    <div className="loadingScreen">
      <div className="softLoader"></div>
      <p>{t("loading", lang)}</p>
    </div>
  );
}