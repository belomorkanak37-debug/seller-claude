import { ArrowDown, ArrowUp, Save, Tag, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { Toggle } from "@/components/ui/toggle";
import {
  getRepricer,
  promoCalc,
  saveRepricer,
  type PromoResult,
  type RepriceResult,
} from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { haptic } from "@/lib/telegram";

export function Pricing({
  productId,
  productName,
}: {
  productId: number;
  productName: string;
}) {
  const [data, setData] = useState<RepriceResult | null>(null);
  const [enabled, setEnabled] = useState(false);
  const [undercut, setUndercut] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [discount, setDiscount] = useState("");
  const [promo, setPromo] = useState<PromoResult | null>(null);
  const [promoBusy, setPromoBusy] = useState(false);
  const [promoErr, setPromoErr] = useState<string | null>(null);

  function fill(r: RepriceResult) {
    setEnabled(r.rule.enabled);
    setUndercut(String(r.rule.undercut_pct ?? 0));
    setMinPrice(r.rule.min_price != null ? String(r.rule.min_price) : "");
    setMaxPrice(r.rule.max_price != null ? String(r.rule.max_price) : "");
  }

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const r = await getRepricer(productId);
        if (!active) return;
        setData(r);
        fill(r);
      } catch (e) {
        if (active)
          setError(e instanceof Error ? e.message : "Не удалось загрузить");
      }
    })();
    return () => {
      active = false;
    };
  }, [productId]);

  function num(v: string): number | null {
    if (!v.trim()) return null;
    const n = Number(v.replace(",", "."));
    return Number.isNaN(n) ? null : n;
  }

  async function saveRule() {
    setSaving(true);
    setError(null);
    try {
      const r = await saveRepricer(productId, {
        enabled,
        undercut_pct: num(undercut) ?? 0,
        min_price: num(minPrice),
        max_price: num(maxPrice),
      });
      haptic("success");
      setData(r);
    } catch (e) {
      haptic("error");
      setError(e instanceof Error ? e.message : "Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  }

  async function calcPromo() {
    const d = num(discount);
    if (d == null) {
      setPromoErr("Введите скидку, %");
      return;
    }
    setPromoBusy(true);
    setPromoErr(null);
    try {
      const r = await promoCalc(productId, { discount_pct: d });
      haptic(r.is_profitable ? "success" : "warning");
      setPromo(r);
    } catch (e) {
      haptic("error");
      setPromoErr(e instanceof Error ? e.message : "Ошибка расчёта");
    } finally {
      setPromoBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold">Ценообразование</h2>
        <p className="line-clamp-1 text-sm text-[var(--tg-theme-hint-color)]">
          {productName}
        </p>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* Рекомендация репрайсера */}
      {data && (
        <Card className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold">Рекомендация по цене</h3>
          <Line label="Текущая цена" value={formatPrice(data.current_price)} />
          <Line
            label="Мин. цена конкурента"
            value={formatPrice(data.lowest_competitor)}
          />
          <div className="flex items-center justify-between">
            <span className="text-sm text-[var(--tg-theme-hint-color)]">
              Рекомендуемая
            </span>
            <span className="flex items-center gap-1 text-lg font-bold">
              {data.direction === "down" && (
                <ArrowDown className="h-4 w-4 text-green-600" />
              )}
              {data.direction === "up" && (
                <ArrowUp className="h-4 w-4 text-blue-600" />
              )}
              {formatPrice(data.recommended_price)}
            </span>
          </div>
          <p className="text-xs text-[var(--tg-theme-hint-color)]">
            {data.reason}
            {data.floor_hit && " · упёрлись в минимум"}
          </p>
          {data.break_even_price != null && (
            <p className="text-xs text-[var(--tg-theme-hint-color)]">
              Безубыточность: {formatPrice(data.break_even_price)} — ниже неё уйти
              в минус.
            </p>
          )}
        </Card>
      )}

      {/* Правило */}
      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium">Авто-репрайсер</div>
            <div className="text-xs text-[var(--tg-theme-hint-color)]">
              Ниже конкурента на N%, но не ниже минимума
            </div>
          </div>
          <Toggle checked={enabled} onChange={setEnabled} />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label>Ниже на, %</Label>
            <Input
              inputMode="decimal"
              value={undercut}
              onChange={(e) => setUndercut(e.target.value)}
            />
          </div>
          <div>
            <Label>Мин. цена, ₽</Label>
            <Input
              inputMode="decimal"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
            />
          </div>
          <div>
            <Label>Макс. цена, ₽</Label>
            <Input
              inputMode="decimal"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
            />
          </div>
        </div>
        <Button onClick={saveRule} disabled={saving || !data}>
          {saving ? <Spinner /> : <Save className="h-4 w-4" />}
          Сохранить правило
        </Button>
        <p className="text-xs text-[var(--tg-theme-hint-color)]">
          Цена считается по правилу; применить её нужно в кабинете маркетплейса.
        </p>
      </Card>

      {/* Калькулятор акции */}
      <Card className="flex flex-col gap-3">
        <h3 className="flex items-center gap-2 text-sm font-semibold">
          <Tag className="h-4 w-4" /> Выгода от акции
        </h3>
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <Label>Скидка, %</Label>
            <Input
              inputMode="decimal"
              value={discount}
              onChange={(e) => setDiscount(e.target.value)}
            />
          </div>
          <Button onClick={calcPromo} disabled={promoBusy}>
            {promoBusy ? <Spinner /> : <TrendingUp className="h-4 w-4" />}
            Рассчитать
          </Button>
        </div>
        {promoErr && <ErrorBanner message={promoErr} />}
        {promo && (
          <div className="flex flex-col gap-1 rounded-xl bg-[var(--tg-theme-bg-color)] p-3 text-sm">
            <Line label="Цена по акции" value={formatPrice(promo.promo_price)} />
            <div className="flex justify-between">
              <span className="text-[var(--tg-theme-hint-color)]">
                Прибыль с единицы
              </span>
              <span
                className={
                  "font-semibold " +
                  (promo.is_profitable ? "text-green-600" : "text-red-600")
                }
              >
                {formatPrice(promo.net_profit)}
              </span>
            </div>
            <Line
              label="Изменение прибыли"
              value={`${promo.profit_delta >= 0 ? "+" : ""}${formatPrice(
                promo.profit_delta
              )}`}
            />
            <p className="mt-1 text-xs text-[var(--tg-theme-hint-color)]">
              {promo.is_profitable
                ? "Акция остаётся прибыльной."
                : "При такой скидке товар уходит в минус."}
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}

function Line({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-[var(--tg-theme-hint-color)]">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
