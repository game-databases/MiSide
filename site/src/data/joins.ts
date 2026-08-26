/*
 * SERVER-ONLY readers over the ACCEPTED contract registries
 * (contracts/registry/{joins,entities}.json) + the canonical relink tree they
 * describe (data-contracts spec §4: read surface extracted/relinks/*.jsonl
 * ONLY).
 *
 * Consumption law this module enforces (spec §1 consumes-never-derives,
 * §4.2): an entity page never computes a relation the tree does not ship —
 * every edge a page shows comes from a REGISTERED family file, parsed through
 * the registry's OWN anchor grammar, with a consume-time census gate that
 * fails loud when disk drifts from the registry. No family, no edge.
 *
 * This module stays PUR (imports only ./jsonl.ts): endpoint→page resolution
 * lives one layer up (lib/relations/relationCards.ts) so the data reader
 * never depends on display concerns.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { contractsRegistryRoot, readJsonl } from "./jsonl.ts";

/* ------------------------------------------------------------------ */
/* Registry documents                                                  */
/* ------------------------------------------------------------------ */

/** One family entry of joins.json (= data-contracts spec §4.1 row). */
export interface JoinFamily {
  family: string;
  /** Owning file, registry-verbatim ("extracted/relinks/<stem>.jsonl"). */
  file: string;
  binds: string;
  schema_id: string | null;
  /** "endpoints" | "id-columns" | "meta-only". */
  anchor_mode: string;
  /** "direction-split" | "forward-only" | "reverse-index" | "kind-encoded" | "meta-only". */
  direction_handling: string;
  edge_count_expected: number;
  edge_count_measured: number;
  /** Family-specific anchor-form vocabulary ("<bare>", "achievement:", …). */
  anchor_grammar?: { from: string[]; to: string[] };
  mechanisms: Record<string, number>;
  statuses: Record<string, number>;
  notes?: string;
}

interface JoinsDocMeta {
  build_pin?: { build_id?: string; version_label?: string };
  expected_edge_total?: number;
}

export interface JoinsRegistry {
  meta: JoinsDocMeta;
  /** Keyed by family stem ("character--cartridge", …). */
  families: Record<string, JoinFamily>;
}

let joinsCache: JoinsRegistry | null = null;

/** Parse joins.json once; every consumer shares the pinned family table. */
export function joinRegistry(): JoinsRegistry {
  if (joinsCache) return joinsCache;
  const raw = readFileSync(
    join(contractsRegistryRoot(), "joins.json"),
    "utf8"
  );
  const doc = JSON.parse(raw) as Record<string, unknown> & {
    families?: Record<string, Omit<JoinFamily, "family">>;
  };
  const families: Record<string, JoinFamily> = {};
  for (const [stem, f] of Object.entries(doc.families ?? {})) {
    families[stem] = { ...(f as Omit<JoinFamily, "family">), family: stem };
  }
  joinsCache = {
    meta: {
      build_pin: doc.build_pin as JoinsDocMeta["build_pin"],
      expected_edge_total: doc.expected_edge_total as number | undefined,
    },
    families,
  };
  return joinsCache;
}

/** One entity_types entry of entities.json (fields/enums/row_count census). */
export interface EntityTypeEntry {
  artifacts?: string[];
  key?: string;
  row_count?: number;
  header_class?: string;
  schema_id?: string;
  enums: Record<string, Record<string, number>>;
}

let entitiesCache: Record<string, EntityTypeEntry> | null = null;

/** entities.json entity_types — the measured census the search builder pins against. */
export function entitiesRegistry(): Record<string, EntityTypeEntry> {
  if (entitiesCache) return entitiesCache;
  const raw = readFileSync(
    join(contractsRegistryRoot(), "entities.json"),
    "utf8"
  );
  const doc = JSON.parse(raw) as {
    entity_types?: Record<string, EntityTypeEntry>;
  };
  entitiesCache = doc.entity_types ?? {};
  return entitiesCache;
}

/* ------------------------------------------------------------------ */
/* Edge reading — generic over every registered family                 */
/* ------------------------------------------------------------------ */

/**
 * One parsed anchor endpoint. `form` is the family-vocabulary token
 * ("achievement:", "container:", "<bare>", …); `id` is the verbatim anchor id
 * after the prefix (whole raw string when bare). `raw` stays verbatim for
 * fail-closed echo; JSON-null anchors keep raw=null (a TYPED empty state,
 * never conflated with absent keys — spec §4.2).
 */
export interface RelationEndpoint {
  raw: string | null;
  form: string;
  id: string;
}

/**
 * One normalized relink row. Direction reads BOTH corpus spellings
 * (`direction` on relink-schema files, `kind` on the documents-family files —
 * measured 2026-08-26). mechanism/status/method ride verbatim (carry law;
 * `method` is the spec §3.10 "recorded derivation" string). Every other
 * column lands in `scalars` untouched — the reader never drops a shipped
 * field nor invents one.
 */
export interface RelationEdge {
  family: string;
  /** "forward" | "inverse" | mirror restatement | "id-columns". */
  direction: string;
  from: RelationEndpoint | null;
  to: RelationEndpoint | null;
  mechanism: string | null;
  status: string | null;
  method: string | null;
  missing_fields: string[];
  scalars: Record<string, unknown>;
}

const ENDPOINT_KEYS = new Set(["direction", "kind", "from", "to"]);
const PROVENANCE_KEYS = new Set([
  "mechanism",
  "status",
  "missing_fields",
  "method",
]);

/** Split one anchor into (form, id) against a family's own grammar. */
function parseAnchor(
  raw: string | null | undefined,
  grammarForms: string[]
): RelationEndpoint | null {
  if (raw === null) return { raw: null, form: "<null>", id: "" };
  if (typeof raw !== "string") return null;
  const colon = raw.indexOf(":");
  const candidate = colon > 0 ? `${raw.slice(0, colon)}:` : "<bare>";
  const known =
    grammarForms.includes(candidate) || grammarForms.includes("<bare>");
  const form = colon > 0 ? candidate : "<bare>";
  // Unknown vocabulary still parses (fail-closed echo downstream) but keeps
  // its literal form so consumers can see what they refused to resolve.
  void known;
  return { raw, form, id: colon > 0 ? raw.slice(colon + 1) : raw };
}

/**
 * All normalized edges of one registered family. Throws when the file's row
 * count drifts from the registry's measured census (the C5 fingerprint bar,
 * re-checked at consume time so no consumer can quietly read a stale tree).
 * META-ONLY families (measured absence shipped as data, §4.1) return [].
 */
export function familyEdges(family: string): RelationEdge[] {
  const reg = joinRegistry();
  const fam = reg.families[family];
  if (!fam) {
    throw new Error(`join family not registered: ${family}`);
  }
  if (fam.anchor_mode === "meta-only" || fam.edge_count_measured === 0) {
    return [];
  }
  const rel = fam.file.startsWith("extracted/")
    ? fam.file.slice("extracted/".length)
    : fam.file;
  const { rows } = readJsonl<Record<string, unknown>>(rel);
  if (rows.length !== fam.edge_count_measured) {
    throw new Error(
      `${family}: registry pins ${fam.edge_count_measured} edges but ${rel} holds ${rows.length}`
    );
  }
  const grammarForms = [
    ...(fam.anchor_grammar?.from ?? []),
    ...(fam.anchor_grammar?.to ?? []),
  ];
  return rows.map((r) => {
    const direction =
      typeof r.direction === "string"
        ? r.direction
        : typeof (r as { kind?: unknown }).kind === "string"
          ? ((r as { kind: string }).kind)
          : fam.anchor_mode === "id-columns"
            ? "id-columns"
            : "";
    const missing = Array.isArray(r.missing_fields)
      ? (r.missing_fields as unknown[]).filter(
          (m): m is string => typeof m === "string"
        )
      : [];
    const scalars: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(r)) {
      if (ENDPOINT_KEYS.has(k) || PROVENANCE_KEYS.has(k)) continue;
      scalars[k] = v;
    }
    const idColumns = fam.anchor_mode === "id-columns";
    return {
      family,
      direction,
      from: idColumns
        ? null
        : parseAnchor(r.from as string | null | undefined, grammarForms),
      to: idColumns
        ? null
        : parseAnchor(r.to as string | null | undefined, grammarForms),
      mechanism: typeof r.mechanism === "string" ? r.mechanism : null,
      status: typeof r.status === "string" ? r.status : null,
      method: typeof r.method === "string" ? r.method : null,
      missing_fields: missing,
      scalars,
    };
  });
}
