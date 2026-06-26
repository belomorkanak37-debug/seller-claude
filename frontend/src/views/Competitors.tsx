import { ChevronDown, ChevronUp, Plus, Save, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { ErrorBanner } from "@/components/ErrorBanner";
import { ProductImage } from "@/components/ProductImage";
import { ReviewList } from "@/components/ReviewList";
import { Stars } from "@/components/Stars";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import {
  addCompetitor,
  deleteCompetitor,
  getCompetitorReviews,
  listCompetitors,
  searchCompetitors,
  updateCompetitor,
  type Competitor,
  type CompetitorPreview,
  type Review,
} from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { haptic } from "@/lib/telegram";

export function Competitors({
  productId,
  productName,
}: {
  productId: number;
  productName: string;
}) {
  const [saved, setSaved] = useState<Competitor[]>([]);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<CompetitorPreview[]>([]);
  const [loadingSaved, setLoadingSaved] = useState(true);
  const [searching, setSearching] = useState(true);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [addingArticle, setAddingArticle] = useState<string | null>(null);

  const reloadSaved = useCallback(async () => {
    setLoadingSaved(true);
    try {
      setSaved(await listCompetitors(productId));
    } finally {
      setLoadingSaved(false);
    }
  }, [productId]);

  const runSearch = useCallback(async () => {
    setSearching(true);
    setSearchError(null);
    try {
      const res = await searchCompetitors(productId);
      setKeywords(res.keywords);
      setSuggestions(res.competitors);
    } catch (e) {
      setSearchError(e instanceof Error ? e.message : "Поиск не удался");
    } finally {
      setSearching(false);
    }
  }, [productId]);

  useEffect(() => {
    reloadSaved();
    runSearch();
  }, [reloadSaved, runSearch]);

  const savedArticles = new Set(saved.map((c) => c.article).filter(Boolean));

  async function onAdd(c: CompetitorPreview) {
    if (!c.article) return;
    setAddingArticle(c.article);
    try {
      await addCompetitor(productId, c);
      haptic("success");
      setSuggestions((prev) => prev.filter((s) => s.article !== c.article));
      await reloadSaved();
    } catch (e) {
      haptic("error");
      setSearchError(e instanceof Error ? e.message : "Не удалось добавить");
    } finally {
      setAddingArticle(null);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold">Конкуренты</h2>
        <p className="line-clamp-1 text-sm text-[var(--tg-theme-hint-color)]">
          {productName}
        </p>
      </div>

      {/* Подсказки поиска */}
      <section className="flex flex-col gap-2">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-[var(--tg-theme-hint-color)]">
            Поиск по ключевым словам:
          </span>
          {searching && <Spinner className="h-4 w-4" />}
        </div>
        {keywords.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {keywords.map((k) => (
              <span
                key={k}
                className="rounded-lg bg-[var(--tg-theme-button-color)] px-2 py-0.5 text-xs text-[var(--tg-theme-button-text-color)]"
              >
                {k}
              </span>
            ))}
          </div>
        )}

        {searchError && <ErrorBanner message={searchError} />}

        {!searching &&
          suggestions
            .filter((s) => !s.article || !savedArticles.has(s.article))
            .map((c, i) => (
              <Card key={c.article ?? i} className="flex gap-3">
                <ProductImage
                  src={c.photo_url}
                  alt={c.name}
                  className="h-16 w-16 shrink-0"
                />
                <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                  <span className="line-clamp-2 text-sm font-medium leading-snug">
                    {c.name}
                  </span>
                  <span className="font-semibold">{formatPrice(c.price)}</span>
                  <Stars rating={c.rating} count={c.reviews_count} />
                </div>
                <Button
                  size="sm"
                  className="self-center"
                  disabled={!c.article || addingArticle === c.article}
                  onClick={() => onAdd(c)}
                >
                  {addingArticle === c.article ? (
                    <Spinner />
                  ) : (
                    <Plus className="h-4 w-4" />
                  )}
                </Button>
              </Card>
            ))}

        {!searching && suggestions.length === 0 && !searchError && (
          <p className="text-sm text-[var(--tg-theme-hint-color)]">
            Конкуренты не найдены.
          </p>
        )}
      </section>

      {/* Сохранённые конкуренты */}
      <section className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold">
          Мои конкуренты {saved.length > 0 && `(${saved.length})`}
        </h3>
        {loadingSaved ? (
          <Spinner />
        ) : saved.length === 0 ? (
          <p className="text-sm text-[var(--tg-theme-hint-color)]">
            Добавьте конкурентов из списка выше.
          </p>
        ) : (
          saved.map((c) => (
            <SavedCompetitorCard
              key={c.id}
              competitor={c}
              onDeleted={reloadSaved}
            />
          ))
        )}
      </section>
    </div>
  );
}

function SavedCompetitorCard({
  competitor,
  onDeleted,
}: {
  competitor: Competitor;
  onDeleted: () => void;
}) {
  const [note, setNote] = useState(competitor.note ?? "");
  const [savingNote, setSavingNote] = useState(false);
  const [noteSaved, setNoteSaved] = useState(false);
  const [reviews, setReviews] = useState<Review[] | null>(null);
  const [showReviews, setShowReviews] = useState(false);
  const [loadingReviews, setLoadingReviews] = useState(false);

  async function saveNote() {
    setSavingNote(true);
    setNoteSaved(false);
    try {
      await updateCompetitor(competitor.id, { note: note.trim() || null });
      haptic("success");
      setNoteSaved(true);
    } finally {
      setSavingNote(false);
    }
  }

  async function toggleReviews() {
    const next = !showReviews;
    setShowReviews(next);
    if (next && reviews === null) {
      setLoadingReviews(true);
      try {
        setReviews(await getCompetitorReviews(competitor.id));
      } finally {
        setLoadingReviews(false);
      }
    }
  }

  async function onDelete() {
    haptic("warning");
    if (!window.confirm("Удалить конкурента?")) return;
    await deleteCompetitor(competitor.id);
    haptic("success");
    onDeleted();
  }

  return (
    <Card className="flex flex-col gap-2">
      <div className="flex gap-3">
        <ProductImage
          src={competitor.photo_url}
          alt={competitor.name}
          className="h-16 w-16 shrink-0"
        />
        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          <span className="line-clamp-2 text-sm font-medium leading-snug">
            {competitor.name}
          </span>
          <span className="font-semibold">{formatPrice(competitor.price)}</span>
          <Stars rating={competitor.rating} count={competitor.reviews_count} />
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="self-start"
          onClick={onDelete}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>

      {competitor.tags && competitor.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {competitor.tags.slice(0, 8).map((t, i) => (
            <span
              key={i}
              className="rounded-lg bg-[var(--tg-theme-bg-color)] px-2 py-0.5 text-xs text-[var(--tg-theme-hint-color)]"
            >
              {t}
            </span>
          ))}
        </div>
      )}

      {/* Заметка продавца (вместо «Добавить отзыв») */}
      <div className="flex flex-col gap-1">
        <Textarea
          placeholder="Заметка: что у конкурента сильнее/слабее…"
          value={note}
          onChange={(e) => {
            setNote(e.target.value);
            setNoteSaved(false);
          }}
        />
        <Button
          variant="secondary"
          size="sm"
          className="self-end"
          onClick={saveNote}
          disabled={savingNote}
        >
          {savingNote ? <Spinner /> : <Save className="h-4 w-4" />}
          {noteSaved ? "Сохранено" : "Сохранить заметку"}
        </Button>
      </div>

      <Button variant="ghost" size="sm" onClick={toggleReviews}>
        {showReviews ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
        Отзывы конкурента
      </Button>
      {showReviews &&
        (loadingReviews ? (
          <Spinner />
        ) : (
          <ReviewList reviews={reviews ?? []} />
        ))}
    </Card>
  );
}
