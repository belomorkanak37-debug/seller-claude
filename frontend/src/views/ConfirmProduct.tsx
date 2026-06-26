import { Check, X } from "lucide-react";
import { useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { ProductImage } from "@/components/ProductImage";
import { ReviewList } from "@/components/ReviewList";
import { Stars } from "@/components/Stars";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  createProduct,
  type MarketplaceId,
  type Product,
  type ProductPreview,
} from "@/lib/api";
import { formatPrice, marketplaceLabel } from "@/lib/format";
import { haptic } from "@/lib/telegram";

export function ConfirmProduct({
  marketplace,
  article,
  costPrice,
  preview,
  onConfirmed,
  onCancel,
}: {
  marketplace: MarketplaceId;
  article: string;
  costPrice: number | null;
  preview: ProductPreview;
  onConfirmed: (product: Product) => void;
  onCancel: () => void;
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function confirm() {
    setError(null);
    setSaving(true);
    try {
      const product = await createProduct(marketplace, article, costPrice);
      haptic("success");
      onConfirmed(product);
    } catch (e) {
      haptic("error");
      setError(e instanceof Error ? e.message : "Не удалось сохранить товар");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold">Это ваш товар?</h2>

      <Card className="flex flex-col gap-3">
        <div className="flex gap-3">
          <ProductImage
            src={preview.photo_url}
            alt={preview.name}
            className="h-24 w-24 shrink-0"
          />
          <div className="flex flex-col gap-1">
            <span className="text-xs text-[var(--tg-theme-hint-color)]">
              {marketplaceLabel(preview.marketplace)} · {preview.article}
              {preview.brand ? ` · ${preview.brand}` : ""}
            </span>
            <span className="text-sm font-medium leading-snug">
              {preview.name}
            </span>
            <span className="text-lg font-semibold">
              {formatPrice(preview.price)}
            </span>
            <Stars rating={preview.rating} count={preview.reviews_count} />
          </div>
        </div>

        {preview.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {preview.tags.slice(0, 8).map((t, i) => (
              <span
                key={i}
                className="rounded-lg bg-[var(--tg-theme-bg-color)] px-2 py-0.5 text-xs text-[var(--tg-theme-hint-color)]"
              >
                {t}
              </span>
            ))}
          </div>
        )}
      </Card>

      <div>
        <h3 className="mb-2 text-sm font-semibold">
          Отзывы покупателей{" "}
          {preview.reviews.length > 0 && `(${preview.reviews.length})`}
        </h3>
        <ReviewList reviews={preview.reviews.slice(0, 10)} />
      </div>

      {error && <ErrorBanner message={error} />}

      <div className="grid grid-cols-2 gap-2">
        <Button variant="secondary" onClick={onCancel} disabled={saving}>
          <X className="h-4 w-4" />
          Не он
        </Button>
        <Button onClick={confirm} disabled={saving}>
          {saving ? <Spinner /> : <Check className="h-4 w-4" />}
          Это мой товар
        </Button>
      </div>
    </div>
  );
}
