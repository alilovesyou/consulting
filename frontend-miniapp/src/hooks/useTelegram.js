export function useTelegram() {
  const tg = window.Telegram?.WebApp;

  const initTelegram = () => {
    if (!tg) return;

    tg.ready();
    tg.expand();
  };

  return {
    tg,
    user: tg?.initDataUnsafe?.user || null,
    initData: tg?.initData || "",
    initTelegram,
  };
}