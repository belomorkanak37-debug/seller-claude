import { getInitData } from "./telegram";

// По умолчанию ходим на тот же origin через nginx-прокси (/api -> backend).
// Можно переопределить через VITE_API_BASE на этапе сборки.
const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export type MarketplaceId = "wildberries" | "ozon" | "yandex_market";

export interface User {
  id: number;
  telegram_id: number;
  username?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  language_code?: string | null;
  photo_url?: string | null;
  notifications_enabled: boolean;
  notify_new_reviews: boolean;
  notify_stock: boolean;
  registered_at: string;
}

export interface UserSettingsUpdate {
  notifications_enabled?: boolean;
  notify_new_reviews?: boolean;
  notify_stock?: boolean;
}

export interface NotificationItem {
  id: number;
  type: string;
  title?: string | null;
  body?: string | null;
  sent_at: string;
}

export interface ReviewRefreshResult {
  new: number;
  total: number;
  reviews: Review[];
}

export interface AuthResponse {
  user: User;
  is_new: boolean;
}

export interface Review {
  id?: number | null;
  external_id?: string | null;
  source: string;
  author?: string | null;
  text?: string | null;
  rating?: number | null;
  published_at?: string | null;
  sentiment?: string | null;
}

export interface ProductPreview {
  marketplace: string;
  article: string;
  name: string;
  price?: number | null;
  photo_url?: string | null;
  rating?: number | null;
  reviews_count?: number | null;
  tags: string[];
  stock?: number | null;
  url?: string | null;
  brand?: string | null;
  reviews: Review[];
}

export interface Product {
  id: number;
  marketplace: string;
  article: string;
  name: string;
  price?: number | null;
  photo_url?: string | null;
  rating?: number | null;
  reviews_count?: number | null;
  tags?: string[] | null;
  stock?: number | null;
  cost_price?: number | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductUpdate {
  name?: string | null;
  price?: number | null;
  photo_url?: string | null;
  rating?: number | null;
  reviews_count?: number | null;
  tags?: string[] | null;
  stock?: number | null;
  cost_price?: number | null;
  notes?: string | null;
}

export interface CompetitorPreview {
  marketplace: string;
  article?: string | null;
  name: string;
  price?: number | null;
  photo_url?: string | null;
  rating?: number | null;
  reviews_count?: number | null;
  url?: string | null;
}

export interface CompetitorSearchResponse {
  keywords: string[];
  competitors: CompetitorPreview[];
}

export interface Competitor {
  id: number;
  product_id: number;
  marketplace: string;
  article?: string | null;
  url?: string | null;
  name: string;
  photo_url?: string | null;
  price?: number | null;
  rating?: number | null;
  reviews_count?: number | null;
  tags?: string[] | null;
  note?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PricePoint {
  captured_at: string;
  price: number;
}

export interface PriceSeries {
  label: string;
  competitor_id?: number | null;
  points: PricePoint[];
}

export interface PriceHistory {
  product: PriceSeries;
  competitors: PriceSeries[];
}

export interface SnapshotResult {
  product: number;
  competitors: number;
}

export interface EconomicsParams {
  commission_pct: number;
  logistics_cost: number;
  storage_cost: number;
  acquiring_pct: number;
  returns_pct: number;
  tax_pct: number;
}

export interface EconomicsResult {
  price: number;
  cost_price: number;
  params: EconomicsParams;
  breakdown: Record<string, number>;
  total_costs: number;
  net_profit: number;
  margin_pct?: number | null;
  is_profitable: boolean;
}

export interface WarehouseParams {
  daily_sales: number;
  lead_time_days: number;
  target_cover_days: number;
  low_stock_threshold_days: number;
}

export interface WarehouseForecast {
  stock: number;
  daily_sales: number;
  days_left?: number | null;
  recommended_supply: number;
  status: "out" | "critical" | "low" | "ok" | "unknown";
  params: WarehouseParams;
}

export interface RepriceRule {
  enabled: boolean;
  undercut_pct: number;
  min_price?: number | null;
  max_price?: number | null;
}

export interface RepriceResult {
  rule: RepriceRule;
  current_price?: number | null;
  lowest_competitor?: number | null;
  target_price?: number | null;
  recommended_price?: number | null;
  floor?: number | null;
  floor_hit: boolean;
  would_change: boolean;
  direction: "down" | "up" | "none";
  reason: string;
  break_even_price?: number | null;
}

export interface PromoResult {
  base_price: number;
  promo_price: number;
  discount_pct: number;
  net_profit: number;
  margin_pct?: number | null;
  is_profitable: boolean;
  profit_delta: number;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      // Защищённые эндпоинты читают initData отсюда.
      Authorization: `tma ${getInitData()}`,
      ...(options.headers ?? {}),
    },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

/** Авторизация Mini App: отправляем initData, бэкенд валидирует подпись. */
export function authTelegram(): Promise<AuthResponse> {
  return request<AuthResponse>("/auth/telegram", {
    method: "POST",
    body: JSON.stringify({ init_data: getInitData() }),
  });
}

/** Живая карточка по артикулу для экрана «Это ваш товар?» (без сохранения). */
export function lookupProduct(
  marketplace: MarketplaceId,
  article: string
): Promise<ProductPreview> {
  const qs = new URLSearchParams({ marketplace, article });
  return request<ProductPreview>(`/products/lookup?${qs.toString()}`);
}

export function createProduct(
  marketplace: MarketplaceId,
  article: string,
  costPrice?: number | null
): Promise<Product> {
  return request<Product>("/products", {
    method: "POST",
    body: JSON.stringify({
      marketplace,
      article,
      cost_price: costPrice ?? null,
    }),
  });
}

export function listProducts(): Promise<Product[]> {
  return request<Product[]>("/products");
}

export function getProduct(id: number): Promise<Product> {
  return request<Product>(`/products/${id}`);
}

export function getProductReviews(id: number): Promise<Review[]> {
  return request<Review[]>(`/products/${id}/reviews`);
}

export function updateProduct(
  id: number,
  patch: ProductUpdate
): Promise<Product> {
  return request<Product>(`/products/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function deleteProduct(id: number): Promise<void> {
  return request<void>(`/products/${id}`, { method: "DELETE" });
}

// ── Конкуренты ──────────────────────────────────────────────
export function searchCompetitors(
  productId: number
): Promise<CompetitorSearchResponse> {
  return request<CompetitorSearchResponse>(
    `/products/${productId}/competitors/search`
  );
}

export function listCompetitors(productId: number): Promise<Competitor[]> {
  return request<Competitor[]>(`/products/${productId}/competitors`);
}

export function addCompetitor(
  productId: number,
  payload: CompetitorPreview & { note?: string | null }
): Promise<Competitor> {
  return request<Competitor>(`/products/${productId}/competitors`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCompetitorReviews(competitorId: number): Promise<Review[]> {
  return request<Review[]>(`/competitors/${competitorId}/reviews`);
}

export function updateCompetitor(
  competitorId: number,
  patch: { note?: string | null }
): Promise<Competitor> {
  return request<Competitor>(`/competitors/${competitorId}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function deleteCompetitor(competitorId: number): Promise<void> {
  return request<void>(`/competitors/${competitorId}`, { method: "DELETE" });
}

// ── Профиль и уведомления ───────────────────────────────────
export function getMe(): Promise<User> {
  return request<User>("/me");
}

export function updateSettings(patch: UserSettingsUpdate): Promise<User> {
  return request<User>("/me/settings", {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function listNotifications(): Promise<NotificationItem[]> {
  return request<NotificationItem[]>("/notifications");
}

export function refreshProductReviews(
  productId: number
): Promise<ReviewRefreshResult> {
  return request<ReviewRefreshResult>(`/products/${productId}/reviews/refresh`, {
    method: "POST",
  });
}

// ── История цен ─────────────────────────────────────────────
export function getPriceHistory(productId: number): Promise<PriceHistory> {
  return request<PriceHistory>(`/products/${productId}/price-history`);
}

export function takePriceSnapshot(productId: number): Promise<SnapshotResult> {
  return request<SnapshotResult>(`/products/${productId}/price-snapshot`, {
    method: "POST",
  });
}

// ── Юнит-экономика ──────────────────────────────────────────
export function getUnitEconomics(productId: number): Promise<EconomicsResult> {
  return request<EconomicsResult>(`/products/${productId}/unit-economics`);
}

export function saveUnitEconomics(
  productId: number,
  params: EconomicsParams
): Promise<EconomicsResult> {
  return request<EconomicsResult>(`/products/${productId}/unit-economics`, {
    method: "PUT",
    body: JSON.stringify(params),
  });
}

// ── Склад и поставки ────────────────────────────────────────
export function getWarehouse(productId: number): Promise<WarehouseForecast> {
  return request<WarehouseForecast>(`/products/${productId}/warehouse`);
}

export function saveWarehouse(
  productId: number,
  params: WarehouseParams
): Promise<WarehouseForecast> {
  return request<WarehouseForecast>(`/products/${productId}/warehouse`, {
    method: "PUT",
    body: JSON.stringify(params),
  });
}

// ── Ценообразование ─────────────────────────────────────────
export function getRepricer(productId: number): Promise<RepriceResult> {
  return request<RepriceResult>(`/products/${productId}/repricer`);
}

export function saveRepricer(
  productId: number,
  rule: RepriceRule
): Promise<RepriceResult> {
  return request<RepriceResult>(`/products/${productId}/repricer`, {
    method: "PUT",
    body: JSON.stringify(rule),
  });
}

export function promoCalc(
  productId: number,
  input: { discount_pct?: number; promo_price?: number }
): Promise<PromoResult> {
  return request<PromoResult>(`/products/${productId}/promo-calc`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}
