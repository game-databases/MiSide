/*
 * M2 emit (content-pipeline spec §2/§3): compile authored article .mdx into
 * the machine plane —
 *   • content/emit/articles.jsonl        registry (_meta + one row/article)
 *   • content/emit/article_locales.jsonl per-article locale admission ledger
 *   • content/emit/bodies/<guides|news>/<slug>.<locale>.html  compiled bodies
 *
 * Laws enforced HERE, before anything renders:
 *   §4 V1/V2  every entities[] ref resolves through the routed kinds and
 *             their contract id columns — wrong vocabulary rejected outright,
 *             rename decay fails loud (nonzero exit naming file + ref);
 *   §4 V3     deterministic linking FROM the declared list only: known names
 *             link their first occurrence per entity per locale; byte-identical
 *             display strings never auto-link; nameless rows link zero unless
 *             frontmatter declares link_terms; absent locale names omit links
 *             (never an EN fallback);
 *   §4 V5     drafts never reach the registry (logged DRAFT-SKIPPED);
 *   §2/§5/C14 ESCAPE-FIRST rendering: any lexer `html` token at ANY depth
 *             fails the build naming file + snippet; link/image destinations
 *             restricted to http/https/mailto/relative/#fragment — judged on
 *             the BROWSER-DECODED form (character references decoded before
 *             the allowlist, amendment 2026-08-26), so `javascript&colon;…`
 *             and `&#58;…` cannot smuggle an executable scheme past either
 *             gate; every
 *             emitted body RE-PARSES clean against the closed element
 *             allowlist (GFM table scaffolding included; `input` only in its
 *             task-list scope: leading child of an li, attributes drawn solely
 *             from type/disabled/checked with type="checkbox" required); zero
 *             event-handler attributes (parsed attribute NAMES matching on*);
 *             allowlisted href/src only. No sanitizer dependency.
 *   §3.3      staleness: entity-row hash drift flips the article stale
 *             (STALE: lines); pivot-move drift flags non-pivot cells whose
 *             stored base_sha16 no longer equals the CURRENT pivot body sha16
 *             (TRANSLATION-STALE: <article_id>@<locale> <- pivot moved).
 *             Both machine-plane output only, never user-facing.
 *
 * Self-contained .mjs by the emit-artifacts convention (no TS imports): the
 * mirrors below pin the same contract documents as src/data/*.
 *
 * Run: node scripts/build-content.mjs   (also exported for tests/prebuild)
 */
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, readdirSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { Marked } from "marked";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const SITE_ROOT = join(SCRIPT_DIR, "..");

export function sha16(text) {
  return createHash("sha256").update(text, "utf8").digest("hex").slice(0, 16);
}

/* ---------- shared reader layer (B-RP1: no second copy of the readers) ---- */
import { ENTITY_KINDS, kindRows } from "../src/data/contracts.ts";
import { displayName, desluggedLabel } from "../src/components/routes/entityDisplay.ts";
import { KIND_SEGMENT } from "../src/lib/routes.ts";
import { LOCALES } from "../src/i18n/locales.ts";

const LOCALE_CODES = new Set(LOCALES.map((l) => l.code));
const PIVOT = "en";

function loadCorpus() {
  const rowsByKind = new Map(); // kind -> [{id,row}]
  const idsByKind = new Map(); // kind -> Set(id)
  for (const [kind, def] of Object.entries(ENTITY_KINDS)) {
    const list = kindRows(kind).map((row) => ({
      id: String(row[def.idField]),
      row,
    }));
    rowsByKind.set(kind, list);
    idsByKind.set(kind, new Set(list.map((e) => e.id)));
  }
  return { rowsByKind, idsByKind };
}

/* ---------- frontmatter parser (minimal YAML subset, strict) -------------- */
/*
 * Supports exactly what §4 declares: top-level scalars, inline [] lists,
 * block lists of scalars or one-level mappings ("- kind: id" plus continued
 * indented keys), quoted strings. Anything else fails loud — no silent
 * repair, per §4's "No warnings, no auto-correction".
 */
function parseFrontmatter(source, file) {
  const fail = (msg) => {
    const err = new Error(`${file}: ${msg}`);
    err.expose = true;
    return err;
  };
  const m = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/.exec(source);
  if (!m) throw fail("missing --- frontmatter fence");
  const body = source.slice(m[0].length);
  const lines = m[1].split(/\r?\n/);

  const unquote = (v) => {
    const s = String(v).trim();
    if (
      (s.startsWith('"') && s.endsWith('"') && s.length >= 2) ||
      (s.startsWith("'") && s.endsWith("'") && s.length >= 2)
    ) {
      return s.slice(1, -1).replace(/\\"/g, '"').replace(/''/g, "'");
    }
    return s;
  };
  const scalar = (raw) => {
    // §4 frontmatter is string-typed end to end — no numeric coercion, so a
    // quoted build id stays a string and ids never lose their shape
    return unquote(raw);
  };
  const parseInlineList = (raw) => {
    const inner = unquote(raw.trim());
    if (!inner.startsWith("[") || !inner.endsWith("]")) {
      throw fail(`unsupported list syntax: ${String(raw).trim().slice(0, 40)}`);
    }
    const itemsSrc = inner.slice(1, -1).trim();
    if (!itemsSrc) return [];
    const out = [];
    const itemRe = /"(?:[^"\\]|\\.)*"|'(?:[^']|'')*'|[^,\s]+/g;
    let mm;
    while ((mm = itemRe.exec(itemsSrc))) {
      out.push(scalar(mm[0].replace(/,$/, "")));
    }
    return out;
  };

  const keyRe = /^([A-Za-z_][\w-]*)\s*:\s*(.*)$/;
  let i = 0;

  function indentOf(line) {
    return line.match(/^(\s*)/)[1].length;
  }

  /** Parse the value after "key:" — inline scalar/list or a block list/mapping. */
  function parseValue(rawAfterKey, keyIndent) {
    const trimmed = rawAfterKey.trim();
    if (trimmed !== "") {
      if (trimmed.startsWith("[")) return parseInlineList(trimmed);
      return scalar(trimmed);
    }
    // block value: nested list items, nested mapping, or empty
    if (i < lines.length) {
      const next = lines[i];
      if (next.trim() === "") return null;
      const nextIndent = indentOf(next);
      if (nextIndent <= keyIndent) return null;
      if (next.trim().startsWith("- ")) return parseListItems(nextIndent);
      if (keyRe.test(next.trim())) return parseBlockMapping(nextIndent);
    }
    return null;
  }

  /** Parse a block mapping whose keys sit at exactly `indent`. */
  function parseBlockMapping(indent) {
    const obj = {};
    while (i < lines.length) {
      const line = lines[i];
      if (line.trim() === "") break;
      if (indentOf(line) !== indent || line.trim().startsWith("- ")) break;
      const ck = line.trim().match(keyRe);
      if (!ck) throw fail(`unsupported mapping line: ${line.trim().slice(0, 60)}`);
      i++; // consume the key line before parsing its (possibly block) value
      obj[ck[1]] = parseValue(ck[2], indent);
    }
    return obj;
  }

  /** Parse "- ..." items at exactly `indent`; scalars or one-level mappings. */
  function parseListItems(indent) {
    const items = [];
    while (i < lines.length) {
      const line = lines[i];
      if (line.trim() === "") break;
      if (indentOf(line) !== indent || !line.trim().startsWith("- ")) break;
      const rest = line.trim().slice(2);
      const km = rest.match(keyRe);
      if (!km) {
        items.push(scalar(rest));
        i++;
        continue;
      }
      const obj = {};
      i++; // consume the item line before parsing its (possibly block) value
      obj[km[1]] = parseValue(km[2], indent);
      // continuation keys of the SAME mapping item sit deeper than `indent`
      while (i < lines.length) {
        const cont = lines[i];
        if (cont.trim() === "") break;
        if (cont.trim().startsWith("- ")) break;
        if (indentOf(cont) <= indent) break;
        const ck = cont.trim().match(keyRe);
        if (!ck) throw fail(`unsupported mapping continuation: ${cont.trim().slice(0, 60)}`);
        i++;
        obj[ck[1]] = parseValue(ck[2], indentOf(cont));
      }
      items.push(obj);
    }
    return items;
  }

  const doc = {};
  while (i < lines.length) {
    const line = lines[i];
    if (line.trim() === "") {
      i++;
      continue;
    }
    const km = line.trim().match(keyRe);
    if (!km) throw fail(`unsupported frontmatter line: ${line.trim().slice(0, 60)}`);
    if (indentOf(line) !== 0) {
      throw fail(`top-level key must be unindented: ${line.trim().slice(0, 40)}`);
    }
    i++; // consume the key line before parsing its (possibly block) value
    doc[km[1]] = parseValue(km[2], 0);
  }

  // normalize `- lore: paperpart-level13-0` mapping items to {kind,id,...}
  if (doc.entities !== undefined && doc.entities !== null) {
    if (!Array.isArray(doc.entities)) throw fail("entities: must be a list");
    doc.entities = doc.entities.map((e) => {
      if (e && typeof e === "object" && !Array.isArray(e)) {
        if ("kind" in e && "id" in e) return { ...e, id: String(e.id) };
        const kindKey = Object.keys(e).find((k) => k !== "link_terms");
        if (kindKey) {
          return {
            kind: kindKey,
            id: String(e[kindKey]),
            ...(e.link_terms !== undefined ? { link_terms: e.link_terms } : {}),
          };
        }
      }
      return e;
    });
  }
  return { fm: doc, body };
}

/* ---------- escape-first law: lexer gates + emitted re-parse (C14) -------- */

/** Deep-walk a marked token forest regardless of nesting shape. */
function* walkTokens(tokens) {
  for (const t of tokens ?? []) {
    yield t;
    if (Array.isArray(t?.tokens)) yield* walkTokens(t.tokens);
    if (t?.type === "list" && Array.isArray(t.items)) {
      for (const item of t.items) {
        yield item;
        if (Array.isArray(item.tokens)) yield* walkTokens(item.tokens);
      }
    }
    if (t?.type === "table") {
      for (const cell of [...(t.header ?? []), ...(t.rows ?? []).flat()]) {
        if (Array.isArray(cell?.tokens)) yield* walkTokens(cell.tokens);
      }
    }
  }
}

/**
 * §2/§5 gate on the SAME lexer AST the TOC walk uses: deny every `html`
 * token at any depth and restrict link/image destinations. Throws with
 * file + offending snippet.
 */
export function assertEscapeFirst(tokens, file) {
  for (const t of walkTokens(tokens)) {
    if (t.type === "html") {
      throw new Error(
        `${file}: raw HTML denied at any depth (escape-first law): ${JSON.stringify(
          String(t.raw).trim().slice(0, 80)
        )}`
      );
    }
    if ((t.type === "link" || t.type === "image") && typeof t.href === "string") {
      try {
        assertDestination(t.href, `${file}: link destination`);
      } catch (err) {
        throw new Error(`${err.message} (escape-first law)`);
      }
    }
  }
}

/**
 * HTML character-reference decode mirroring browser ATTRIBUTE-value
 * semantics (single pass — browsers never re-decode): numeric refs with an
 * optional semicolon (`&#58;`, `&#x3a;`, `&#58` …) plus the known named
 * refs; unknown named refs stay literal exactly as a browser leaves them.
 * Needed because `javascript&colon;alert(1)` carries no raw colon yet
 * executes as `javascript:` once the browser decodes the attribute value.
 */
const NAMED_CHARREFS = new Map(
  Object.entries({
    amp: "&", AMP: "&", lt: "<", LT: "<", gt: ">", GT: ">",
    quot: '"', QUOT: '"', apos: "'", colon: ":", semi: ";",
    sol: "/", bsol: "\\", num: "#", percnt: "%", excl: "!", quest: "?",
    commat: "@", equals: "=", plus: "+", lpar: "(", rpar: ")",
    ast: "*", midast: "*", comma: ",", period: ".", lowbar: "_", grave: "`",
    dollar: "$", verbar: "|", lbrace: "{", rbrace: "}", lsqb: "[", rsqb: "]",
    Tab: "\t", NewLine: "\n", nbsp: "\u00a0",
  })
);

export function decodeAttrCharRefs(value) {
  const src = String(value);
  if (!src.includes("&")) return src;
  return src.replace(
    /&(#[xX][0-9a-fA-F]+|#[0-9]+|[a-zA-Z][a-zA-Z0-9]*);?/g,
    (whole, body) => {
      if (body.startsWith("#")) {
        const cp =
          body[1] === "x" || body[1] === "X"
            ? parseInt(body.slice(2), 16)
            : parseInt(body.slice(1), 10);
        // browser mapping: NUL, surrogates and out-of-range decode to U+FFFD
        if (
          !Number.isFinite(cp) || cp <= 0 || cp > 0x10ffff ||
          (cp >= 0xd800 && cp <= 0xdfff)
        ) {
          return "\uFFFD";
        }
        return String.fromCodePoint(cp);
      }
      return NAMED_CHARREFS.get(body) ?? whole;
    }
  );
}

/**
 * http / https / mailto / relative / #fragment ONLY — closes javascript:.
 * C14 amendment (2026-08-26, R-CT3 HIGH-1): the check judges the DECODED,
 * URL-normalized form. A browser decodes character references inside
 * attribute values and strips tab/newline before URL parsing, so BOTH gates
 * route every destination through this single choke point BEFORE the
 * allowlist — an executable decoded scheme fails naming label + value.
 */
export function assertDestination(href, label) {
  const raw = String(href);
  const decoded = decodeAttrCharRefs(raw);
  // URL parser strips tab/newline anywhere plus leading/trailing C0 + space
  const url = decoded
    .replace(/[\t\n\r]/g, "")
    .replace(/^[\u0000-\u0020]+/, "")
    .replace(/[\u0000-\u0020]+$/, "");
  const scheme = /^([a-zA-Z][a-zA-Z0-9+.-]*):/.exec(url);
  if (scheme) {
    const s = scheme[1].toLowerCase();
    if (s !== "http" && s !== "https" && s !== "mailto") {
      const decodedNote = decoded === raw ? "" : ` (browser-decoded: "${url}")`;
      throw new Error(
        `${label}: protocol "${scheme[1]}:" outside the allowlist in "${raw}"${decodedNote}`
      );
    }
    return;
  }
  if (url.startsWith("//")) {
    throw new Error(`${label}: protocol-relative URL not allowed: "${raw}"`);
  }
}

/* ----- emitted-body re-parse invariants (C14 second half, decidable) ------ */

const ALLOWED_ELEMENTS = new Set([
  "p", "h1", "h2", "h3", "h4", "h5", "h6",
  "ul", "ol", "li", "a", "img", "code", "pre", "blockquote",
  "table", "thead", "tbody", "tr", "th", "td",
  // `input` rides the closed list ONLY under its task-list scope, enforced
  // by the dedicated <input> branch below (leading li child + attr triple)
  "em", "strong", "del", "br", "hr", "span", "input",
]);
const VOID_ELEMENTS = new Set(["br", "hr", "img", "input"]);
const TASK_INPUT_ATTRS = new Set(["type", "disabled", "checked"]);

/**
 * Re-parse an EMITTED body against three decidable invariants (spec C14):
 * element set ⊆ closed markdown-generated allowlist (`input` only as the GFM
 * task-list checkbox marked itself emits — leading child of an li, attributes
 * ⊆ type/disabled/checked, type="checkbox" required); zero event-handler
 * attributes (parsed attribute NAMES matching on*, never substrings); every
 * href/src ∈ http/https/mailto/relative/#fragment (browser-decoded form, see
 * assertDestination). Returns failures ([]=clean).
 */
export function reparseFailures(html, file) {
  const failures = [];
  const stack = [];
  const tagRe = /<(\/?)([a-zA-Z][a-zA-Z0-9-]*)([^<>]*)>/g;
  const liOpenEnds = [];
  let lastLiOpenEnd = -1;
  let m;
  while ((m = tagRe.exec(html))) {
    const [full, closing, rawTag, attrSrc] = m;
    const tag = rawTag.toLowerCase();
    const start = m.index;
    const end = tagRe.lastIndex;
    void full;
    if (closing) {
      if (VOID_ELEMENTS.has(tag)) {
        failures.push(`${file}: void element </${tag}> has no close`);
        continue;
      }
      const top = stack.pop();
      if (tag === "li") lastLiOpenEnd = liOpenEnds.pop() ?? -1;
      if (top !== tag) {
        failures.push(`${file}: mismatched close </${tag}> (open: <${top ?? "none"}>)`);
      }
      continue;
    }
    if (!ALLOWED_ELEMENTS.has(tag)) {
      failures.push(`${file}: element <${tag}> outside the closed allowlist`);
      continue;
    }
    // parsed attribute names — event handlers die here even when quoted oddly
    const attrs = new Map();
    const attrRe = /([a-zA-Z_:][-\w:.]*)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'<>]+)))?/g;
    let am;
    while ((am = attrRe.exec(attrSrc))) {
      attrs.set(am[1].toLowerCase(), am[2] ?? am[3] ?? am[4] ?? "");
    }
    for (const name of attrs.keys()) {
      if (/^on/i.test(name)) {
        failures.push(`${file}: event-handler attribute "${name}" on <${tag}>`);
      }
    }
    if (tag === "input") {
      const bad = [...attrs.keys()].filter((k) => !TASK_INPUT_ATTRS.has(k));
      if (bad.length > 0) {
        failures.push(
          `${file}: <input> attribute outside the task-list triple {type,disabled,checked}: "${bad.sort().join('","')}"`
        );
      }
      if ((attrs.get("type") ?? "") !== "checkbox") {
        failures.push(`${file}: <input> without type="checkbox" (task-list scope only)`);
      }
      const parent = stack[stack.length - 1];
      const sinceLi =
        lastLiOpenEnd >= 0 && start >= lastLiOpenEnd ? html.slice(lastLiOpenEnd, start) : null;
      if (parent !== "li" || sinceLi === null || !/^\s*$/.test(sinceLi)) {
        failures.push(`${file}: <input> must be the leading child of an li (GFM task-list scope)`);
      }
    }
    for (const dest of ["href", "src"]) {
      if (attrs.has(dest)) {
        try {
          assertDestination(attrs.get(dest) || '', `${file}: ${dest} on <${tag}>`);
        } catch (err) {
          failures.push(String(err.message));
        }
      }
    }
    if (!VOID_ELEMENTS.has(tag) && !attrSrc.trim().endsWith("/")) {
      stack.push(tag);
      if (tag === "li") {
        liOpenEnds.push(end);
        lastLiOpenEnd = end;
      }
    }
  }
  for (const open of stack) failures.push(`${file}: unclosed <${open}>`);
  return failures;
}

/* ---------- deterministic entity linking (§4 V3) -------------------------- */

function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Per-entity candidate terms for ONE locale cell: resolved display name
 * (when non-empty) + declared link_terms. Byte-identical terms across ≥2
 * entities suppress linking entirely for those entities (V3 tie-break law).
 */
function candidateTerms(entities, corpus, siteCode) {
  const candidates = []; // {term, entityIdx}
  (entities ?? []).forEach((ref, idx) => {
    if (!corpus.idsByKind.get(ref.kind)?.has(ref.id)) return;
    const entry = corpus.rowsByKind.get(ref.kind)?.find((e) => e.id === ref.id);
    const name = entry
      ? displayName(ref.kind, entry.row, siteCode)
      : "";
    if (name && name.trim() !== "") candidates.push({ term: name, entityIdx: idx });
    for (const t of ref.link_terms ?? []) candidates.push({ term: t, entityIdx: idx });
  });
  const owners = new Map();
  for (const c of candidates) {
    const k = c.term.toLowerCase();
    if (!owners.has(k)) owners.set(k, new Set());
    owners.get(k).add(c.entityIdx);
  }
  return candidates.filter((c) => owners.get(c.term.toLowerCase()).size === 1);
}

/** Whole-token, case-insensitive first match of `term` at/after `from`.
 * Whitespace runs inside the term match any whitespace (markdown reflows
 * paragraphs at 80 cols — a wrapped display name must still link). */
function termPattern(term) {
  return escapeRegExp(term).replace(/\s+/g, "\\s+");
}

function findWholeTerm(text, term, from) {
  const pat = new RegExp(
    `(?<![\\p{L}\\p{N}_])${termPattern(term)}(?![\\p{L}\\p{N}_])`,
    "giu"
  );
  pat.lastIndex = from;
  const m = pat.exec(text);
  return m ? m.index : -1;
}

/** Split the document into fenced (verbatim) vs editable segments. */
function editableSegments(body) {
  const segs = [];
  let fence = null;
  let cur = { text: "", editable: true };
  for (const line of body.split("\n")) {
    const fm = /^\s*(`{3,}|~{3,})/.exec(line);
    if (fence) {
      cur.text += line + "\n";
      if (line.trim().startsWith(fence)) {
        segs.push(cur);
        fence = null;
        cur = { text: "", editable: true };
      }
      continue;
    }
    if (fm) {
      if (cur.text !== "") segs.push(cur);
      cur = { text: line + "\n", editable: false };
      fence = fm[1];
      continue;
    }
    cur.text += line + "\n";
  }
  if (cur.text !== "") segs.push(cur);
  return segs;
}

/**
 * Replace the FIRST whole-token occurrence of each entity's candidate terms
 * with a markdown link; longest-term-first so "Short-haired Mita" wins before
 * "Mita". Fenced blocks and inline code spans stay verbatim. First occurrence
 * per ENTITY per document, in body order (§4 V3).
 */
function injectEntityLinks(body, candidates, hrefFor) {
  if (candidates.length === 0) return body;
  const ordered = [...candidates].sort((a, b) => b.term.length - a.term.length);
  const linked = new Set();

  function linkPass(text) {
    const parts = text.split(/(`[^`\n]*`)/g);
    return parts
      .map((part, i) => {
        if (i % 2 === 1) return part; // inline code span — verbatim
        let pos = 0;
        let out = "";
        for (;;) {
          let best = null;
          for (const cand of ordered) {
            if (linked.has(cand.entityIdx)) continue;
            const idx = findWholeTerm(part, cand.term, pos);
            if (idx === -1) continue;
            if (
              !best ||
              idx < best.idx ||
              (idx === best.idx && cand.term.length > best.cand.term.length)
            ) {
              best = { idx, cand };
            }
          }
          if (!best) break;
          out += part.slice(pos, best.idx);
          const matched = part
            .slice(best.idx)
            .match(new RegExp(`^${termPattern(best.cand.term)}`, "iu"));
          const label = (matched ? matched[0] : best.cand.term).replace(/\s+/g, " ");
          out += `[${label}](${hrefFor(best.cand.entityIdx)})`;
          linked.add(best.cand.entityIdx);
          pos = best.idx + matched[0].length;
        }
        return out + part.slice(pos);
      })
      .join("");
  }

  return editableSegments(body)
    .map((seg) => (seg.editable ? linkPass(seg.text) : seg.text))
    .join("");
}

/* ---------- heading slugs + TOC ------------------------------------------- */

export function slugifyHeading(text) {
  return String(text)
    .toLowerCase()
    .replace(/[\p{P}\p{S}]+/gu, "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-");
}

/** One isolated marked instance per compiled cell (no extension bleed). */
function makeParser(tocSink) {
  const inst = new Marked({ gfm: true });
  const usedIds = new Map();
  inst.use({
    renderer: {
      heading(token) {
        const text = String(token.text ?? "");
        const base = slugifyHeading(text) || "heading";
        const n = usedIds.get(base) ?? 0;
        usedIds.set(base, n + 1);
        const slug = n === 0 ? base : `${base}-${n}`;
        tocSink.push({ id: slug, text, level: token.depth });
        const inner = this.parser.parseInline(token.tokens ?? []);
        return `<h${token.depth} id="${slug}">${inner}</h${token.depth}>\n`;
      },
    },
  });
  return inst;
}

/* ---------- main ----------------------------------------------------------- */

export function emitContent(opts = {}) {
  const contentRoot =
    opts.contentRoot ?? process.env.MISIDE_CONTENT_ROOT ?? join(SITE_ROOT, "content");
  const emitDir =
    opts.emitDir ?? process.env.MISIDE_CONTENT_EMIT ?? join(contentRoot, "emit");
  const extracted =
    opts.extractedRoot ?? process.env.MISIDE_EXTRACTED_ROOT ?? join(SITE_ROOT, "..", "extracted");

  const corpus = loadCorpus();
  const routedIds = (kind) => corpus.idsByKind.get(kind); // undefined ⇒ unknown kind

  // scenes _meta build pins (same derivation as src/data buildId())
  let buildId = process.env.MISIDE_BUILD_ID ?? null;
  let versionLabel = process.env.MISIDE_VERSION_LABEL ?? null;
  {
    const metaRaw = readFileSyncSafe(join(extracted, "data", "scenes", "scenes.jsonl"));
    const firstLine = metaRaw.split("\n").find((l) => l.trim());
    const header = firstLine ? JSON.parse(firstLine) : null;
    const meta = header?._meta ?? header;
    const pins = meta?.build_pins ?? meta?.pins ?? {};
    buildId = buildId ?? pins.buildId ?? pins.build_id ?? String(meta?.build_id ?? "");
    versionLabel = versionLabel ?? pins.versionLabel ?? String(meta?.version_label ?? "");
  }

  /* -- discover cells ------------------------------------------------------ */
  const sections = [
    { dir: "guides", types: new Set(["guide"]) },
    { dir: "news", types: new Set(["game", "database", "patch"]) },
  ];
  const errors = [];
  const articles = new Map(); // "<dir>:<slug>" -> {dir, slug, pivot, translations}

  for (const { dir, types } of sections) {
    const absDir = join(contentRoot, dir);
    let files = [];
    try {
      files = readdirSync(absDir).filter((f) => f.endsWith(".mdx")).sort();
    } catch (err) {
      if (err.code === "ENOENT") continue;
      throw err;
    }
    for (const f of files) {
      const relFile = `${dir}/${f}`;
      const base = f.replace(/\.mdx$/, "");
      let code = PIVOT;
      let slug = base;
      const dot = base.lastIndexOf(".");
      if (dot > 0) {
        const suffix = base.slice(dot + 1);
        if (LOCALE_CODES.has(suffix)) {
          slug = base.slice(0, dot);
          code = suffix;
        }
      }
      let source;
      try {
        source = readFileSync(join(absDir, f), "utf8");
      } catch (err) {
        errors.push(`${relFile}: unreadable (${err.message})`);
        continue;
      }
      let fm, body;
      try {
        ({ fm, body } = parseFrontmatter(source, relFile));
      } catch (err) {
        errors.push(err.message);
        continue;
      }
      if (typeof fm.slug !== "string" || fm.slug !== slug) {
        errors.push(`${relFile}: frontmatter slug "${String(fm.slug)}" != filename slug "${slug}"`);
        continue;
      }
      if (typeof fm.type !== "string" || !types.has(fm.type)) {
        errors.push(`${relFile}: type "${String(fm.type)}" is not routable under /${dir}`);
        continue;
      }
      const key = `${dir}:${slug}`;
      const art =
        articles.get(key) ?? { dir, slug, type: fm.type, pivot: undefined, translations: new Map() };
      const cell = { relFile, fm, body, code };
      if (code === PIVOT) art.pivot = cell;
      else art.translations.set(code, cell);
      articles.set(key, art);
    }
  }

  for (const art of articles.values()) {
    if (!art.pivot) {
      const codes = [...art.translations.keys()].join(", ");
      errors.push(
        `${art.dir}/${art.slug}.{${codes}}.mdx: translation without a pivot ${art.slug}.${PIVOT}.mdx`
      );
    }
  }

  /* -- validate each admitted cell (shape + V1/V2) ------------------------- */
  const published = [];
  for (const art of articles.values()) {
    if (!art.pivot) continue;
    validateCellShape(art.pivot, routedIds, art.dir, errors);
    if (errors.some((e) => e.startsWith(art.pivot.relFile))) continue;
    if (art.pivot.fm.status === "draft") {
      console.log(`DRAFT-SKIPPED: ${art.pivot.relFile} (V5: drafts never reach the registry)`);
      continue;
    }
    for (const cell of art.translations.values()) {
      validateCellShape(cell, routedIds, art.dir, errors);
      if (cell.fm.status === "draft") {
        console.log(`DRAFT-SKIPPED: ${cell.relFile} (cell omitted, V5)`);
        continue;
      }
      if (errors.some((e) => e.startsWith(cell.relFile))) continue;
      const pk = entityKeySet(art.pivot.fm.entities ?? []);
      const tk = entityKeySet(cell.fm.entities ?? []);
      if (pk !== tk) {
        errors.push(`${cell.relFile}: declared entity set differs from the pivot (link-graph parity)`);
      }
    }
    if (errors.length > 0) continue; // any error aborts the whole run below
    published.push(art);
  }

  if (errors.length > 0) {
    for (const e of errors) console.error(`content ERROR: ${e}`);
    console.error(`build-content FAIL: ${errors.length} validation error(s)`);
    return { ok: false, errors };
  }

  /* -- compile each admitted cell (escape-first, then render) -------------- */
  // R-CT3 MED-2 ordering law: bodies compile into a STAGING dir that swaps in
  // only after EVERY cell compiled and validated. A failed emit must leave the
  // previously compiled bodies (and the registry/ledger that reference them)
  // fully intact — half-deleted emit dirs are the defect this kills.
  const bodiesDir = join(emitDir, "bodies");
  const stagingDir = join(emitDir, ".bodies.staging");
  const previousDir = join(emitDir, ".bodies.previous");
  mkdirSync(emitDir, { recursive: true });
  rmSync(stagingDir, { recursive: true, force: true });
  if (existsSync(previousDir)) {
    // self-heal an interrupted swap: `.bodies.previous` holding the only copy
    // of the bodies means the last run died mid-swap — put them back
    if (!existsSync(bodiesDir)) renameSync(previousDir, bodiesDir);
    else rmSync(previousDir, { recursive: true, force: true });
  }
  let stagedBodiesSwapped = false;

  const prevRows = new Map(readRegistry(emitDir).map((r) => [r.article_id, r]));
  const prevCells = new Map(readLedger(emitDir).map((r) => [r.cell, r]));

  const registryRows = [];
  const ledgerRows = [];

  /** Failure carrier so per-cell validation can abort the compile pass while
   * the caller still returns the same {ok:false} shape it always did. */
  const failCompile = (errors) => {
    throw Object.assign(new Error(errors[0] ?? "content compile failed"), { errors });
  };

  const compileAndStage = () => {
  for (const art of published) {
    const articleId = `${art.dir === "guides" ? "guide" : art.type}:${art.slug}`;
    const localesOut = {};
    const tocByLocale = new Map();

    const pivotSha = sha16(readFileSync(join(contentRoot, art.pivot.relFile), "utf8"));

    const cellsToCompile = [
      ["en", art.pivot],
      ...[...art.translations.entries()].filter(([, c]) => c.fm.status !== "draft"),
    ];

    for (const [code, cell] of cellsToCompile) {
      const localeDef = LOCALES.find((l) => l.code === code);
      if (!localeDef) throw new Error(`unknown locale cell: ${code}`);
      const siteCode = localeDef.code;
      const prefix = localeDef.prefix;
      const sectionSegment = art.dir; // guides | news

      // V3: deterministic links from the declared set, resolved THIS locale
      const candidates = candidateTerms(art.pivot.fm.entities ?? [], corpus, siteCode);
      const linkedBody = injectEntityLinks(cell.body, candidates, (entityIdx) => {
        const ref = (art.pivot.fm.entities ?? [])[entityIdx];
        return `${prefix}/${KIND_SEGMENT[ref.kind]}/${ref.id}`;
      });

      const tokens = new Marked().lexer(linkedBody);
      try {
        assertEscapeFirst(tokens, cell.relFile);
      } catch (err) {
        console.error(`content ERROR: ${err.message}`);
            failCompile([String(err.message)]);
      }

      const toc = [];
      let html;
      try {
        html = makeParser(toc).parse(linkedBody, { async: false });
      } catch (err) {
        console.error(`content ERROR: ${cell.relFile}: render failed (${err.message})`);
            failCompile([String(err.message)]);
      }

      // C14 second half: the EMITTED html must re-parse clean
      const reparse = reparseFailures(html, cell.relFile);
      if (reparse.length > 0) {
        for (const f of reparse) console.error(`content ERROR: ${f}`);
            failCompile(reparse);
      }

      // embed anchors must resolve inside THIS cell's headings (loud, not silent)
      for (const emb of cell.fm.embeds ?? []) {
        if (emb.after !== undefined && !toc.some((h) => h.id === emb.after)) {
          const msg = `${cell.relFile}: embed "${emb.id}" after:"${emb.after}" matches no heading in this cell`;
          console.error(`content ERROR: ${msg}`);
                failCompile([msg]);
        }
      }

      const wordCount = wordCountOf(html);
      mkdirSync(join(stagingDir, sectionSegment), { recursive: true });
      writeFileSync(join(stagingDir, sectionSegment, `${art.slug}.${code}.html`), html, "utf8");

      // ledger admission: an own-file change stamps BOTH hashes fresh
      const ownSha = sha16(readFileSync(join(contentRoot, cell.relFile), "utf8"));
      const cellId = `${articleId}@${code}`;
      const prevCell = prevCells.get(cellId);
      const readmitted = !prevCell || prevCell.body_sha16 !== ownSha;
      const baseSha =
        code === PIVOT ? undefined : readmitted ? pivotSha : (prevCell.base_sha16 ?? pivotSha);
      const transStale = code !== PIVOT && baseSha !== pivotSha;
      if (transStale) {
        console.log(`TRANSLATION-STALE: ${articleId}@${code} <- pivot moved`);
      }

      ledgerRows.push({
        cell: cellId,
        article_id: articleId,
        locale: code,
        path: `${prefix}/${sectionSegment}/${art.slug}`,
        title: String(cell.fm.title),
        description: String(cell.fm.description),
        word_count: wordCount,
        body_sha16: ownSha,
        ...(baseSha ? { base_sha16: baseSha } : {}),
        pivot: code === PIVOT,
        stale: transStale,
      });

      localesOut[code] = {
        path: `${prefix}/${sectionSegment}/${art.slug}`,
        title: String(cell.fm.title),
        description: String(cell.fm.description),
        word_count: wordCount,
        body_sha16: ownSha,
        ...(baseSha ? { base_sha16: baseSha } : {}),
        toc,
        // R-CT3 HIGH-2: each locale cell carries its OWN embed declarations
        // (anchors resolved against this cell's headings above, props in this
        // cell's language) — pivot-only anchors never match a translated
        // body, which is how /ru guides silently lost every anchored embed.
        embeds: Array.isArray(cell.fm.embeds) ? cell.fm.embeds : [],
        body_ref: `${sectionSegment}/${art.slug}.${code}.html`,
        stale: transStale,
      };
      tocByLocale.set(code, toc);
    }

    // entity row hashes — recomputed every run; drift flips the article stale
    const entityRowHashes = {};
    let stale = false;
    for (const ref of art.pivot.fm.entities ?? []) {
      const entry = corpus.rowsByKind.get(ref.kind)?.find((e) => e.id === ref.id);
      if (!entry) continue;
      const h = sha16(JSON.stringify(entry.row));
      entityRowHashes[`${ref.kind}:${ref.id}`] = h;
      const prevHash = prevRows.get(articleId)?.entity_row_hashes?.[`${ref.kind}:${ref.id}`];
      if (prevHash !== undefined && prevHash !== h) {
        stale = true;
        console.log(`STALE: ${articleId} <- ${ref.kind}:${ref.id} (field-level diff omitted)`);
      }
    }

    registryRows.push({
      article_id: articleId,
      type: art.dir === "guides" ? "guide" : art.type,
      slug: art.slug,
      title_en: String(art.pivot.fm.title),
      locales: localesOut,
      entities: (art.pivot.fm.entities ?? []).map(({ kind, id }) => ({ kind, id })),
      entity_row_hashes: entityRowHashes,
      toc: tocByLocale.get(PIVOT) ?? [],
      spoiler: art.pivot.fm.spoiler,
      verified_build_id: String(art.pivot.fm.verified_build_id),
      published_at: String(art.pivot.fm.published_at),
      updated_at: String(art.pivot.fm.updated_at ?? art.pivot.fm.published_at),
      status: "published",
      stale,
      steps: Array.isArray(art.pivot.fm.steps) ? art.pivot.fm.steps : [],
      embeds: Array.isArray(art.pivot.fm.embeds) ? art.pivot.fm.embeds : [],
      body_ref: localesOut[PIVOT]?.body_ref ?? "",
    });
  }
  }; // end compileAndStage

  try {
    compileAndStage();
    // Every cell compiled + validated — only NOW do the old bodies move
    // aside. The swap is old→previous, staged→bodies with restore-on-fail:
    // a rename hiccup (Windows file lock) must never leave the tree without
    // the bodies the current registry still references (R-CT3 MED-2).
    rmSync(previousDir, { recursive: true, force: true });
    let movedOld = false;
    if (existsSync(bodiesDir)) {
      renameSync(bodiesDir, previousDir);
      movedOld = true;
    }
    try {
      renameSync(stagingDir, bodiesDir);
    } catch (swapErr) {
      if (movedOld) renameSync(previousDir, bodiesDir); // put the old set back
      throw swapErr;
    }
    rmSync(previousDir, { recursive: true, force: true });
    stagedBodiesSwapped = true;
  } catch (err) {
    if (err && Array.isArray(err.errors)) {
      return { ok: false, errors: err.errors };
    }
    throw err;
  } finally {
    if (!stagedBodiesSwapped) {
      // no staging debris; `.bodies.previous` survives ONLY when it is still
      // the sole copy of the old bodies (restore failed) — swept next run
      rmSync(stagingDir, { recursive: true, force: true });
      if (existsSync(bodiesDir)) {
        rmSync(previousDir, { recursive: true, force: true });
      }
    }
  }

  /* -- write artifacts ------------------------------------------------------ */
  const streams = { guide: 0, game: 0, database: 0, patch: 0 };
  for (const row of registryRows) streams[row.type] += 1;

  registryRows.sort(
    (a, b) =>
      a.published_at === b.published_at
        ? b.slug.localeCompare(a.slug)
        : b.published_at.localeCompare(a.published_at) // newest first
  );
  ledgerRows.sort((a, b) => a.cell.localeCompare(b.cell));

  writeJsonl(
    join(emitDir, "articles.jsonl"),
    {
      schema: "miside.content.articles/1",
      generator: "scripts/build-content.mjs",
      build_id: buildId,
      version_label: versionLabel,
      row_count: registryRows.length,
      streams,
    },
    registryRows
  );
  writeJsonl(
    join(emitDir, "article_locales.jsonl"),
    {
      schema: "miside.content.article_locales/1",
      generator: "scripts/build-content.mjs",
      build_id: buildId,
      row_count: ledgerRows.length,
    },
    ledgerRows
  );

  console.log(
    `build-content OK: ${registryRows.length} article(s), ${ledgerRows.length} locale cell(s), streams ${JSON.stringify(streams)}, build ${buildId}`
  );
  return { ok: true, registryRows, ledgerRows, meta: { schema: "miside.content.articles/1", build_id: buildId, streams } };
}

/* ---------- helpers --------------------------------------------------------- */

function readFileSyncSafe(p) {
  try {
    return readFileSync(p, "utf8");
  } catch {
    return "";
  }
}

function entityKeySet(entities) {
  if (!Array.isArray(entities)) return "";
  return entities.map((e) => `${e.kind}:${e.id}`).sort().join("|");
}

function wordCountOf(html) {
  const text = html.replace(/<[^>]+>/g, " ").replace(/&[a-z#0-9]+;/gi, " ");
  const words = text.match(/[\p{L}\p{N}'’-]+/gu);
  return words ? words.length : 0;
}

/** _meta-pinned jsonl reader for OUR OWN emit artifacts (throw on drift). */
function readJsonlRows(path) {
  let raw;
  try {
    raw = readFileSync(path, "utf8");
  } catch (err) {
    if (err.code === "ENOENT") return [];
    throw err;
  }
  const lines = raw.split("\n").filter((l) => l.trim());
  if (lines.length === 0) return [];
  const first = JSON.parse(lines[0]);
  let start = 0;
  if (first && typeof first === "object" && ("_meta" in first || "schema" in first)) {
    const meta = first._meta ?? first;
    start = 1;
    const dataCount = lines.length - start;
    if (typeof meta.row_count === "number" && meta.row_count !== dataCount) {
      throw new Error(`${path}: _meta.row_count=${meta.row_count} but ${dataCount} data rows`);
    }
  }
  return lines.slice(start).map((l) => JSON.parse(l));
}

function readRegistry(emitDir) {
  return readJsonlRows(join(emitDir, "articles.jsonl")).filter((r) => r.article_id !== undefined);
}

function readLedger(emitDir) {
  return readJsonlRows(join(emitDir, "article_locales.jsonl")).filter((r) => r.cell !== undefined);
}

function writeJsonl(path, meta, rows) {
  mkdirSync(dirname(path), { recursive: true });
  const lines = [JSON.stringify({ _meta: meta }), ...rows.map((r) => JSON.stringify(r))];
  writeFileSync(path, lines.join("\n") + "\n", "utf8");
}

/** Exported for the test lane: verdict parity with content/_schema/frontmatter.ts */
export function validateCellShape(cell, routedIds, dir, errors) {
  const fm = cell.fm;
  const fail = (msg) => errors.push(`${cell.relFile}: ${msg}`);
  const KNOWN = [
    "type", "slug", "title", "description", "status", "published_at",
    "updated_at", "verified_build_id", "spoiler", "entities", "steps", "embeds",
  ];
  for (const k of Object.keys(fm)) {
    if (!KNOWN.includes(k)) fail(`unknown frontmatter key "${k}"`);
  }
  const TYPES = ["guide", "game", "database", "patch"];
  const STATUSES = ["draft", "published"];
  const SPOILERS = ["none", "mild", "full"];
  if (!TYPES.includes(fm.type)) fail(`type: must be one of ${TYPES.join(" | ")}`);
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(String(fm.slug))) fail("slug: kebab-case required");
  if (typeof fm.title !== "string" || fm.title.trim() === "") fail("title: required non-empty string");
  if (typeof fm.description !== "string" || fm.description.trim() === "") {
    fail("description: required non-empty string");
  } else if ([...fm.description].length > 160) {
    fail(`description: ${[...fm.description].length} chars > 160`);
  }
  if (!STATUSES.includes(fm.status)) fail("status: draft | published");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(fm.published_at))) fail("published_at: YYYY-MM-DD required");
  if (fm.updated_at !== undefined && !/^\d{4}-\d{2}-\d{2}$/.test(String(fm.updated_at))) {
    fail("updated_at: YYYY-MM-DD required");
  }
  if (typeof fm.verified_build_id !== "string" || !/^\d+$/.test(fm.verified_build_id)) {
    fail("verified_build_id: quoted numeric string required");
  }
  if (!SPOILERS.includes(fm.spoiler)) fail("spoiler: none | mild | full");
  if (fm.steps !== undefined) {
    if (!Array.isArray(fm.steps)) fail("steps: must be a list");
    else if (fm.type !== "guide") fail("steps: guides only");
  }

  // entities[] — V1 resolution + V2 vocabulary
  if (!Array.isArray(fm.entities)) {
    fail("entities: must be a list");
  } else {
    if (fm.entities.length === 0 && dir === "guides") {
      fail("entities: guides require >=1 entity (they are entity-linked by definition)");
    }
    fm.entities.forEach((e, i) => {
      if (!e || typeof e !== "object" || Array.isArray(e)) {
        fail(`entities[${i}]: expected "<kind>: <id>"`);
        return;
      }
      const { kind, id, link_terms } = e;
      if (typeof kind !== "string" || typeof id !== "string") {
        fail(`entities[${i}]: expected "<kind>: <id>"`);
        return;
      }
      if (link_terms !== undefined) {
        if (!Array.isArray(link_terms) || link_terms.some((t) => typeof t !== "string" || t.trim() === "")) {
          fail(`entities[${i}].link_terms: list of non-empty strings`);
          return;
        }
      }
      const ids = routedIds(kind);
      if (ids === undefined) {
        fail(`entities[${i}]: "${kind}" is not a routed kind (V2)`);
        return;
      }
      if (!ids.has(id)) {
        fail(`entities[${i}]: ${kind}:${id} does not resolve through the contract id column (V1)`);
      }
    });
  }

  // embeds[] against the closed module map (§5)
  if (fm.embeds !== undefined) {
    if (!Array.isArray(fm.embeds)) {
      fail("embeds: must be a list");
      return;
    }
    const MODULES = ["map-scene", "entity-cards", "checklist"];
    const seen = new Set();
    fm.embeds.forEach((emb, i) => {
      if (!emb || typeof emb !== "object" || Array.isArray(emb)) {
        fail(`embeds[${i}]: expected a mapping`);
        return;
      }
      const { id, after, module: mod, props } = emb;
      if (typeof id !== "string" || id.trim() === "") {
        fail(`embeds[${i}].id: anchor id required`);
      } else if (seen.has(id)) {
        fail(`embeds[${i}].id: duplicate embed id "${id}"`);
      } else seen.add(id);
      if (after !== undefined && (typeof after !== "string" || after === "")) {
        fail(`embeds[${i}].after: heading id or omit`);
      }
      if (typeof mod !== "string" || !MODULES.includes(mod)) {
        fail(`embeds[${i}].module: must be one of ${MODULES.join(" | ")}`);
      }
      if (!props || typeof props !== "object" || Array.isArray(props)) {
        fail(`embeds[${i}].props: mapping required`);
        return;
      }
      const keys = Object.keys(props);
      if (mod === "map-scene") {
        for (const k of keys) {
          if (!["scene_id", "focus_poi_id", "height"].includes(k))
            fail(`embeds[${i}].props.${k}: not a map-scene prop`);
        }
        if (typeof props.scene_id !== "string") fail(`embeds[${i}].props.scene_id: required string`);
      } else if (mod === "entity-cards") {
        for (const k of keys) {
          if (k !== "title") fail(`embeds[${i}].props.${k}: not an entity-cards prop`);
        }
      } else if (mod === "checklist") {
        for (const k of keys) {
          if (k !== "items" && k !== "title") fail(`embeds[${i}].props.${k}: not a checklist prop`);
        }
        if (!Array.isArray(props.items) || props.items.length === 0) {
          fail(`embeds[${i}].props.items: non-empty list required`);
        } else {
          props.items.forEach((it, j) => {
            if (!it || typeof it !== "object" || Array.isArray(it) || typeof it.text !== "string") {
              fail(`embeds[${i}].props.items[${j}]: {text, keys?, danger?} required`);
            } else if (
              it.keys !== undefined &&
              (!Array.isArray(it.keys) || it.keys.some((k) => typeof k !== "string"))
            ) {
              fail(`embeds[${i}].props.items[${j}].keys: string list required`);
            }
          });
        }
      }
    });
  }
}

/* ---------- CLI entry ------------------------------------------------------- */
const invokedDirectly =
  process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (invokedDirectly) {
  const result = emitContent();
  if (!result.ok) process.exit(1); // CLI: loud failure; library callers check .ok
}
