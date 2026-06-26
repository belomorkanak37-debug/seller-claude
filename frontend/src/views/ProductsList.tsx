import { Plus, PackageOpen, Settings as SettingsIcon } from "lucide-react";
import { useEffect, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { ProductImage } from "@/components/ProductImage";
import { Stars } from "@/components/Stars";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { listProducts, type Product } from "@/lib/api";
import { formatPrice, marketplaceLabel } from "@/lib/format";
import { haptic } from "@/lib/telegram";

export function ProductsList({
  reloadKey,
  onAdd,
  onOpen,
  onSettings,
}: {
  reloadKey: number;
  onAdd: () => void;
  onOpen: (productId: number) => void;
  onSettings: () => void;
}) {
  const [products, setProducts] = useState<Product[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      setError(null);
      try {
        const list = await listProducts();
        if (active) setProducts(list);
      } catch (e) {
        if (active)
          setError(e instanceof Error ? e.message : "Не удалось загрузить");
      }
    })();
    return () => {
      active = false;
    };
  }, [reloadKey]);

  if (error) return <ErrorBanner message={error} />;
  if (products === null) {
    return (
      <div className="flex items-center gap-3 py-8">
        <Spinner /> <span>Загрузка…</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Мои товары</h2>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              haptic("light");
              onSettings();
            }}
          >
            <SettingsIcon className="h-4 w-4" />
          </Button>
          <Button
            size="sm"
            onClick={() => {
              haptic("light");
              onAdd();
            }}
          >
            <Plus className="h-4 w-4" /> Добавить
          </Button>
        </div>
      </div>

      {products.length === 0 ? (
        <Card className="flex flex-col items-center gap-2 py-8 text-center">
          <PackageOpen className="h-8 w-8 text-[var(--tg-theme-hint-color)]" />
          <p className="text-sm text-[var(--tg-theme-hint-color)]">
            Пока нет товаров. Добавьте первый по артикулу.
          </p>
        </Card>
      ) : (
        <div className="flex flex-col gap-2">
          {products.map((p) => (
            <Card
              key={p.id}
              className="flex cursor-pointer gap-3 active:opacity-80"
              onClick={() => {
                haptic("light");
                onOpen(p.id);
              }}
            >
              <ProductImage
                src={p.photo_url}
                alt={p.name}
                className="h-16 w-16 shrink-0"
              />
              <div className="flex min-w-0 flex-col gap-0.5">
                <span className="text-xs text-[var(--tg-theme-hint-color)]">
                  {marketplaceLabel(p.marketplace)} · {p.article}
                </span>
                <span className="line-clamp-2 text-sm font-medium leading-snug">
                  {p.name}
                </span>
                <div className="flex items-center gap-2">
                  <span className="font-semibold">{formatPrice(p.price)}</span>
                  <Stars rating={p.rating} count={p.reviews_count} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
