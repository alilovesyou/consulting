// components/ErrorBox.jsx
import { t } from "../i18n";

export default function ErrorBox({ message, lang = "uz" }) {
  return (
    <div className="loadingScreen">
      <section className="plainCard">
        <h2>{t("error", lang)}</h2>
        <p>{message}</p>
        <span>{t("miniAppTelegramNote", lang)}</span>
      </section>
    </div>
  );
}