"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

/*
 * shadcn table (TanStack-ready host). Kit law: header pills; danger rows take
 * --ms-danger, CRT green --ms-signal is RESERVED for machine-voice cells —
 * those register via data-machine / data-danger attributes the kit styles.
 */
function Table({ className, ...props }: React.ComponentProps<"table">) {
  return (
    <div data-slot="table-container" className="relative w-full overflow-x-auto">
      <table
        data-slot="table"
        className={cn("w-full caption-bottom text-sm", className)}
        {...props}
      />
    </div>
  );
}

function TableHeader({ className, ...props }: React.ComponentProps<"thead">) {
  return (
    <thead data-slot="table-header" className={cn("[&_tr]:border-b", className)} {...props} />
  );
}

function TableBody({ className, ...props }: React.ComponentProps<"tbody">) {
  return (
    <tbody data-slot="table-body" className={cn("[&_tr:last-child]:border-0", className)} {...props} />
  );
}

function TableFooter({ className, ...props }: React.ComponentProps<"tfoot">) {
  return (
    <tfoot
      data-slot="table-footer"
      className={cn("bg-card/50 border-t font-medium", className)}
      {...props}
    />
  );
}

function TableRow({ className, ...props }: React.ComponentProps<"tr">) {
  return (
    <tr
      data-slot="table-row"
      className={cn(
        "border-b transition-colors hover:bg-secondary/60 data-[danger=true]:bg-[color-mix(in_srgb,var(--ms-danger)_18%,transparent)] data-[state=selected]:bg-secondary",
        className
      )}
      {...props}
    />
  );
}

function TableHead({ className, ...props }: React.ComponentProps<"th">) {
  return (
    <th
      data-slot="table-head"
      className={cn(
        "h-10 px-3 text-start align-middle text-xs font-bold uppercase tracking-wide whitespace-nowrap [&:has([role=checkbox])]:pe-0",
        "[&_>span]:inline-flex [&_>span]:items-center [&_>span]:rounded-full [&_>span]:bg-secondary [&_>span]:px-3 [&_>span]:py-1",
        className
      )}
      {...props}
    />
  );
}

function TableCell({ className, ...props }: React.ComponentProps<"td">) {
  return (
    <td
      data-slot="table-cell"
      className={cn(
        "p-3 align-middle whitespace-nowrap [&:has([role=checkbox])]:pe-0",
        "group-data-[machine=true]/cell:font-lcd group-data-[machine=true]/cell:text-[var(--ms-signal)]",
        className
      )}
      {...props}
    />
  );
}

function TableCaption({
  className,
  ...props
}: React.ComponentProps<"caption">) {
  return (
    <caption
      data-slot="table-caption"
      className={cn("mt-4 text-sm text-muted-foreground", className)}
      {...props}
    />
  );
}

export {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
};
