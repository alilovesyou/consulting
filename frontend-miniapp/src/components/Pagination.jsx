export default function Pagination({ page, hasNext, onPrev, onNext }) {
  return (
    <div className="pagination">
      <button
        className="pageBtn"
        type="button"
        disabled={page <= 1}
        onClick={onPrev}
      >
        ← Prev
      </button>

      <span className="pageNumber">Page {page}</span>

      <button
        className="pageBtn"
        type="button"
        disabled={!hasNext}
        onClick={onNext}
      >
        Next →
      </button>
    </div>
  );
}