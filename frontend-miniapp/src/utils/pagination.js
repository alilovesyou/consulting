export function paginate(items = [], page = 1, pageSize = 10) {
  const safePage = Math.max(Number(page) || 1, 1);
  const safePageSize = Math.max(Number(pageSize) || 10, 1);

  const start = (safePage - 1) * safePageSize;
  const end = start + safePageSize;

  return items.slice(start, end);
}

export function getTotalPages(items = [], pageSize = 10) {
  const safePageSize = Math.max(Number(pageSize) || 10, 1);
  return Math.max(Math.ceil(items.length / safePageSize), 1);
}

export function clampPage(page, totalPages) {
  const safeTotal = Math.max(Number(totalPages) || 1, 1);
  const safePage = Math.max(Number(page) || 1, 1);

  return Math.min(safePage, safeTotal);
}