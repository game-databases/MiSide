/*
 * M1 authoring schema (content-pipeline spec §4) — TYPES + a zod-less hand
 * validator for article frontmatter. This module is the reviewable contract
 * of what an .mdx article may declare; scripts/build-content.mjs enforces
 * the SAME law at emit time (self-contained .mjs twin, per the
 * emit-artifacts convention) and tests pin both sides to identical verdicts.
 *
 * Bodies stay JSX-free markdown inside .mdx files (spec §5): no HTML, no
 * iframes, no inline scripts — interactive behavior is DECLARED here as
 * embeds[] slots and rendered by ArticleRoute from a closed module map.
 */

export type ArticleType = "guide" | "game" | "database" | "patch";
export type ArticleStatus = "draft" | "published";
export type SpoilerLevel = "none" | "mild" | "full";

/** §4 entities[] entry: `<routed-kind>: <id>` + optional explicit link terms. */
export interface EntityRef {
  /** ROUTED kind segment (profiles, not documents; mita, not characters). */
  kind: string;
  /** Contract id column value — exact string match, no fuzzy repair. */
  id: string;
  /**
   * V3.2 escape hatch: exact case-insensitive whole-token link terms for
   * rows the client never names (all 23 cartridges ship name_loc ABSENT).
   * Community aliases are never auto-scavenged — only declared here.
   */
  link_terms?: string[];
}

export interface ChecklistItem {
  text: string;
  /** Keycap hints rendered through KeycapKbd. */
  keys?: string[];
  /** Semantic danger state (--ms-danger): this step LOSES something. */
  danger?: boolean;
}

/** §5 closed embed map — OUR components only, declared, never inline JSX. */
export interface ArticleEmbed {
  /** Anchor target in the body, e.g. "route-map". */
  id: string;
  /** Heading/step id to insert after; omitted ⇒ end of body. */
  after?: string;
  module: "map-scene" | "entity-cards" | "checklist";
  props: Record<string, unknown>;
}

export interface ArticleFrontmatter {
  type: ArticleType;
  slug: string;
  title: string;
  /** ≤160 chars; used verbatim in metadata + search rows. */
  description: string;
  status: ArticleStatus;
  published_at: string;
  updated_at?: string;
  verified_build_id: string;
  spoiler: SpoilerLevel;
  /** ≥1 required for guides (entity-linked by definition); optional news. */
  entities: EntityRef[];
  /** Guides only, when the body honestly is steps → HowTo JSON-LD. */
  steps?: string[];
  embeds?: ArticleEmbed[];
}

export const ARTICLE_TYPES: readonly ArticleType[] = ["guide", "game", "database", "patch"];
export const ARTICLE_STATUSES: readonly ArticleStatus[] = ["draft", "published"];
export const SPOILER_LEVELS: readonly SpoilerLevel[] = ["none", "mild", "full"];
export const EMBED_MODULES: readonly ArticleEmbed["module"][] = [
  "map-scene",
  "entity-cards",
  "checklist",
];

const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const BUILD_ID_RE = /^\d+$/;

export interface ShapeVerdict {
  ok: boolean;
  /** Machine-readable failures naming field + offending value. */
  errors: string[];
}

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

/**
 * Shape law only (fields, formats, enums, nesting). V1/V2 entity resolution
 * needs the corpus, so the caller injects `routedIds(kind)` — undefined for
 * an unknown kind (= the V2 vocabulary rejection), else the id column set.
 * Corpus-free so tests can run it against fixtures.
 */
export function validateFrontmatter(
  raw: unknown,
  routedIds: (kind: string) => readonly string[] | undefined
): ShapeVerdict {
  const errors: string[] = [];
  const fail = (msg: string) => errors.push(msg);
  if (!isPlainObject(raw)) {
    return { ok: false, errors: ["frontmatter: expected a mapping"] };
  }
  const fm = raw as Record<string, unknown>;

  // -- unknown keys are rejected outright (reviewability over tolerance)
  const KNOWN = new Set([
    "type", "slug", "title", "description", "status", "published_at",
    "updated_at", "verified_build_id", "spoiler", "entities", "steps", "embeds",
  ]);
  for (const k of Object.keys(fm)) {
    if (!KNOWN.has(k)) fail(`unknown frontmatter key "${k}"`);
  }

  // -- required scalars
  const type = fm.type;
  if (typeof type !== "string" || !ARTICLE_TYPES.includes(type as ArticleType)) {
    fail(`type: must be one of ${ARTICLE_TYPES.join(" | ")}`);
  }
  const slug = fm.slug;
  if (typeof slug !== "string" || !SLUG_RE.test(slug)) {
    fail(`slug: "${String(slug)}" is not a kebab-case slug`);
  }
  if (typeof fm.title !== "string" || fm.title.trim() === "") {
    fail("title: required non-empty string");
  }
  if (typeof fm.description !== "string" || fm.description.trim() === "") {
    fail("description: required non-empty string");
  } else if ([...fm.description].length > 160) {
    fail(`description: ${[...fm.description].length} chars > 160`);
  }
  const status = fm.status;
  if (typeof status !== "string" || !ARTICLE_STATUSES.includes(status as ArticleStatus)) {
    fail(`status: must be one of ${ARTICLE_STATUSES.join(" | ")}`);
  }
  if (typeof fm.published_at !== "string" || !DATE_RE.test(fm.published_at)) {
    fail(`published_at: "${String(fm.published_at)}" is not YYYY-MM-DD`);
  }
  if (fm.updated_at !== undefined) {
    if (typeof fm.updated_at !== "string" || !DATE_RE.test(fm.updated_at)) {
      fail(`updated_at: "${String(fm.updated_at)}" is not YYYY-MM-DD`);
    }
  }
  if (
    typeof fm.verified_build_id !== "string" ||
    !BUILD_ID_RE.test(fm.verified_build_id)
  ) {
    fail('verified_build_id: quoted numeric string required (e.g. "19029065")');
  }
  const spoiler = fm.spoiler;
  if (typeof spoiler !== "string" || !SPOILER_LEVELS.includes(spoiler as SpoilerLevel)) {
    fail(`spoiler: must be one of ${SPOILER_LEVELS.join(" | ")}`);
  }

  // -- steps[] (guides only)
  if (fm.steps !== undefined) {
    if (!Array.isArray(fm.steps)) fail("steps: must be a list");
    else if (type === "guide") {
      fm.steps.forEach((s, i) => {
        if (typeof s !== "string" || s.trim() === "")
          fail(`steps[${i}]: required non-empty string`);
      });
    } else fail("steps: guides only");
  }

  // -- entities[] with V1/V2 via the injected resolver
  const entities: EntityRef[] = [];
  if (!Array.isArray(fm.entities)) {
    fail("entities: must be a list");
  } else {
    if (fm.entities.length === 0 && type === "guide") {
      fail("entities: guides require >=1 entity (they are entity-linked by definition)");
    }
    fm.entities.forEach((e, i) => {
      if (!isPlainObject(e)) {
        fail(`entities[${i}]: expected "<kind>: <id>" mapping`);
        return;
      }
      const extraKeys = Object.keys(e).filter(
        (k) => k !== "kind" && k !== "id" && k !== "link_terms"
      );
      if (extraKeys.length > 0) {
        fail(`entities[${i}]: unknown key "${extraKeys[0]}"`);
        return;
      }
      const kind = e.kind;
      const id = e.id;
      if (typeof kind !== "string" || typeof id !== "string") {
        fail(`entities[${i}]: expected "<kind>: <id>"`);
        return;
      }
      let linkTerms: string[] | undefined;
      if (e.link_terms !== undefined) {
        if (
          !Array.isArray(e.link_terms) ||
          e.link_terms.some((t) => typeof t !== "string" || t.trim() === "")
        ) {
          fail(`entities[${i}].link_terms: list of non-empty strings`);
          return;
        }
        linkTerms = e.link_terms as string[];
      }
      const ids = routedIds(kind);
      if (ids === undefined) {
        // V2: the ROUTED vocabulary only — synonyms rejected outright
        fail(`entities[${i}]: "${kind}" is not a routed kind (V2)`);
        return;
      }
      if (!ids.includes(id)) {
        // V1/V4: unresolved refs break the build loudly (rename decay fails loud)
        fail(`entities[${i}]: ${kind}:${id} does not resolve through the contract id column (V1)`);
        return;
      }
      entities.push({ kind, id, ...(linkTerms ? { link_terms: linkTerms } : {}) });
    });
  }

  // -- embeds[] against the closed module map (§5)
  if (fm.embeds !== undefined) {
    if (!Array.isArray(fm.embeds)) fail("embeds: must be a list");
    else {
      const seenIds = new Set<string>();
      fm.embeds.forEach((e, i) => {
        if (!isPlainObject(e)) {
          fail(`embeds[${i}]: expected a mapping`);
          return;
        }
        const { id, after, module: mod, props } = e as Record<string, unknown>;
        if (typeof id !== "string" || !SLUG_RE.test(id)) {
          fail(`embeds[${i}].id: kebab-case anchor id required`);
        } else if (seenIds.has(id)) {
          fail(`embeds[${i}].id: duplicate embed id "${id}"`);
        } else seenIds.add(id);
        if (after !== undefined && (typeof after !== "string" || after === "")) {
          fail(`embeds[${i}].after: heading/step id or omit`);
        }
        if (typeof mod !== "string" || !EMBED_MODULES.includes(mod as ArticleEmbed["module"])) {
          fail(`embeds[${i}].module: must be one of ${EMBED_MODULES.join(" | ")}`);
        }
        if (!isPlainObject(props)) fail(`embeds[${i}].props: mapping required`);
        else {
          // per-module prop laws (§5)
          if (mod === "map-scene") {
            const allowed = new Set(["scene_id", "focus_poi_id", "height"]);
            for (const k of Object.keys(props)) {
              if (!allowed.has(k)) fail(`embeds[${i}].props.${k}: not a map-scene prop`);
            }
            if (typeof props.scene_id !== "string") {
              fail(`embeds[${i}].props.scene_id: required string`);
            }
          } else if (mod === "entity-cards") {
            const allowed = new Set(["title"]);
            for (const k of Object.keys(props)) {
              if (!allowed.has(k)) fail(`embeds[${i}].props.${k}: not an entity-cards prop`);
            }
          } else if (mod === "checklist") {
            const allowed = new Set(["items", "title"]);
            for (const k of Object.keys(props)) {
              if (!allowed.has(k)) fail(`embeds[${i}].props.${k}: not a checklist prop`);
            }
            const items = props.items;
            if (!Array.isArray(items) || items.length === 0) {
              fail(`embeds[${i}].props.items: non-empty list required`);
            } else {
              items.forEach((it, j) => {
                if (!isPlainObject(it) || typeof (it as Record<string, unknown>).text !== "string") {
                  fail(`embeds[${i}].props.items[${j}]: {text, keys?, danger?} required`);
                }
              });
            }
          }
        }
      });
    }
  }

  return { ok: errors.length === 0, errors };
}
