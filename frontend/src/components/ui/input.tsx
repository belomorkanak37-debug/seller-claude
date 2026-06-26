import * as React from "react";

import { cn } from "@/lib/utils";

const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "h-11 w-full rounded-xl border border-black/10 bg-[var(--tg-theme-bg-color)]",
      "px-3 text-[var(--tg-theme-text-color)] outline-none",
      "placeholder:text-[var(--tg-theme-hint-color)]",
      "focus:border-[var(--tg-theme-link-color)]",
      className
    )}
    {...props}
  />
));
Input.displayName = "Input";

export { Input };
