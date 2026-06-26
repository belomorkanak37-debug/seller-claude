import {
  ExternalLink,
  LineChart,
  Pencil,
  RefreshCw,
  Trash2,
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { ProductImage } from "@/components/ProductImage";
import { ReviewList } from "@/components/ReviewList";
import { Stars } from "@/components/Stars";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  deleteProduct,
  getProduct,
  getProductReviews,
  refreshProductReviews,
  type Product,
  type Review,
} from "@/lib/api";
import {
  formatPrice,
  marketplaceLabel,
  marketplaceProductUrl,
} from "@/lib/format";
import { haptic } from "@/lib/telegram";

export function ProductDetail({
  productId,
  onEdit,
  onDeleted,
  onCompetitors,
  onPriceHistory,
}: {
  productId: number;
  onEdit: (product: Product) => void;
  onDeleted: () => void;
  onCompetitors: (product: Product) => void;
  onPriceHistory: (product: Product) => void;
}) {
  const [product, setProduct] = useState<Product | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [refreshingReviews, setRefreshingReviews] = useState(false);
  const [reviewsMsg, setReviewsMsg] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [p, r] = await Promise.all([
          getProduct(productId),
          getProductReviews(productId),
        ]);
        if (!active) return;
        setProduct(p);
        setReviews(r);
      } catch (e) {
        if (!active) return;
        setError(e instanceof Error ? e.message : "Не удалось загрузить товар");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [productId]);

  async function onDelete() {
    haptic("warning");
    const wa = window.Telegram?.WebApp as
      | (TelegramWebApp & { showConfirm?: (m: string, cb: (ok: boolean) => void) => void })
      | undefined;
    const confirmed = await new Promise<boolean>((resolve) => {
      if (wa?.showConfirm) {
        wa.showConfirm("Удалить товар?", resolve);
      } else {
        resolve(window.confirm("Удалить товар?"));
      }
    });
    if (!confirmed) return;
    setDeleting(true);
    try {
      await deleteProduct(productId);
      haptic("success");
      onDeleted();
    } catch (e) {
      haptic("error");
      setError(e instanceof Error ? e.message : "Не удалось удалить");
      setDeleting(false);
    }
  }

  async function onRefreshReviews() {
    setRefreshingReviews(true);
    setReviewsMsg(null);
    try {
      const res = await refreshProductReviews(productId);
      setReviews(res.reviews);
      haptic(res.new > 0 ? "success" : "light");
      setReviewsMsg(
        res.new > 0 ? `Новых отзывов: ${res.new}` : "Новых отзывов нет"
      );
    } catch (e) {
      haptic("error");
      setReviewsMsg(e instanceof Error ? e.message : "Не удалось обновить");
    } finally {
      setRefreshingReviews(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-3 py-8">
        <Spinner /> <span>Загрузка…</span>
      </div>
    );
  }
  if (error && !product) return <ErrorBanner message={error} />;
  if (!product) return null;

  return (
    <div className="flex flex-col gap-4">
      <Card className="flex flex-col gap-3">
        <div className="flex gap-3">
          <ProductImage
            src={product.photo_url}
            alt={product.name}
            className="h-24 w-24 shrink-0"
          />
          <div className="flex flex-col gap-1">
            <span className="text-xs text-[var(--tg-theme-hint-color)]">
              {marketplaceLabel(product.marketplace)} · {product.article}
            </span>
            <span className="text-sm font-medium leading-snug">
              {product.name}
            </span>
            <span className="text-lg font-semibold">
              {formatPrice(product.price)}
            </span>
            <Stars rating={product.rating} count={product.reviews_count} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-sm">
          <Info label="Остаток" value={product.stock?.toString() ?? "—"} />
          <Info label="Себестоимость" value={formatPrice(product.cost_price)} />
        </div>

        {product.tags && product.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {product.tags.slice(0, 12).map((t, i) => (
              <span
                key={i}
                className="rounded-lg bg-[var(--tg-theme-bg-color)] px-2 py-0.5 text-xs text-[var(--tg-theme-hint-color)]"
              >
                {t}
              </span>
            ))}
          </div>
        )}

        {product.notes && (
          <p className="rounded-xl bg-[var(--tg-theme-bg-color)] p-2 text-sm">
            📝 {product.notes}
          </p>
        )}

        {marketplaceProductUrl(product.marketplace, product.article) && (
          <a
            href={marketplaceProductUrl(product.marketplace, product.article)!}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-sm text-[var(--tg-theme-link-color)]"
          >
            <ExternalLink className="h-4 w-4" /> Открыть на маркетплейсе
          </a>
        )}
      </Card>

      {error && <ErrorBanner message={error} />}

      <div className="grid grid-cols-2 gap-2">
        <Button onClick={() => onCompetitors(product)}>
          <Users className="h-4 w-4" /> Конкуренты
        </Button>
        <Button onClick={() => onPriceHistory(product)}>
          <LineChart className="h-4 w-4" /> История цен
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Button variant="secondary" onClick={() => onEdit(product)}>
          <Pencil className="h-4 w-4" /> Редактировать
        </Button>
        <Button variant="secondary" onClick={onDelete} disabled={deleting}>
          {deleting ? <Spinner /> : <Trash2 className="h-4 w-4" />} Удалить
        </Button>
      </div>

      <div>
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold">
            Отзывы {reviews.length > 0 && `(${reviews.length})`}
          </h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={onRefreshReviews}
            disabled={refreshingReviews}
          >
            {refreshingReviews ? (
              <Spinner />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Обновить
          </Button>
        </div>
        {reviewsMsg && (
          <p className="mb-2 text-xs text-[var(--tg-theme-hint-color)]">
            {reviewsMsg}
          </p>
        )}
        <ReviewList reviews={reviews} />
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-[var(--tg-theme-bg-color)] p-2">
      <div className="text-xs text-[var(--tg-theme-hint-color)]">{label}</div>
      <div className="font-medium">{value}</div>
    </div>
  );
}
