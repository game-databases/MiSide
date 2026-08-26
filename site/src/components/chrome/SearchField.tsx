"use client";

import * as React from "react";
import Link from "next/link";
import { SearchIcon, XIcon } from "lucide-react";

import { Input } from "@/components/ui/input";
import { VoidWell } from "@/components/kit/VoidWell";
import { asRoute } from "@/lib/utils";
import {
  MAX_VISIBLE_ROWS,
  MIN_QUERY_LENGTH,
  countSearchHits,
  createSearchIndex,
  indexAll,
  searchRows,
  type SearchHit,
  type SearchRow,
} from "@/lib/search/searchRows";

/** Index kinds → their chrome nav word (facet chips speak chrome, not slugs). */
const FACETS: Array<{ kind: string; key: string }> = [
  { kind: "mita", key: "nav.mita" },
  { kind: "players", key: "nav.players" },
  { kind: "cartridges", key: "nav.cartridges" },
  { kind: "minigames", key: "nav.minigames" },
  { kind: "achievements", key: "nav.achievements" },
  { kind: "endings", key: "nav.endings" },
  { kind: "lore/profiles", key: "nav.lore" },
  { kind: "lore/books", key: "nav.books" },
  { kind: "locations", key: "nav.locations" },
  { kind: "dialogue", key: "nav.dialogue" },
];

/*
 * The header owns the field (DR-2026-08-22-search-is-not-a-page):
 * closed — "Search" is a word in the nav; open — the input grows across the
 * nav row. Results replace page content IN PLACE at ≥2 typed characters;
 * content returns on clear or Escape. Content is hidden, never unmounted.
 * No form element, no submit control anywhere (AC S12); recomputes per keystroke.
 * The address bar does NOT follow search typing — the field has no route by
 * ruling. Facet chips stay client-local; facet combinations create no URLs.
 */
export function SearchField({
  chrome,
  localeCode,
}: {
  chrome: Record<string, string>;
  localeCode: string;
}) {
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const [facet, setFacet] = React.useState<string>("all");
  const [hits, setHits] = React.useState<SearchHit[]>([]);
  // VC-2 fix #4: pre-truncation match count — the "+N" chip carries the
  // remainder so the render cap never reads as "these are all".
  const [total, setTotal] = React.useState(0);
  const [showAll, setShowAll] = React.useState(false);
  // Built exclusively through createSearchIndex — no second MiniSearch config
  const indexRef = React.useRef<ReturnType<typeof createSearchIndex> | null>(
    null
  );
  const inputRef = React.useRef<HTMLInputElement | null>(null);

  // Lazy-load the emitted per-locale index once, then run the ONE matching
  // path on the browser side — the SAME constructor and matching function the
  // server uses (B-RP1: a second hand-rolled MiniSearch config here could
  // drift from createSearchIndex; there is exactly one now).
  const ensureIndex = React.useCallback(async () => {
    if (indexRef.current) return indexRef.current;
    const res = await fetch(`/search/${localeCode}.idx.json`);
    const rows = (await res.json()) as SearchRow[];
    const index = createSearchIndex(rows);
    indexAll(index, rows);
    indexRef.current = index;
    return index;
  }, [localeCode]);

  React.useEffect(() => {
    let cancelled = false;
    if (!open) return;
    void (async () => {
      const index = await ensureIndex();
      if (cancelled) return;
      setHits(
        searchRows(index, query, {
          kind: facet,
          limit: showAll ? Number.POSITIVE_INFINITY : MAX_VISIBLE_ROWS,
        })
      );
      setTotal(countSearchHits(index, query, { kind: facet }));
    })();
    return () => {
      cancelled = true;
    };
  }, [query, facet, open, showAll, ensureIndex]);

  // In-place replacement: hide the page content wrapper, never unmount it.
  React.useEffect(() => {
    const content = document.getElementById("page-content");
    if (!content) return;
    if (open && query.trim().length >= MIN_QUERY_LENGTH) {
      content.setAttribute("hidden", "");
    } else {
      content.removeAttribute("hidden");
    }
  }, [open, query]);

  function close() {
    setOpen(false);
    setQuery("");
    setHits([]);
    setTotal(0);
    setShowAll(false);
  }

  if (!open) {
    return (
      <button
        type="button"
        data-slot="search-toggle"
        aria-label={chrome["a11y.searchToggle"]}
        onClick={() => {
          setOpen(true);
          requestAnimationFrame(() => inputRef.current?.focus());
        }}
        className="inline-flex h-10 items-center gap-2 rounded-full px-4 text-sm font-bold text-foreground hover:bg-accent"
      >
        <SearchIcon className="size-4" />
        <span>{chrome["nav.search"]}</span>
      </button>
    );
  }

  return (
    <div className="flex min-w-0 flex-1 flex-col">
      <div className="flex items-center gap-2">
        {/* grows across the nav row */}
        <Input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Escape") close();
          }}
          placeholder={chrome["search.placeholder"]}
          aria-label={chrome["nav.search"]}
          className="h-10 flex-1 border-border bg-card text-foreground placeholder:text-muted-foreground"
        />
        <button
          type="button"
          onClick={close}
          aria-label={chrome["tracker.reset"]}
          className="inline-flex size-10 items-center justify-center rounded-full hover:bg-accent"
        >
          <XIcon className="size-4" />
        </button>
      </div>
      {query.trim().length >= MIN_QUERY_LENGTH && (
        <div
          data-slot="search-results"
          className="absolute inset-x-0 top-full z-50 mx-auto mt-2 max-w-5xl rounded-md border border-border bg-card p-3 shadow-glow-pink"
        >
          <div className="mb-2 flex flex-wrap gap-1.5">
            <FacetChip active={facet === "all"} onClick={() => setFacet("all")} label={chrome["filters.all"]} />
            {FACETS.map((f) => (
              <FacetChip
                key={f.kind}
                active={facet === f.kind}
                onClick={() => setFacet(f.kind)}
                label={chrome[f.key] ?? f.kind}
              />
            ))}
          </div>
          {hits.length === 0 ? (
            /* empty well, not an absence announcement (design-standard §5.3) */
            <VoidWell className="h-16 min-h-16" role="presentation" />
          ) : (
            <>
              <ul className="max-h-96 overflow-y-auto rounded-md">
                {hits.map((hit) => (
                  <li key={`${hit.kind}:${hit.id}`}>
                    <Link
                      href={asRoute(hit.url)}
                      onClick={close}
                      className="flex items-center justify-between gap-3 rounded-full px-3 py-1.5 text-sm hover:bg-accent"
                    >
                      <span className="font-bold">{hit.title}</span>
                      <span className="text-xs uppercase tracking-wide text-muted-foreground">
                        {chrome[FACETS.find((f) => f.kind === hit.kind)?.key ?? ""] ?? hit.kind}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
              {/* the cap's remainder, as a number — expands in place */}
              {total > hits.length && (
                <button
                  type="button"
                  data-slot="search-more"
                  onClick={() => setShowAll(true)}
                  aria-label={`+${total - hits.length}`}
                  className="mt-2 inline-flex items-center rounded-full bg-secondary px-3 py-1 font-lcd text-sm text-[var(--ms-signal)] hover:brightness-110"
                >
                  +{total - hits.length}
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

function FacetChip({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={
        "rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wide transition-colors " +
        (active
          ? "bg-primary text-primary-foreground"
          : "bg-secondary text-secondary-foreground hover:brightness-110")
      }
    >
      {label}
    </button>
  );
}
