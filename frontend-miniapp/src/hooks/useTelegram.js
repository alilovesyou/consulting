// frontend-miniapp/src/hooks/useTelegram.js
export function useTelegram() {
  const tg = window.Telegram?.WebApp || null;

  const initTelegram = () => {
    if (!tg) return;

    tg.ready();
    tg.expand();

    if (tg.MainButton) {
      tg.MainButton.hide();
    }
  };

  return {
    tg,
    user: tg?.initDataUnsafe?.user || null,
    initData: tg?.initData || "",
    colorScheme: tg?.colorScheme || "light",
    initTelegram,
  };
}