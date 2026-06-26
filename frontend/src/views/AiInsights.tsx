import { MessageSquare, Sparkles, ThumbsDown, ThumbsUp, Wand2 } from "lucide-react";
import { useEffect, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  analyzeCompetitorsAi,
  analyzeReviews,
  generateReply,
  getProductReviews,
  type CompetitorAnalysis,
  type Review,
  type ReviewAnalysis,
} from "@/lib/api";
import { haptic } from "@/lib/telegram";

function Bullets({ items }: { items: string[] }) {
  return (
    <ul className="flex flex-col gap-1">
      {items.map((t, i) => (
        <li key={i} className="text-sm text-[var(--tg-theme-hint-color)]">
          • {t}
        </li>
      ))}
    </ul>
  );
}

export function AiInsights({
  productId,
  productName,
}: {
  productId: number;
  productName: string;
}) {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [analysis, setAnalysis] = useState<ReviewAnalysis | null>(null);
  const [competAnalysis, setCompetAnalysis] = useState<CompetitorAnalysis | null>(
    null
  );
  const [replies, setReplies] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getProductReviews(productId)
      .then((r) => active && setReviews(r))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [productId]);

  async function run<T>(key: string, fn: () => Promise<T>, onOk: (v: T) => void) {
    setBusy(key);
    setError(null);
    try {
      onOk(await fn());
      haptic("success");
    } catch (e) {
      haptic("error");
      setError(e instanceof Error ? e.message : "Ошибка AI");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold">AI по отзывам</h2>
        <p className="line-clamp-1 text-sm text-[var(--tg-theme-hint-color)]">
          {productName}
        </p>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* Тональность и жалобы */}
      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <Sparkles className="h-4 w-4" /> Тональность и жалобы
          </h3>
          <Button
            size="sm"
            disabled={busy === "analyze"}
            onClick={() =>
              run("analyze", () => analyzeReviews(productId), setAnalysis)
            }
          >
            {busy === "analyze" ? <Spinner /> : <Wand2 className="h-4 w-4" />}
            Анализ
          </Button>
        </div>
        {analysis && (
          <div className="flex flex-col gap-2">
            <div className="flex gap-2 text-sm">
              <span className="rounded-lg bg-green-500/15 px-2 py-0.5 text-green-600">
                + {analysis.sentiment.positive}
              </span>
              <span className="rounded-lg bg-black/10 px-2 py-0.5">
                ~ {analysis.sentiment.neutral}
              </span>
              <span className="rounded-lg bg-red-500/15 px-2 py-0.5 text-red-600">
                − {analysis.sentiment.negative}
              </span>
            </div>
            {analysis.common_complaints.length > 0 && (
              <div>
                <div className="text-xs font-medium">Частые жалобы</div>
                <Bullets items={analysis.common_complaints} />
              </div>
            )}
            {analysis.suggestions.length > 0 && (
              <div>
                <div className="text-xs font-medium">Рекомендации</div>
                <Bullets items={analysis.suggestions} />
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Конкуренты */}
      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">Отзывы конкурентов</h3>
          <Button
            size="sm"
            disabled={busy === "compet"}
            onClick={() =>
              run("compet", () => analyzeCompetitorsAi(productId), setCompetAnalysis)
            }
          >
            {busy === "compet" ? <Spinner /> : <Wand2 className="h-4 w-4" />}
            Анализ
          </Button>
        </div>
        {competAnalysis && (
          <div className="flex flex-col gap-2">
            {competAnalysis.praise.length > 0 && (
              <div>
                <div className="flex items-center gap-1 text-xs font-medium text-green-600">
                  <ThumbsUp className="h-3.5 w-3.5" /> Хвалят
                </div>
                <Bullets items={competAnalysis.praise} />
              </div>
            )}
            {competAnalysis.criticism.length > 0 && (
              <div>
                <div className="flex items-center gap-1 text-xs font-medium text-red-600">
                  <ThumbsDown className="h-3.5 w-3.5" /> Ругают
                </div>
                <Bullets items={competAnalysis.criticism} />
              </div>
            )}
            {competAnalysis.differentiation.length > 0 && (
              <div>
                <div className="text-xs font-medium">Чем выделиться</div>
                <Bullets items={competAnalysis.differentiation} />
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Ответы на отзывы */}
      <Card className="flex flex-col gap-3">
        <h3 className="flex items-center gap-2 text-sm font-semibold">
          <MessageSquare className="h-4 w-4" /> Ответы на отзывы
        </h3>
        {reviews.length === 0 ? (
          <p className="text-sm text-[var(--tg-theme-hint-color)]">
            Нет отзывов. Обновите отзывы в карточке товара.
          </p>
        ) : (
          reviews.slice(0, 10).map((r) => (
            <div
              key={r.id}
              className="rounded-xl bg-[var(--tg-theme-bg-color)] p-2"
            >
              <div className="mb-1 flex items-center justify-between">
                <span className="text-xs font-medium">
                  {r.author ?? "Покупатель"} · {r.rating ?? "—"}★
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={busy === `reply-${r.id}`}
                  onClick={() =>
                    r.id &&
                    run(
                      `reply-${r.id}`,
                      () => generateReply(r.id as number),
                      (v) =>
                        setReplies((prev) => ({ ...prev, [r.id as number]: v.reply }))
                    )
                  }
                >
                  {busy === `reply-${r.id}` ? (
                    <Spinner />
                  ) : (
                    <Wand2 className="h-4 w-4" />
                  )}
                  Ответ
                </Button>
              </div>
              {r.text && (
                <p className="line-clamp-2 text-sm text-[var(--tg-theme-hint-color)]">
                  {r.text}
                </p>
              )}
              {r.id && replies[r.id] && (
                <p className="mt-2 whitespace-pre-line rounded-lg bg-[var(--tg-theme-secondary-bg-color)] p-2 text-sm">
                  {replies[r.id]}
                </p>
              )}
            </div>
          ))
        )}
      </Card>
    </div>
  );
}
