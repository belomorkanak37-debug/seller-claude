import { Camera, LineChart as LineChartIcon } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { PriceChart, type ChartSeries } from "@/components/PriceChart";
import { ErrorBanner } from "@/components/ErrorBanner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { getPriceHistory, takePriceSnapshot, type PriceHistory as PH } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { haptic } from "@/lib/telegram";

const COMPETITOR_COLORS = [
  "#ef4444",
  "#f59e0b",
  "#8b5cf6",
  "#10b981",
  "#3b82f6",
];

export function PriceHistory({
  productId,
  productName,
}: {
  productId: number;
  productName: string;
}) {
  const [data, setData] = useState<PH | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [snapping, setSnapping] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setData(await getPriceHistory(productId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить историю");
    }
  }, [productId]);

  useEffect(() => {
    load();
  }, [load]);

  async function snapshotNow() {
    setSnapping(true);
    setMsg(null);
    try {
      const res = await takePriceSnapshot(productId);
      haptic("success");
      setMsg(
        `Снимок сделан: товар ${res.product ? "✓" : "—"}, конкурентов ${res.competitors}`
      );
      await load();
    } catch (e) {
      haptic("error");
      setMsg(e instanceof Error ? e.message : "Не удалось снять цены");
    } finally {
      setSnapping(false);
    }
  }

  const series: ChartSeries[] = data
    ? [
        { label: data.product.label, color: "#2481cc", points: data.product.points },
        ...data.competitors.map((c, i) => ({
          label: c.label,
          color: COMPETITOR_COLORS[i % COMPETITOR_COLORS.length],
          points: c.points,
        })),
      ]
    : [];

  const hasPoints = series.some((s) => s.points.length > 0);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold">История цен</h2>
        <p className="line-clamp-1 text-sm text-[var(--tg-theme-hint-color)]">
          {productName}
        </p>
      </div>

      {error && <ErrorBanner message={error} />}

      <Card className="flex flex-col gap-3">
        {!data ? (
          <div className="flex items-center gap-3 py-6">
            <Spinner /> <span>Загрузка…</span>
          </div>
        ) : hasPoints ? (
          <>
            <PriceChart series={series} />
            <div className="flex flex-col gap-1">
              {series
                .filter((s) => s.points.length > 0)
                .map((s) => (
                  <div key={s.label} className="flex items-center gap-2 text-xs">
                    <span
                      className="inline-block h-2.5 w-2.5 rounded-full"
                      style={{ background: s.color }}
                    />
                    <span className="line-clamp-1 flex-1">{s.label}</span>
                    <span className="text-[var(--tg-theme-hint-color)]">
                      {formatPrice(s.points[s.points.length - 1].price)}
                    </span>
                  </div>
                ))}
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center gap-2 py-6 text-center">
            <LineChartIcon
              className="h-8 w-8"
              color="var(--tg-theme-hint-color)"
            />
            <p className="text-sm text-[var(--tg-theme-hint-color)]">
              Истории пока нет. Цены снимаются автоматически раз в сутки —
              график появится по мере накопления. Можно снять цены прямо сейчас,
              чтобы начать.
            </p>
          </div>
        )}

        {msg && (
          <p className="text-xs text-[var(--tg-theme-hint-color)]">{msg}</p>
        )}

        <Button onClick={snapshotNow} disabled={snapping}>
          {snapping ? <Spinner /> : <Camera className="h-4 w-4" />}
          Снять цены сейчас
        </Button>
      </Card>
    </div>
  );
}
