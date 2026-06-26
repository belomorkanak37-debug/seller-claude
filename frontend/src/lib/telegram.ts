// Обёртка над window.Telegram.WebApp. Безопасно работает и вне Telegram
// (например, при открытии в обычном браузере для отладки вёрстки).

export function getWebApp(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null;
}

export function isInTelegram(): boolean {
  const wa = getWebApp();
  return !!wa && !!wa.initData;
}

/** Сообщает Telegram, что приложение готово, и разворачивает на весь экран. */
export function initTelegram(): void {
  const wa = getWebApp();
  if (!wa) return;
  wa.ready();
  wa.expand();
  applyTheme();
  wa.onEvent("themeChanged", applyTheme);
}

/** Прокидывает параметры темы Telegram в CSS-переменные. */
export function applyTheme(): void {
  const wa = getWebApp();
  if (!wa) return;
  const tp = wa.themeParams;
  const root = document.documentElement;
  const map: Record<string, string | undefined> = {
    "--tg-theme-bg-color": tp.bg_color,
    "--tg-theme-text-color": tp.text_color,
    "--tg-theme-hint-color": tp.hint_color,
    "--tg-theme-link-color": tp.link_color,
    "--tg-theme-button-color": tp.button_color,
    "--tg-theme-button-text-color": tp.button_text_color,
    "--tg-theme-secondary-bg-color": tp.secondary_bg_color,
  };
  for (const [key, value] of Object.entries(map)) {
    if (value) root.style.setProperty(key, value);
  }
}

export function haptic(
  type: "light" | "medium" | "heavy" | "success" | "error" | "warning"
): void {
  const hf = getWebApp()?.HapticFeedback;
  if (!hf) return;
  if (type === "success" || type === "error" || type === "warning") {
    hf.notificationOccurred(type);
  } else {
    hf.impactOccurred(type);
  }
}

/** Сырой initData для отправки на бэкенд (там проверяется подпись). */
export function getInitData(): string {
  return getWebApp()?.initData ?? "";
}
