import * as React from "react";

import { cn } from "@/lib/utils";

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-2xl bg-[var(--tg-theme-secondary-bg-color)] p-4 shadow-sm",
      className
    )}
    {...props}
  />
));
Card.displayName = "Card";

export { Card };
