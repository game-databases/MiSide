import * as React from "react";
import { Slot } from "radix-ui";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

/*
 * Button → PillButton (kit contract §4.1): pill radius-full, gradient fill
 * --ms-accent-gradient, glow lift --ms-glow-pink (T2 §3 key-hint pills,
 * §6 recipes). Radix press/focus semantics inherited from ui/button stock.
 */
const pillVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full font-bold uppercase tracking-wide transition-[filter,box-shadow,transform] duration-200 outline-none focus-visible:ring-2 focus-visible:ring-ring/70 focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 active:translate-y-px hover:brightness-110",
  {
    variants: {
      tone: {
        accent:
          "text-primary-foreground shadow-glow-pink [background-image:var(--ms-accent-gradient)]",
        hot: "bg-primary text-primary-foreground shadow-glow-pink",
        soft: "bg-[var(--ms-accent-soft)] text-[color-mix(in_srgb,var(--ms-bg-0)_82%,black)]",
        ghost:
          "bg-secondary text-secondary-foreground hover:bg-[color-mix(in_srgb,var(--ms-bg-2)_80%,white)]",
        danger: "bg-destructive text-destructive-foreground shadow-glow-glitch",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-5 text-sm",
        lg: "h-12 px-7 text-base",
      },
    },
    defaultVariants: { tone: "accent", size: "md" },
  }
);

function PillButton({
  className,
  tone,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof pillVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot.Root : "button";
  return (
    <Comp
      data-slot="pill-button"
      className={cn(pillVariants({ tone, size }), className)}
      {...props}
    />
  );
}

export { PillButton, pillVariants };
