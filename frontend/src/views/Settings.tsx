import { Bell } from "lucide-react";
import { useEffect, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Toggle } from "@/components/ui/toggle";
import {
  getMe,
  listNotifications,
  updateSettings,
  type NotificationItem,
  type User,
} from "@/lib/api";
import { formatDate } from "@/lib/format";
import { haptic } from "@/lib/telegram";

export function Settings() {
  const [user, setUser] = useState<User | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [me, notes] = await Promise.all([getMe(), listNotifications()]);
        if (!active) return;
        setUser(me);
        setNotifications(notes);
      } catch (e) {
        if (active)
          setError(e instanceof Error ? e.message : "Не удалось загрузить");
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  async function patch(field: "notifications_enabled" | "notify_new_reviews", value: boolean) {
    if (!user) return;
    haptic("light");
    setSaving(true);
    const prev = user;
    setUser({ ...user, [field]: value }); // оптимистично
    try {
      const updated = await updateSettings({ [field]: value });
      setUser(updated);
    } catch (e) {
      setUser(prev);
      setError(e instanceof Error ? e.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  if (error && !user) return <ErrorBanner message={error} />;
  if (!user) {
    return (
      <div className="flex items-center gap-3 py-8">
        <Spinner /> <span>Загрузка…</span>
      </div>
    );
  }

  const master = user.notifications_enabled;

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold">Настройки</h2>

      <Card className="flex flex-col gap-4">
        <Row
          title="Уведомления"
          subtitle="Главный выключатель всех уведомлений"
          checked={master}
          disabled={saving}
          onChange={(v) => patch("notifications_enabled", v)}
        />
        <Row
          title="Новые отзывы"
          subtitle="Сообщать при появлении новых отзывов по товару"
          checked={user.notify_new_reviews && master}
          disabled={saving || !master}
          onChange={(v) => patch("notify_new_reviews", v)}
        />
      </Card>

      {error && <ErrorBanner message={error} />}

      <section>
        <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold">
          <Bell className="h-4 w-4" /> История уведомлений
        </h3>
        {notifications.length === 0 ? (
          <p className="text-sm text-[var(--tg-theme-hint-color)]">
            Уведомлений пока не было.
          </p>
        ) : (
          <div className="flex flex-col gap-2">
            {notifications.map((n) => (
              <Card key={n.id} className="flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{n.title ?? n.type}</span>
                  <span className="text-xs text-[var(--tg-theme-hint-color)]">
                    {formatDate(n.sent_at)}
                  </span>
                </div>
                {n.body && (
                  <p className="line-clamp-3 whitespace-pre-line text-sm text-[var(--tg-theme-hint-color)]">
                    {n.body}
                  </p>
                )}
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function Row({
  title,
  subtitle,
  checked,
  disabled,
  onChange,
}: {
  title: string;
  subtitle: string;
  checked: boolean;
  disabled?: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <div className="min-w-0">
        <div className="text-sm font-medium">{title}</div>
        <div className="text-xs text-[var(--tg-theme-hint-color)]">{subtitle}</div>
      </div>
      <Toggle checked={checked} onChange={onChange} disabled={disabled} />
    </div>
  );
}
