import { Star } from "lucide-react";

import { formatRating } from "@/lib/format";

export function Stars({
  rating,
  count,
}: {
  rating?: number | null;
  count?: number | null;
}) {
  if (rating == null && count == null) return null;
  return (
    <div className="flex items-center gap-1 text-sm">
      <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
      <span className="font-medium">{formatRating(rating)}</span>
      {count != null && (
        <span className="text-[var(--tg-theme-hint-color)]">
          · {count} отзывов
        </span>
      )}
    </div>
  );
}
