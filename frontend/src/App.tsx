import { Loader2, ShieldCheck, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { authTelegram, type User } from "@/lib/api";
import { getWebApp, haptic, isInTelegram } from "@/lib/telegram";

type State =
  | { status: "loading" }
  | { status: "ready"; user: User; isNew: boolean }
  | { status: "error"; message: string };

export default function App() {
  const [state, setState] = useState<State>({ status: "loading" });

  async function authenticate() {
    setState({ status: "loading" });
    if (!isInTelegram()) {
      setState({
        status: "error",
        message:
          "Откройте приложение через Telegram-бота — здесь нужны данные авторизации Telegram.",
      });
      return;
    }
    try {
      const res = await authTelegram();
      haptic("success");
      setState({ status: "ready", user: res.user, isNew: res.is_new });
    } catch (e) {
      haptic("error");
      const message = e instanceof Error ? e.message : "Не удалось авторизоваться";
      setState({ status: "error", message });
    }
  }

  useEffect(() => {
    authenticate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // BackButton демонстрирует управление нативными кнопками Telegram.
  useEffect(() => {
    const wa = getWebApp();
    if (!wa) return;
    const onBack = () => {
      haptic("light");
      wa.close();
    };
    wa.BackButton.onClick(onBack);
    if (state.status === "ready") {
      wa.BackButton.show();
    } else {
      wa.BackButton.hide();
    }
    return () => wa.BackButton.offClick(onBack);
  }, [state.status]);

  return (
    <div className="mx-auto flex min-h-full max-w-md flex-col gap-4 p-4">
      <header className="pt-2">
        <h1 className="text-xl font-semibold">Помощник продавца</h1>
        <p className="text-sm text-[var(--tg-theme-hint-color)]">
          Ozon · Wildberries · Яндекс Маркет
        </p>
      </header>

      {state.status === "loading" && (
        <Card className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Авторизация…</span>
        </Card>
      )}

      {state.status === "error" && (
        <Card className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-red-500">
            <TriangleAlert className="h-5 w-5" />
            <span className="font-medium">Ошибка авторизации</span>
          </div>
          <p className="text-sm text-[var(--tg-theme-hint-color)]">
            {state.message}
          </p>
          <Button variant="secondary" size="sm" onClick={authenticate}>
            Повторить
          </Button>
        </Card>
      )}

      {state.status === "ready" && (
        <Card className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-green-500">
            <ShieldCheck className="h-5 w-5" />
            <span className="font-medium">Авторизация подтверждена</span>
          </div>
          <div className="text-sm">
            <div>
              Вы вошли как{" "}
              <b>
                {state.user.first_name ?? ""} {state.user.last_name ?? ""}
              </b>
              {state.user.username ? ` (@${state.user.username})` : ""}
            </div>
            <div className="text-[var(--tg-theme-hint-color)]">
              telegram_id: {state.user.telegram_id}
            </div>
            {state.isNew && (
              <div className="mt-1 text-[var(--tg-theme-hint-color)]">
                Аккаунт создан только что 🎉
              </div>
            )}
          </div>
        </Card>
      )}

      <footer className="mt-auto pb-2 text-center text-xs text-[var(--tg-theme-hint-color)]">
        Этап 0 — каркас и авторизация
      </footer>
    </div>
  );
}
