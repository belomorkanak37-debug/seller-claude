import { PackageCheck, Save, TruckIcon } from "lucide-react";
import { useEffect, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import {
  getWarehouse,
  saveWarehouse,
  type WarehouseForecast,
  type WarehouseParams,
} from "@/lib/api";
import { haptic } from "@/lib/telegram";

const STATUS: Record<
  WarehouseForecast["status"],
  { label: string; bg: string; color: string }
> = {
  ok: { label: "В норме", bg: "rgba(16,185,129,0.12)", color: "#059669" },
  low: { label: "Низкий остаток", bg: "rgba(245,158,11,0.14)", color: "#d97706" },
  critical: { label: "Критично", bg: "rgba(239,68,68,0.14)", color: "#dc2626" },
  out: { label: "Закончился", bg: "rgba(239,68,68,0.18)", color: "#dc2626" },
  unknown: { label: "Нет данных о продажах", bg: "rgba(0,0,0,0.06)", color: "inherit" },
};

const FIELDS: { key: keyof WarehouseParams; label: string }[] = [
  { key: "daily_sales", label: "Продаж в день, шт" },
  { key: "lead_time_days", label: "Срок поставки, дн" },
  { key: "target_cover_days", label: "Целевой запас, дн" },
  { key: "low_stock_threshold_days", label: "Порог алерта, дн" },
];

export function Warehouse({
  productId,
  productName,
}: {
  productId: number;
  productName: string;
}) {
  const [data, setData] = useState<WarehouseForecast | null>(null);
  const [form, setForm] = useState<Record<keyof WarehouseParams, string>>({
    daily_sales: "",
    lead_time_days: "",
    target_cover_days: "",
    low_stock_threshold_days: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function fill(p: WarehouseParams) {
    setForm({
      daily_sales: String(p.daily_sales ?? 0),
      lead_time_days: String(p.lead_time_days ?? 14),
      target_cover_days: String(p.target_cover_days ?? 30),
      low_stock_threshold_days: String(p.low_stock_threshold_days ?? 7),
    });
  }

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const r = await getWarehouse(productId);
        if (!active) return;
        setData(r);
        fill(r.params);
      } catch (e) {
        if (active)
          setError(e instanceof Error ? e.message : "Не удалось загрузить");
      }
    })();
    return () => {
      active = false;
    };
  }, [productId]);

  function num(v: string): number {
    const n = Number(v.replace(",", "."));
    return Number.isNaN(n) ? 0 : n;
  }

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const params: WarehouseParams = {
        daily_sales: num(form.daily_sales),
        lead_time_days: Math.round(num(form.lead_time_days)),
        target_cover_days: Math.round(num(form.target_cover_days)),
        low_stock_threshold_days: Math.round(num(form.low_stock_threshold_days)),
      };
      const r = await saveWarehouse(productId, params);
      haptic(r.status === "ok" || r.status === "unknown" ? "success" : "warning");
      setData(r);
    } catch (e) {
      haptic("error");
      setError(e instanceof Error ? e.message : "Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  }

  const st = data ? STATUS[data.status] : null;

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold">Склад и поставки</h2>
        <p className="line-clamp-1 text-sm text-[var(--tg-theme-hint-color)]">
          {productName}
        </p>
      </div>

      {error && <ErrorBanner message={error} />}

      {data && st && (
        <Card className="flex flex-col gap-3" style={{ background: st.bg }}>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2 font-semibold">
              <PackageCheck className="h-5 w-5" /> Остаток
            </span>
            <span className="text-lg font-bold">{data.stock} шт</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-[var(--tg-theme-hint-color)]">Статус</span>
            <span className="font-medium" style={{ color: st.color }}>
              {st.label}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-[var(--tg-theme-hint-color)]">
              Хватит на
            </span>
            <span className="font-medium">
              {data.days_left != null ? `${data.days_left} дн.` : "—"}
            </span>
          </div>
          {data.recommended_supply > 0 && (
            <div className="flex items-center justify-between rounded-xl bg-[var(--tg-theme-bg-color)] p-2 text-sm">
              <span className="flex items-center gap-2">
                <TruckIcon className="h-4 w-4" /> Рекомендуем отгрузить
              </span>
              <span className="font-semibold">
                {data.recommended_supply} шт
              </span>
            </div>
          )}
        </Card>
      )}

      <Card className="flex flex-col gap-3">
        <h3 className="text-sm font-semibold">Параметры</h3>
        <div className="grid grid-cols-2 gap-2">
          {FIELDS.map((f) => (
            <div key={f.key}>
              <Label>{f.label}</Label>
              <Input
                inputMode="decimal"
                value={form[f.key]}
                onChange={(e) =>
                  setForm((s) => ({ ...s, [f.key]: e.target.value }))
                }
              />
            </div>
          ))}
        </div>
        <p className="text-xs text-[var(--tg-theme-hint-color)]">
          Остаток берётся из карточки маркетплейса. Укажите среднюю скорость
          продаж, чтобы получить прогноз и рекомендацию по отгрузке.
        </p>
      </Card>

      <Button onClick={save} disabled={saving || !data}>
        {saving ? <Spinner /> : <Save className="h-4 w-4" />}
        Сохранить и рассчитать
      </Button>
    </div>
  );
}
