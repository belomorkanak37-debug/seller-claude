import { Lightbulb, RefreshCw, Search, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  checkPositions,
  getCardComparison,
  getPositions,
  getSeo,
  type CardComparison,
  type PositionItem,
  type SeoResult,
} from "@/lib/api";
import { haptic } from "@/lib/telegram";

export function CardInsights({
  productId,
  productName,
}: {
  productId: number;
  productName: string;
}) {
  const [positions, setPositions] = useState<PositionItem[] | null>(null);
  const [comparison, setComparison] = useState<CardComparison | null>(null);
  const [seo, setSeo] = useState<SeoResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [pos, cmp, s] = await Promise.all([
          getPositions(productId),
          getCardComparison(productId),
          getSeo(productId),
        ]);
        if (!active) return;
        setPositions(pos.latest.length ? pos.latest : pos.queries.map((q) => ({ query: q, position: null })));
        setComparison(cmp);
        setSeo(s);
      } catch (e) {
        if (active)
          setError(e instanceof Error ? e.message : "Не удалось загрузить");
      }
    })();
    return () => {
      active = false;
    };
  }, [productId]);

  async function check() {
    setChecking(true);
    try {
      const r = await checkPositions(productId);
      haptic("success");
      setPositions(r);
    } catch (e) {
      haptic("error");
      setError(e instanceof Error ? e.message : "Не удалось проверить позиции");
    } finally {
      setChecking(false);
    }
  }

  const scoreColor =
    seo && seo.score >= 80
      ? "#059669"
      : seo && seo.score >= 50
        ? "#d97706"
        : "#dc2626";

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold">Карточка и позиции</h2>
        <p className="line-clamp-1 text-sm text-[var(--tg-theme-hint-color)]">
          {productName}
        </p>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* Позиции */}
      <Card className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <Search className="h-4 w-4" /> Позиции в поиске
          </h3>
          <Button variant="ghost" size="sm" onClick={check} disabled={checking}>
            {checking ? <Spinner /> : <RefreshCw className="h-4 w-4" />}
            Проверить
          </Button>
        </div>
        {positions === null ? (
          <Spinner />
        ) : positions.length === 0 ? (
          <p className="text-sm text-[var(--tg-theme-hint-color)]">
            Нет запросов для трекинга.
          </p>
        ) : (
          positions.map((p) => (
            <div key={p.query} className="flex justify-between text-sm">
              <span className="line-clamp-1 text-[var(--tg-theme-hint-color)]">
                {p.query}
              </span>
              <span className="font-medium">
                {p.position != null ? `#${p.position}` : "вне топ-100"}
              </span>
            </div>
          ))
        )}
      </Card>

      {/* Сравнение с конкурентами */}
      {comparison && (
        <Card className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold">Сравнение с конкурентами</h3>
          <CompareRow
            label="Рейтинг"
            mine={comparison.product.rating}
            avg={comparison.competitors_avg.rating}
          />
          <CompareRow
            label="Отзывы"
            mine={comparison.product.reviews_count}
            avg={comparison.competitors_avg.reviews_count}
          />
          <CompareRow
            label="Характеристики"
            mine={comparison.product.tags_count}
            avg={comparison.competitors_avg.tags_count}
          />
          <div className="mt-1 flex flex-col gap-1">
            {comparison.recommendations.map((r, i) => (
              <p
                key={i}
                className="flex gap-1.5 text-xs text-[var(--tg-theme-hint-color)]"
              >
                <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                {r}
              </p>
            ))}
          </div>
        </Card>
      )}

      {/* SEO */}
      {seo && (
        <Card className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-sm font-semibold">
              <Sparkles className="h-4 w-4" /> Оценка карточки
            </h3>
            <span className="text-2xl font-bold" style={{ color: scoreColor }}>
              {seo.score}
              <span className="text-sm font-normal text-[var(--tg-theme-hint-color)]">
                /100
              </span>
            </span>
          </div>

          {seo.suggested_keywords.length > 0 && (
            <div>
              <div className="mb-1 text-xs text-[var(--tg-theme-hint-color)]">
                Ключевые слова конкурентов, которых нет у вас:
              </div>
              <div className="flex flex-wrap gap-1">
                {seo.suggested_keywords.map((k) => (
                  <span
                    key={k}
                    className="rounded-lg bg-[var(--tg-theme-bg-color)] px-2 py-0.5 text-xs"
                  >
                    {k}
                  </span>
                ))}
              </div>
            </div>
          )}

          {seo.tips.length > 0 && (
            <div className="flex flex-col gap-1">
              {seo.tips.map((t, i) => (
                <p
                  key={i}
                  className="flex gap-1.5 text-xs text-[var(--tg-theme-hint-color)]"
                >
                  <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  {t}
                </p>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function CompareRow({
  label,
  mine,
  avg,
}: {
  label: string;
  mine: number;
  avg: number;
}) {
  const better = mine >= avg;
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-[var(--tg-theme-hint-color)]">{label}</span>
      <span>
        <b style={{ color: better ? "#059669" : "#dc2626" }}>{mine}</b>
        <span className="text-[var(--tg-theme-hint-color)]"> / ~{avg}</span>
      </span>
    </div>
  );
}
