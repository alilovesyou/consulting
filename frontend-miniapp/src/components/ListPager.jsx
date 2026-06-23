import { t } from "../i18n";

export default function ListPager({
  page,
  totalPages,
  totalItems,
  pageSize,
  onPrev,
  onNext,
  lang = "uz",
}) {
  if (!totalItems || totalItems <= pageSize) {
    return null;
  }

  return (
    <div className="listPager">
      <button type="button" disabled={page <= 1} onClick={onPrev}>
        {t("prev", lang)}
      </button>

      <span>
        {t("page", lang)} {page}/{totalPages}
      </span>

      <button type="button" disabled={page >= totalPages} onClick={onNext}>
        {t("next", lang)}
      </button>
    </div>
  );
}