import { ImageOff } from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";

export function ProductImage({
  src,
  alt,
  className,
}: {
  src?: string | null;
  alt?: string;
  className?: string;
}) {
  const [failed, setFailed] = useState(false);

  if (!src || failed) {
    return (
      <div
        className={cn(
          "flex items-center justify-center rounded-xl bg-black/5 text-[var(--tg-theme-hint-color)]",
          className
        )}
      >
        <ImageOff className="h-6 w-6" />
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt ?? ""}
      loading="lazy"
      onError={() => setFailed(true)}
      className={cn("rounded-xl object-cover", className)}
    />
  );
}
