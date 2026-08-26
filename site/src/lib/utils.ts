import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/*
 * typedRoutes is pinned (spec §2 tree); route strings are composed
 * dynamically here by design (one shared route table). This is the single,
 * audited escape hatch — every call site composes its href from
 * lib/routes.ts data only.
 */
import type { Route } from "next";
export function asRoute<T extends string>(href: T): Route<T> {
  return href as Route<T>;
}
