import { Plus, TrendingDown, TrendingUp } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import {
  addAdStat,
  addPayout,
  getAds,
  getPayouts,
  getPnl,
  type AdOverview,
  type PayoutsOverview,
  type PnL,
} from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { haptic } from "@/lib/telegram";

const PAYOUT_LABELS: Record<string, string> = {
  payout: "Выплата",
  fine: "Штраф",
  withholding: "Удержание",
  correction: "Корректировка",
};

export function Finance({
  productId,
  productName,
}: {
  productId: number;
  productName: string;
}) {
  const [ads, setAds] = useState<AdOverview | null>(null);
  const [payouts, setPayouts] = useState<PayoutsOverview | null>(null);
  const [pnl, setPnl] = useState<PnL | null>(null);
  const [units, setUnits] = useState("10");
  const [error, setError] = useState<string | null>(null);

  // формы
  const [ad, setAd] = useState({ label: "", spend: "", revenue: "", clicks: "", orders: "" });
  const [payout, setPayoutForm] = useState({ type: "payout", amount: "", note: "" });
  const [busy, setBusy] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setError(null);
    try {
      const [a, p] = await Promise.all([getAds(productId), getPayouts()]);
      setAds(a);
      setPayouts(p);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить");
    }
  }, [productId]);

  useEffect(() => {
    reload();
  }, [reload]);

  function num(v: string): number {
    const n = Number(v.replace(",", "."));
    return Number.isNaN(n) ? 0 : n;
  }

  async function submitAd() {
    if (!ad.label.trim()) {
      setError("Укажите название кампании/периода");
      return;
    }
    setBusy("ad");
    try {
      await addAdStat(productId, {
        label: ad.label.trim(),
        spend: num(ad.spend),
        revenue: num(ad.revenue),
        clicks: Math.round(num(ad.clicks)),
        orders: Math.round(num(ad.orders)),
      });
      haptic("success");
      setAd({ label: "", spend: "", revenue: "", clicks: "", orders: "" });
      await reload();
    } catch (e) {
      haptic("error");
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(null);
    }
  }

  async function submitPayout() {
    setBusy("payout");
    try {
      await addPayout({
        type: payout.type,
        amount: num(payout.amount),
        note: payout.note.trim() || null,
      });
      haptic("success");
      setPayoutForm({ type: "payout", amount: "", note: "" });
      await reload();
    } catch (e) {
      haptic("error");
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(null);
    }
  }

  async function loadPnl() {
    setBusy("pnl");
    try {
      setPnl(await getPnl(productId, Math.round(num(units))));
      haptic("light");
    } catch (e) {
      haptic("error");
      setError(e instanceof Error ? e.message : "Ошибка P&L");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold">Реклама и финансы</h2>
        <p className="line-clamp-1 text-sm text-[var(--tg-theme-hint-color)]">
          {productName}
        </p>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* Реклама */}
      <Card className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold">Реклама</h3>
        {ads && (
          <div className="grid grid-cols-2 gap-2 text-sm">
            <Metric label="ДРР" value={ads.total.drr != null ? `${ads.total.drr}%` : "—"} />
            <Metric label="ROI" value={ads.total.roi != null ? `${ads.total.roi}%` : "—"} />
            <Metric label="CPO" value={formatPrice(ads.total.cpo)} />
            <Metric label="Расход" value={formatPrice(ads.total.spend)} />
          </div>
        )}
        {ads && (
          <p className="text-xs text-[var(--tg-theme-hint-color)]">
            {ads.total.recommendation}
          </p>
        )}
        <div className="grid grid-cols-2 gap-2">
          <Field label="Кампания/период" value={ad.label} onChange={(v) => setAd({ ...ad, label: v })} />
          <Field label="Расход, ₽" value={ad.spend} onChange={(v) => setAd({ ...ad, spend: v })} />
          <Field label="Выручка, ₽" value={ad.revenue} onChange={(v) => setAd({ ...ad, revenue: v })} />
          <Field label="Клики" value={ad.clicks} onChange={(v) => setAd({ ...ad, clicks: v })} />
          <Field label="Заказы" value={ad.orders} onChange={(v) => setAd({ ...ad, orders: v })} />
        </div>
        <Button size="sm" onClick={submitAd} disabled={busy === "ad"}>
          {busy === "ad" ? <Spinner /> : <Plus className="h-4 w-4" />} Добавить запись
        </Button>
      </Card>

      {/* P&L */}
      <Card className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold">P&L (прибыли и убытки)</h3>
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <Label>Продано, шт</Label>
            <Input inputMode="numeric" value={units} onChange={(e) => setUnits(e.target.value)} />
          </div>
          <Button size="sm" onClick={loadPnl} disabled={busy === "pnl"}>
            {busy === "pnl" ? <Spinner /> : null} Рассчитать
          </Button>
        </div>
        {pnl && (
          <div className="flex flex-col gap-1 text-sm">
            <PnlRow label="Выручка" value={pnl.revenue} />
            <PnlRow label="Себестоимость" value={-pnl.cost_of_goods} />
            <PnlRow label="Издержки МП" value={-pnl.marketplace_costs} />
            <PnlRow label="Реклама" value={-pnl.ad_costs} />
            <PnlRow label="Корректировки" value={pnl.adjustments} />
            <div className="mt-1 flex items-center justify-between border-t border-black/10 pt-1 font-semibold">
              <span className="flex items-center gap-1">
                {pnl.net_profit >= 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-600" />
                )}
                Чистая прибыль
              </span>
              <span className={pnl.net_profit >= 0 ? "text-green-600" : "text-red-600"}>
                {formatPrice(pnl.net_profit)}
                {pnl.margin_pct != null && ` · ${pnl.margin_pct}%`}
              </span>
            </div>
          </div>
        )}
      </Card>

      {/* Выплаты */}
      <Card className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold">Сверка выплат</h3>
        {payouts && (
          <div className="grid grid-cols-2 gap-2 text-sm">
            <Metric label="Выплаты" value={formatPrice(payouts.summary.payout)} />
            <Metric label="Штрафы" value={formatPrice(payouts.summary.fine)} />
            <Metric label="Удержания" value={formatPrice(payouts.summary.withholding)} />
            <Metric label="Корректировки" value={formatPrice(payouts.summary.correction)} />
            <div className="col-span-2 flex justify-between rounded-xl bg-[var(--tg-theme-bg-color)] p-2 font-medium">
              <span>Чистыми</span>
              <span>{formatPrice(payouts.summary.net)}</span>
            </div>
          </div>
        )}
        <div className="grid grid-cols-3 gap-2">
          {Object.entries(PAYOUT_LABELS).map(([k, l]) => (
            <Button
              key={k}
              variant={payout.type === k ? "default" : "secondary"}
              size="sm"
              onClick={() => setPayoutForm({ ...payout, type: k })}
            >
              {l}
            </Button>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Сумма, ₽" value={payout.amount} onChange={(v) => setPayoutForm({ ...payout, amount: v })} />
          <Field label="Комментарий" value={payout.note} onChange={(v) => setPayoutForm({ ...payout, note: v })} />
        </div>
        <Button size="sm" onClick={submitPayout} disabled={busy === "payout"}>
          {busy === "payout" ? <Spinner /> : <Plus className="h-4 w-4" />} Добавить
        </Button>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-[var(--tg-theme-bg-color)] p-2">
      <div className="text-xs text-[var(--tg-theme-hint-color)]">{label}</div>
      <div className="font-medium">{value}</div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <Label>{label}</Label>
      <Input value={value} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}

function PnlRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex justify-between">
      <span className="text-[var(--tg-theme-hint-color)]">{label}</span>
      <span>{formatPrice(value)}</span>
    </div>
  );
}
