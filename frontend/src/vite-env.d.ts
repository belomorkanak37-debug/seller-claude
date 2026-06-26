/// <reference types="vite/client" />

// Минимальные типы Telegram WebApp SDK, которые мы используем.
interface TelegramWebAppUser {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
}

interface TelegramThemeParams {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
}

interface TelegramHapticFeedback {
  impactOccurred(style: "light" | "medium" | "heavy" | "rigid" | "soft"): void;
  notificationOccurred(type: "error" | "success" | "warning"): void;
  selectionChanged(): void;
}

interface TelegramBackButton {
  show(): void;
  hide(): void;
  onClick(cb: () => void): void;
  offClick(cb: () => void): void;
}

interface TelegramMainButton {
  text: string;
  show(): void;
  hide(): void;
  enable(): void;
  disable(): void;
  showProgress(leaveActive?: boolean): void;
  hideProgress(): void;
  setText(text: string): void;
  onClick(cb: () => void): void;
  offClick(cb: () => void): void;
}

interface TelegramWebApp {
  initData: string;
  initDataUnsafe: { user?: TelegramWebAppUser };
  themeParams: TelegramThemeParams;
  colorScheme: "light" | "dark";
  version: string;
  isExpanded: boolean;
  ready(): void;
  expand(): void;
  close(): void;
  BackButton: TelegramBackButton;
  MainButton: TelegramMainButton;
  HapticFeedback: TelegramHapticFeedback;
  onEvent(event: string, cb: () => void): void;
  offEvent(event: string, cb: () => void): void;
}

interface Window {
  Telegram?: { WebApp: TelegramWebApp };
}
