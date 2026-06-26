import * as React from "react";

import { cn } from "@/lib/utils";

const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "min-h-[80px] w-full rounded-xl border border-black/10 bg-[var(--tg-theme-bg-color)]",
      "p-3 text-[var(--tg-theme-text-color)] outline-none",
      "placeholder:text-[var(--tg-theme-hint-color)]",
      "focus:border-[var(--tg-theme-link-color)]",
      className
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";

export { Textarea };
