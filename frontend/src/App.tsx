import { Loader2, ShieldAlert } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { authTelegram, type Product, type ProductPreview } from "@/lib/api";
import type { MarketplaceId } from "@/lib/api";
import { getWebApp, haptic, isInTelegram } from "@/lib/telegram";
import { AddProduct } from "@/views/AddProduct";
import { Competitors } from "@/views/Competitors";
import { ConfirmProduct } from "@/views/ConfirmProduct";
import { EditProduct } from "@/views/EditProduct";
import { ProductDetail } from "@/views/ProductDetail";
import { ProductsList } from "@/views/ProductsList";
import { Settings } from "@/views/Settings";

type View =
  | { name: "list" }
  | { name: "add" }
  | {
      name: "confirm";
      marketplace: MarketplaceId;
      article: string;
      costPrice: number | null;
      preview: ProductPreview;
    }
  | { name: "detail"; productId: number }
  | { name: "edit"; product: Product }
  | { name: "competitors"; productId: number; productName: string }
  | { name: "settings" };

type AuthState =
  | { status: "loading" }
  | { status: "ok" }
  | { status: "error"; message: string };

export default function App() {
  const [auth, setAuth] = useState<AuthState>({ status: "loading" });
  const [stack, setStack] = useState<View[]>([{ name: "list" }]);
  const [reloadKey, setReloadKey] = useState(0);

  const current = stack[stack.length - 1];

  const push = useCallback((v: View) => setStack((s) => [...s, v]), []);
  const pop = useCallback(
    () => setStack((s) => (s.length > 1 ? s.slice(0, -1) : s)),
    []
  );
  const resetTo = useCallback(
    (v: View) => setStack([v]),
    []
  );

  // ── Авторизация по initData ───────────────────────────────
  const authenticate = useCallback(async () => {
    setAuth({ status: "loading" });
    if (!isInTelegram()) {
      setAuth({
        status: "error",
        message:
          "Откройте приложение через Telegram-бота — нужны данные авторизации Telegram.",
      });
      return;
    }
    try {
      await authTelegram();
      setAuth({ status: "ok" });
    } catch (e) {
      const message = e instanceof Error ? e.message : "Ошибка авторизации";
      setAuth({ status: "error", message });
    }
  }, []);

  useEffect(() => {
    authenticate();
  }, [authenticate]);

  // ── Нативная BackButton Telegram управляет стеком ─────────
  useEffect(() => {
    const wa = getWebApp();
    if (!wa) return;
    const onBack = () => {
      haptic("light");
      pop();
    };
    wa.BackButton.onClick(onBack);
    if (stack.length > 1) wa.BackButton.show();
    else wa.BackButton.hide();
    return () => wa.BackButton.offClick(onBack);
  }, [stack.length, pop]);

  if (auth.status === "loading") {
    return (
      <Screen>
        <Card className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Авторизация…</span>
        </Card>
      </Screen>
    );
  }

  if (auth.status === "error") {
    return (
      <Screen>
        <Card className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-red-500">
            <ShieldAlert className="h-5 w-5" />
            <span className="font-medium">Ошибка авторизации</span>
          </div>
          <p className="text-sm text-[var(--tg-theme-hint-color)]">
            {auth.message}
          </p>
          <Button variant="secondary" size="sm" onClick={authenticate}>
            Повторить
          </Button>
        </Card>
      </Screen>
    );
  }

  return (
    <Screen>
      {current.name === "list" && (
        <ProductsList
          reloadKey={reloadKey}
          onAdd={() => push({ name: "add" })}
          onOpen={(productId) => push({ name: "detail", productId })}
          onSettings={() => push({ name: "settings" })}
        />
      )}

      {current.name === "add" && (
        <AddProduct
          onFound={(marketplace, article, costPrice, preview) =>
            push({ name: "confirm", marketplace, article, costPrice, preview })
          }
        />
      )}

      {current.name === "confirm" && (
        <ConfirmProduct
          marketplace={current.marketplace}
          article={current.article}
          costPrice={current.costPrice}
          preview={current.preview}
          onCancel={pop}
          onConfirmed={(product) => {
            setReloadKey((k) => k + 1);
            // Сбрасываем стек: список → карточка нового товара
            setStack([{ name: "list" }, { name: "detail", productId: product.id }]);
          }}
        />
      )}

      {current.name === "detail" && (
        <ProductDetail
          productId={current.productId}
          onEdit={(product) => push({ name: "edit", product })}
          onCompetitors={(product) =>
            push({
              name: "competitors",
              productId: product.id,
              productName: product.name,
            })
          }
          onDeleted={() => {
            setReloadKey((k) => k + 1);
            resetTo({ name: "list" });
          }}
        />
      )}

      {current.name === "competitors" && (
        <Competitors
          productId={current.productId}
          productName={current.productName}
        />
      )}

      {current.name === "settings" && <Settings />}

      {current.name === "edit" && (
        <EditProduct
          product={current.product}
          onSaved={(updated) => {
            setReloadKey((k) => k + 1);
            // Возврат на карточку с обновлёнными данными
            setStack([
              { name: "list" },
              { name: "detail", productId: updated.id },
            ]);
          }}
        />
      )}
    </Screen>
  );
}

function Screen({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto flex min-h-full max-w-md flex-col gap-4 p-4">
      <header className="pt-1">
        <h1 className="text-xl font-semibold">Помощник продавца</h1>
        <p className="text-sm text-[var(--tg-theme-hint-color)]">
          Ozon · Wildberries · Яндекс Маркет
        </p>
      </header>
      {children}
    </div>
  );
}
