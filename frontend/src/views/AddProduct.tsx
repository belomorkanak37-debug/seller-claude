import { Search } from "lucide-react";
import { useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import {
  lookupProduct,
  type MarketplaceId,
  type ProductPreview,
} from "@/lib/api";
import { MARKETPLACES } from "@/lib/format";
import { haptic } from "@/lib/telegram";

export function AddProduct({
  onFound,
}: {
  onFound: (
    marketplace: MarketplaceId,
    article: string,
    costPrice: number | null,
    preview: ProductPreview
  ) => void;
}) {
  const [marketplace, setMarketplace] = useState<MarketplaceId>("wildberries");
  const [article, setArticle] = useState("");
  const [costPrice, setCostPrice] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSearch() {
    setError(null);
    const trimmed = article.trim();
    if (!trimmed) {
      setError("Введите артикул товара");
      return;
    }
    setLoading(true);
    try {
      const preview = await lookupProduct(marketplace, trimmed);
      haptic("success");
      onFound(
        marketplace,
        trimmed,
        costPrice ? Number(costPrice) : null,
        preview
      );
    } catch (e) {
      haptic("error");
      setError(e instanceof Error ? e.message : "Не удалось найти товар");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold">Добавить товар</h2>

      <div>
        <Label>Маркетплейс</Label>
        <div className="grid grid-cols-3 gap-2">
          {MARKETPLACES.map((m) => (
            <Button
              key={m.id}
              variant={marketplace === m.id ? "default" : "secondary"}
              size="sm"
              onClick={() => {
                haptic("light");
                setMarketplace(m.id);
              }}
            >
              {m.label}
            </Button>
          ))}
        </div>
        {marketplace !== "wildberries" && (
          <p className="mt-1 text-xs text-[var(--tg-theme-hint-color)]">
            Ozon и Яндекс Маркет подключаются на следующем этапе. Сейчас
            доступен Wildberries.
          </p>
        )}
      </div>

      <div>
        <Label htmlFor="article">Артикул</Label>
        <Input
          id="article"
          inputMode="numeric"
          placeholder="например, 179770725"
          value={article}
          onChange={(e) => setArticle(e.target.value)}
        />
      </div>

      <div>
        <Label htmlFor="cost">Себестоимость, ₽ (необязательно)</Label>
        <Input
          id="cost"
          inputMode="decimal"
          placeholder="для юнит-экономики"
          value={costPrice}
          onChange={(e) => setCostPrice(e.target.value)}
        />
      </div>

      {error && <ErrorBanner message={error} />}

      <Button onClick={onSearch} disabled={loading}>
        {loading ? <Spinner /> : <Search className="h-4 w-4" />}
        Найти товар
      </Button>
    </div>
  );
}
