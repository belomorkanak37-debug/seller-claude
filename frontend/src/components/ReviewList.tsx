import { Star } from "lucide-react";

import type { Review } from "@/lib/api";
import { formatDate } from "@/lib/format";

export function ReviewList({ reviews }: { reviews: Review[] }) {
  if (reviews.length === 0) {
    return (
      <p className="text-sm text-[var(--tg-theme-hint-color)]">
        Отзывов пока нет.
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-3">
      {reviews.map((r, i) => (
        <div
          key={r.id ?? r.external_id ?? i}
          className="rounded-xl bg-[var(--tg-theme-bg-color)] p-3"
        >
          <div className="mb-1 flex items-center justify-between">
            <span className="text-sm font-medium">
              {r.author ?? "Покупатель"}
            </span>
            <span className="flex items-center gap-1 text-sm">
              <Star className="h-3.5 w-3.5 fill-yellow-400 text-yellow-400" />
              {r.rating ?? "—"}
            </span>
          </div>
          {r.text && <p className="whitespace-pre-line text-sm">{r.text}</p>}
          {r.published_at && (
            <p className="mt-1 text-xs text-[var(--tg-theme-hint-color)]">
              {formatDate(r.published_at)}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
