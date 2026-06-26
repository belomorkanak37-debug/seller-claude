import { Save } from "lucide-react";
import { useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { updateProduct, type Product, type ProductUpdate } from "@/lib/api";
import { haptic } from "@/lib/telegram";

export function EditProduct({
  product,
  onSaved,
}: {
  product: Product;
  onSaved: (updated: Product) => void;
}) {
  const [name, setName] = useState(product.name ?? "");
  const [price, setPrice] = useState(product.price?.toString() ?? "");
  const [stock, setStock] = useState(product.stock?.toString() ?? "");
  const [costPrice, setCostPrice] = useState(
    product.cost_price?.toString() ?? ""
  );
  const [photoUrl, setPhotoUrl] = useState(product.photo_url ?? "");
  const [tags, setTags] = useState((product.tags ?? []).join("\n"));
  const [notes, setNotes] = useState(product.notes ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function numOrNull(v: string): number | null {
    const t = v.trim();
    if (!t) return null;
    const n = Number(t.replace(",", "."));
    return Number.isNaN(n) ? null : n;
  }

  async function save() {
    setError(null);
    setSaving(true);
    const patch: ProductUpdate = {
      name: name.trim() || product.name,
      price: numOrNull(price),
      stock: numOrNull(stock),
      cost_price: numOrNull(costPrice),
      photo_url: photoUrl.trim() || null,
      tags: tags
        .split("\n")
        .map((t) => t.trim())
        .filter(Boolean),
      notes: notes.trim() || null,
    };
    try {
      const updated = await updateProduct(product.id, patch);
      haptic("success");
      onSaved(updated);
    } catch (e) {
      haptic("error");
      setError(e instanceof Error ? e.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold">Редактирование товара</h2>

      <div>
        <Label htmlFor="name">Название</Label>
        <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label htmlFor="price">Цена, ₽</Label>
          <Input
            id="price"
            inputMode="decimal"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="stock">Остаток</Label>
          <Input
            id="stock"
            inputMode="numeric"
            value={stock}
            onChange={(e) => setStock(e.target.value)}
          />
        </div>
      </div>

      <div>
        <Label htmlFor="cost">Себестоимость, ₽</Label>
        <Input
          id="cost"
          inputMode="decimal"
          value={costPrice}
          onChange={(e) => setCostPrice(e.target.value)}
        />
      </div>

      <div>
        <Label htmlFor="photo">Ссылка на фото</Label>
        <Input
          id="photo"
          value={photoUrl}
          onChange={(e) => setPhotoUrl(e.target.value)}
        />
      </div>

      <div>
        <Label htmlFor="tags">Теги (по одному на строку)</Label>
        <Textarea
          id="tags"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
        />
      </div>

      <div>
        <Label htmlFor="notes">Заметка</Label>
        <Textarea
          id="notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </div>

      {error && <ErrorBanner message={error} />}

      <Button onClick={save} disabled={saving}>
        {saving ? <Spinner /> : <Save className="h-4 w-4" />} Сохранить
      </Button>
    </div>
  );
}
