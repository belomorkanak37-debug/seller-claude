export function formatPrice(value?: number | null): string {
  if (value == null) return "—";
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatRating(value?: number | null): string {
  if (value == null) return "—";
  return value.toFixed(1);
}

export function formatDate(value?: string | null): string {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export const MARKETPLACES: { id: "wildberries" | "ozon" | "yandex_market"; label: string }[] = [
  { id: "wildberries", label: "Wildberries" },
  { id: "ozon", label: "Ozon" },
  { id: "yandex_market", label: "Яндекс Маркет" },
];

export function marketplaceLabel(id: string): string {
  return MARKETPLACES.find((m) => m.id === id)?.label ?? id;
}

/** Ссылка на карточку товара на маркетплейсе по артикулу. */
export function marketplaceProductUrl(
  marketplace: string,
  article: string
): string | null {
  switch (marketplace) {
    case "wildberries":
      return `https://www.wildberries.ru/catalog/${article}/detail.aspx`;
    case "ozon":
      return `https://www.ozon.ru/product/${article}`;
    case "yandex_market":
      return `https://market.yandex.ru/product/${article}`;
    default:
      return null;
  }
}
