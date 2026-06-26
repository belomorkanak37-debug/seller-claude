import { getInitData } from "./telegram";

// По умолчанию ходим на тот же origin через nginx-прокси (/api -> backend).
// Можно переопределить через VITE_API_BASE на этапе сборки.
const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export interface User {
  id: number;
  telegram_id: number;
  username?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  language_code?: string | null;
  photo_url?: string | null;
  notifications_enabled: boolean;
  registered_at: string;
}

export interface AuthResponse {
  user: User;
  is_new: boolean;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      // Защищённые эндпоинты читают initData отсюда.
      Authorization: `tma ${getInitData()}`,
      ...(options.headers ?? {}),
    },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

/** Авторизация Mini App: отправляем initData, бэкенд валидирует подпись. */
export function authTelegram(): Promise<AuthResponse> {
  return request<AuthResponse>("/auth/telegram", {
    method: "POST",
    body: JSON.stringify({ init_data: getInitData() }),
  });
}
