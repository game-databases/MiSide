import * as React from "react";

import { cn } from "@/lib/utils";

/*
 * shadcn input. Reactive-input law (DR-2026-08-22-inputs-answer-as-you-type):
 * inputs recompute per keystroke; nothing here renders a form or a submit
 * control (AC S12 grep-gated scaffold-wide).
 */
function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "flex h-10 w-full min-w-0 rounded-full border border-input bg-transparent px-4 py-1 text-base text-foreground transition-[color,box-shadow] outline-none file:inline-flex file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive md:text-sm",
        className
      )}
      {...props}
    />
  );
}

export { Input };
