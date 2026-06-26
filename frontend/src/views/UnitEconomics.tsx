import { Calculator, TrendingDown, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import {
  getUnitEconomics,
  saveUnitEconomics,
  type EconomicsParams,
  type EconomicsResult,
} from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { haptic } from "@/lib/telegram";

const FIELDS: {
  key: keyof EconomicsParams;
  label: string;
  unit: "%" | "₽";
}[] = [
  { key: "commission_pct", label: "Комиссия МП", unit: "%" },
  { key: "acquiring_pct", label: "Эквайринг", unit: "%" },
  { key: "tax_pct", label: "Налог", unit: "%" },
  { key: "returns_pct", label: "Возвраты", unit: "%" },
  { key: "logistics_cost", label: "Логистика", unit: "₽" },
  { key: "storage_cost", label: "Хранение", unit: "₽" },
];

const BREAKDOWN_LABELS: Record<string, string> = {
  cost_price: "Себестоимость",
  commission: "Комиссия МП",
  acquiring: "Эквайринг",
  tax: "Налог",
  returns: "Возвраты",
  logistics: "Логистика",
  storage: "Хранение",
};

export function UnitEconomics({
  productId,
  productName,
}: {
  productId: number;
  productName: string;
}) {
  const [result, setResult] = useState<EconomicsResult | null>(null);
  const [form, setForm] = useState<Record<keyof EconomicsParams, string>>({
    commission_pct: "",
    acquiring_pct: "",
    tax_pct: "",
    returns_pct: "",
    logistics_cost: "",
    storage_cost: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function fillForm(p: EconomicsParams) {
    setForm({
      commission_pct: String(p.commission_pct ?? 0),
      acquiring_pct: String(p.acquiring_pct ?? 0),
      tax_pct: String(p.tax_pct ?? 0),
      returns_pct: String(p.returns_pct ?? 0),
      logistics_cost: String(p.logistics_cost ?? 0),
      storage_cost: String(p.storage_cost ?? 0),
    });
  }

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const r = await getUnitEconomics(productId);
        if (!active) return;
        setResult(r);
        fillForm(r.params);
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

  async function calculate() {
    setSaving(true);
    setError(null);
    try {
      const params: EconomicsParams = {
        commission_pct: num(form.commission_pct),
        acquiring_pct: num(form.acquiring_pct),
        tax_pct: num(form.tax_pct),
        returns_pct: num(form.returns_pct),
        logistics_cost: num(form.logistics_cost),
        storage_cost: num(form.storage_cost),
      };
      const r = await saveUnitEconomics(productId, params);
      haptic(r.is_profitable ? "success" : "warning");
      setResult(r);
    } catch (e) {
      haptic("error");
      setError(e instanceof Error ? e.message : "Ошибка расчёта");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold">Юнит-экономика</h2>
        <p className="line-clamp-1 text-sm text-[var(--tg-theme-hint-color)]">
          {productName}
        </p>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* Итог */}
      {result && (
        <Card
          className="flex flex-col gap-2"
          style={{
            background: result.is_profitable
              ? "rgba(16,185,129,0.12)"
              : "rgba(239,68,68,0.12)",
          }}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm text-[var(--tg-theme-hint-color)]">
              Цена продажи
            </span>
            <span className="font-medium">{formatPrice(result.price)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2 font-semibold">
              {result.is_profitable ? (
                <TrendingUp className="h-5 w-5 text-green-600" />
              ) : (
                <TrendingDown className="h-5 w-5 text-red-600" />
              )}
              Чистая прибыль
            </span>
            <span
              className={
                "text-lg font-bold " +
                (result.is_profitable ? "text-green-600" : "text-red-600")
              }
            >
              {formatPrice(result.net_profit)}
            </span>
          </div>
          <div className="text-right text-xs text-[var(--tg-theme-hint-color)]">
            {result.is_profitable ? "В плюсе" : "В минусе"}
            {result.margin_pct != null && ` · маржа ${result.margin_pct}%`}
          </div>
        </Card>
      )}

      {/* Разбивка */}
      {result && (
        <Card className="flex flex-col gap-1">
          <h3 className="mb-1 text-sm font-semibold">Структура затрат</h3>
          {Object.entries(result.breakdown).map(([k, v]) => (
            <div key={k} className="flex justify-between text-sm">
              <span className="text-[var(--tg-theme-hint-color)]">
                {BREAKDOWN_LABELS[k] ?? k}
              </span>
              <span>{formatPrice(v)}</span>
            </div>
          ))}
          <div className="mt-1 flex justify-between border-t border-black/10 pt-1 text-sm font-medium">
            <span>Итого затрат</span>
            <span>{formatPrice(result.total_costs)}</span>
          </div>
          {result.cost_price === 0 && (
            <p className="mt-1 text-xs text-[var(--tg-theme-hint-color)]">
              Себестоимость не задана — укажите её в редактировании товара для
              точного расчёта.
            </p>
          )}
        </Card>
      )}

      {/* Параметры */}
      <Card className="flex flex-col gap-3">
        <h3 className="text-sm font-semibold">Параметры</h3>
        <div className="grid grid-cols-2 gap-2">
          {FIELDS.map((f) => (
            <div key={f.key}>
              <Label>
                {f.label}, {f.unit}
              </Label>
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
      </Card>

      <Button onClick={calculate} disabled={saving || !result}>
        {saving ? <Spinner /> : <Calculator className="h-4 w-4" />}
        Рассчитать и сохранить
      </Button>
    </div>
  );
}
