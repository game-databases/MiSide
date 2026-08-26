/*
 * Content pipeline suites (content-pipeline spec §11): C14 escape-first
 * enforcement end-to-end, C15 pivot-move staleness off base-hash semantics,
 * C1 validation mutations, C2 admission equality (ledger ⇔ registry ⇔ route
 * params), C5 feed shape, and mjs⇔ts validator verdict parity.
 *
 * Fixtures are generated into per-test temp content roots — the real tree in
 * site/content is never mutated.
 */
import "./registerAliasLoader.mjs";

import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  emitContent,
  reparseFailures,
  assertDestination,
  validateCellShape,
  slugifyHeading,
} from "../scripts/build-content.mjs";
import { buildRssChannel } from "../src/lib/rss.ts";
import { validateFrontmatter } from "../content/_schema/frontmatter.ts";

function freshRoot() {
  const root = mkdtempSync(join(tmpdir(), "miside-content-"));
  mkdirSync(join(root, "guides"), { recursive: true });
  mkdirSync(join(root, "news"), { recursive: true });
  return root;
}

const FM_BASE = [
  "---",
  'type: guide',
  "slug: {slug}",
  'title: "Fixture guide"',
  'description: "A fixture guide body for the pipeline tests."',
  "status: published",
  "published_at: 2026-08-26",
  'verified_build_id: "19029065"',
  "spoiler: none",
].join("\n");

function writeGuide(root, name, { front = "", body = "Hello fixture.\n\n## Head\n\nText.\n" } = {}) {
  const slug = name.replace(/\.en$|\.ru$/, "");
  const fm =
    FM_BASE.replace("{slug}", slug) +
    (front ? "\n" + front : "") +
    "\nentities:\n" +
    "  - locations: level13\n" +
    "embeds: []\n---\n\n";
  writeFileSync(join(root, "guides", `${name}.mdx`), fm + body, "utf8");
}

function run(root) {
  const logs = [];
  const origLog = console.log;
  console.log = (...a) => logs.push(a.join(" "));
  try {
    const result = emitContent({
      contentRoot: root,
      emitDir: join(root, "emit"),
    });
    return { result, logs };
  } finally {
    console.log = origLog;
  }
}

/* ------------------------------------------------------------------ */
/* C14 — escape-first renderer law                                     */
/* ------------------------------------------------------------------ */

describe("C14 lexer gate denies raw HTML at any depth", () => {
  const violations = [
    ["inline html", "Run <b>bold</b> text now.\n"],
    ["script block", "<script>alert(1)</script>\n"],
    ["img onerror", 'Look ![alt](https://example.com/x.png) and <img onerror="alert(1)">.\n'],
    ["javascript href", "[click me](javascript:alert(1))\n"],
  ];
  for (const [name, body] of violations) {
    test(`build fails naming file + token: ${name}`, () => {
      const root = freshRoot();
      try {
        writeGuide(root, "viol.en", { body });
        const { result } = run(root);
        assert.equal(result.ok, false);
        const err = (result.errors ?? []).join("\n");
        assert.match(err, /guides\/viol\.en\.mdx/);
        if (name === "javascript href") {
          assert.match(err, /javascript:/);
          assert.match(err, /allowlist|protocol/i);
        } else if (name === "img onerror") {
          assert.match(err, /onerror/);
        } else {
          assert.match(err, /HTML denied|<b>|<script>/i);
        }
      } finally {
        rmSync(root, { recursive: true, force: true });
      }
    });
  }

  test("clean tree exits ok with zero violations", () => {
    const root = freshRoot();
    try {
      writeGuide(root, "clean.en", {});
      const { result } = run(root);
      assert.equal(result.ok, true);
      assert.equal(result.registryRows.length, 1);
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
});

describe("C14 emitted-body re-parse invariants", () => {
  test("GFM table scaffolding and task-list checkboxes pass the widened allowlist", () => {
    const root = freshRoot();
    try {
      const body = [
        "| a | b |",
        "| --- | --- |",
        "| 1 | 2 |",
        "",
        "- [ ] open task",
        "- [x] done task",
        "",
      ].join("\n");
      writeGuide(root, "wide.en", { body });
      const { result } = run(root);
      assert.equal(result.ok, true);
      const html = readFileSync(
        join(root, "emit", "bodies", "guides", "wide.en.html"),
        "utf8"
      );
      for (const el of ["thead", "tbody", "tr", "th", "td"]) {
        assert.ok(html.includes(`<${el}`), `emitted table must contain ${el}`);
      }
      assert.match(html, /<li><input disabled="" type="checkbox">/);
      // the leading-child checkbox is exactly what marked emits — clean
      assert.deepEqual(reparseFailures(html, "wide.en.html"), []);
      // positive pin on synthetic fragments of the same families
      assert.deepEqual(
        reparseFailures("<table><thead><tr><th>x</th></tr></thead></table>", "f"),
        []
      );
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });

  test("synthetic emitted fragments fail naming element/attribute", () => {
    const cases = [
      ['<p><img onclick="x()" src="a.png"></p>', /onclick/, "event handler"],
      ["<embed src=\"x.swf\">", /embed/, "outside allowlist"],
      ["<ul><li><input type=\"text\"></li></ul>", /type="checkbox"/, "wrong input type"],
      ["<ul><li><input type=\"checkbox\" value=\"x\"></li></ul>", /value/, "attr outside triple"],
      ['<p><a href="javascript:x()">y</a></p>', /javascript:/, "bad destination"],
      ["<ul><li>text first<input type=\"checkbox\"></li></ul>", /leading child/, "non-leading input"],
    ];
    for (const [html, pattern, label] of cases) {
      const failures = reparseFailures(html, "fixture.html");
      assert.ok(failures.length > 0, `${label}: expected failures`);
      assert.match(failures.join("\n"), pattern, `${label}: message must name the cause`);
    }
    // negative control: the exact task-list emission shape stays clean
    assert.deepEqual(
      reparseFailures('<ul>\n<li><input disabled="" type="checkbox"> ok</li>\n</ul>', "ok.html"),
      []
    );
  });
});

/* ------------------------------------------------------------------ */
/* C14 amendment — character-reference destinations decode BEFORE the  */
/* allowlist check (R-CT3 HIGH-1: &colon; / &#58; / &#x3a; hole)       */
/* ------------------------------------------------------------------ */

describe("C14 amendment: charref destinations decode before check at BOTH gates", () => {
  const mutations = [
    ["named &colon;", "[click me](javascript&colon;alert(1))\n"],
    ["decimal &#58;", "[click me](javascript&#58;alert(1))\n"],
    ["hex &#x3a;", "[click me](javascript&#x3a;alert(1))\n"],
    ["tab smuggle &#9;", "[click me](jav&#9;ascript:alert(1))\n"],
  ];
  for (const [name, body] of mutations) {
    test(`lexer gate fails naming file + decoded scheme: ${name}`, () => {
      const root = freshRoot();
      try {
        writeGuide(root, "charref.en", { body });
        const { result } = run(root);
        assert.equal(result.ok, false, `${name}: must not emit`);
        const err = (result.errors ?? []).join("\n");
        assert.match(err, /guides\/charref\.en\.mdx/);
        assert.match(err, /javascript:/, "message must name the DECODED scheme");
        assert.match(err, /allowlist|protocol/i);
      } finally {
        rmSync(root, { recursive: true, force: true });
      }
    });
  }

  test("emitted re-parse gate catches the same shapes in attribute values", () => {
    for (const href of [
      "javascript&colon;alert(1)",
      "javascript&#58;alert(1)",
      "javascript&#x3a;alert(1)",
      "jav&#9;ascript:alert(1)",
    ]) {
      const failures = reparseFailures(
        `<p><a href="${href}">y</a></p>`,
        "fixture.html"
      );
      assert.ok(failures.length > 0, `${href}: expected failures`);
      assert.match(failures.join("\n"), /javascript:/);
      assert.match(failures.join("\n"), /allowlist|protocol/i);
    }
  });

  test("assertDestination pins: legit destinations pass, decoded schemes fail", () => {
    const allowed = [
      "https://example.com/page",
      "http://example.com",
      "mailto:someone@example.com",
      "/relative/path#fragment",
      "#fragment",
      "guides/some-guide",
      // authored entity stays a URL ampersand after decode — still https
      "https://example.com/?a=1&amp;b=2",
      "a&b.html",
    ];
    for (const dest of allowed) {
      assert.doesNotThrow(() => assertDestination(dest, "pin"), dest);
    }
    for (const dest of [
      "javascript&colon;alert(1)",
      "javascript&#58;alert(1)",
      "javascript&#x3a;alert(1)",
      "&#106;avascript&colon;alert(1)",
      "data&colon;text/html,x",
      "//protocol.relative",
    ]) {
      assert.throws(() => assertDestination(dest, "pin"), undefined, dest);
    }
  });

  test("clean tree with legit link flavors emits ok and re-parses clean", () => {
    const root = freshRoot();
    try {
      const body = [
        "See [docs](https://example.com/?a=1&amp;b=2), [mail](mailto:a@b.c),",
        "[rel](/guides/x) and [frag](#head-two).",
        "",
        "## Head two",
        "",
        "More text.",
        "",
      ].join("\n");
      writeGuide(root, "legit.en", { body });
      const { result } = run(root);
      assert.equal(result.ok, true);
      const html = readFileSync(
        join(root, "emit", "bodies", "guides", "legit.en.html"),
        "utf8"
      );
      for (const needle of [
        'href="https://example.com/?a=1&amp;b=2"',
        'href="mailto:a@b.c"',
        'href="/guides/x"',
        'href="#head-two"',
      ]) {
        assert.ok(html.includes(needle), `emitted body must keep ${needle}`);
      }
      assert.deepEqual(reparseFailures(html, "legit.en.html"), []);
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
});

/* ------------------------------------------------------------------ */
/* R-CT3 HIGH-2 — registry locale cells carry their OWN embed anchors  */
/* ------------------------------------------------------------------ */

describe("per-locale embeds: translated pages resolve anchors from their OWN cell", () => {
  function writeEmbedFixture(root) {
    const fm = (lang, anchorA, anchorB) =>
      [
        "---",
        "type: guide",
        "slug: embed-fixture",
        `title: "Embed ${lang}"`,
        `description: "${lang} description."`,
        "status: published",
        "published_at: 2026-08-26",
        'verified_build_id: "19029065"',
        "spoiler: none",
        "entities:",
        "  - locations: level13",
        "embeds:",
        "  - id: photo-route-checklist",
        `    after: ${anchorA}`,
        "    module: checklist",
        "    props:",
        `      title: Checklist ${lang}`,
        "      items:",
        `        - text: Step ${lang}`,
        "  - id: cards-grid",
        `    after: ${anchorB}`,
        "    module: entity-cards",
        "    props:",
        `      title: Cards ${lang}`,
        "---",
        "",
      ].join("\n");
    writeFileSync(
      join(root, "guides", "embed-fixture.mdx"),
      fm("EN", "en-heading-a", "en-heading-b") +
        "Intro.\n\n## En heading a\n\nText.\n\n## En heading b\n\nText.\n",
      "utf8"
    );
    writeFileSync(
      join(root, "guides", "embed-fixture.ru.mdx"),
      fm("RU", "ру-заголовок-а", "ру-заголовок-б") +
        "Вводная.\n\n## Ру заголовок а\n\nТекст.\n\n## Ру заголовок б\n\nТекст.\n",
      "utf8"
    );
  }

  test("registry carries per-cell anchors and both bodies resolve them", () => {
    const root = freshRoot();
    try {
      writeEmbedFixture(root);
      const { result } = run(root);
      assert.equal(result.ok, true);

      const row = result.registryRows.find((r) => r.slug === "embed-fixture");
      assert.ok(row);
      // pivot top-level embeds unchanged…
      assert.deepEqual(
        row.embeds.map((e) => e.after),
        ["en-heading-a", "en-heading-b"]
      );
      // …but EACH cell carries its own anchors + props
      assert.deepEqual(row.locales.en.embeds.map((e) => e.after), ["en-heading-a", "en-heading-b"]);
      assert.deepEqual(row.locales.ru.embeds.map((e) => e.after), ["ру-заголовок-а", "ру-заголовок-б"]);
      assert.equal(row.locales.ru.embeds[0].props.title, "Checklist RU");

      // serve-time resolution (ArticleRoute.interleave semantics): each
      // anchored embed's regex must MATCH its own locale's compiled body
      const interleaveRe = (anchor) =>
        new RegExp(`<h[1-6] id="${anchor}"[^>]*>[\\s\\S]*?</h[1-6]>`, "i");
      for (const code of ["en", "ru"]) {
        const html = readFileSync(
          join(root, "emit", "bodies", "guides", `embed-fixture.${code}.html`),
          "utf8"
        );
        for (const emb of row.locales[code].embeds) {
          if (emb.after === undefined) continue;
          assert.match(html, interleaveRe(emb.after), `${code}: ${emb.id}`);
        }
      }
      // the defect this replaces: PIVOT anchors do NOT exist in the RU body,
      // which is exactly why registry pivot-only anchors lost the embeds
      const ruHtml = readFileSync(
        join(root, "emit", "bodies", "guides", "embed-fixture.ru.html"),
        "utf8"
      );
      assert.doesNotMatch(ruHtml, /id="en-heading-a"/);
      assert.doesNotMatch(ruHtml, interleaveRe("en-heading-a"));
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
});

/* ------------------------------------------------------------------ */
/* R-CT3 MED-2 — failed emit must not destroy previously compiled      */
/* bodies (validate first, swap atomically)                            */
/* ------------------------------------------------------------------ */

describe("failed emit preserves the previously emitted artifacts", () => {
  test("bad second article leaves first article's body byte-identical", () => {
    const root = freshRoot();
    try {
      writeGuide(root, "keep.en", {});
      const first = run(root);
      assert.equal(first.result.ok, true);
      const bodyPath = join(root, "emit", "bodies", "guides", "keep.en.html");
      const before = readFileSync(bodyPath, "utf8");

      writeGuide(root, "broken.en", { body: "Run <b>bold</b> now.\n" });
      const { result } = run(root);
      assert.equal(result.ok, false);
      // old bodies survive AND no staging debris is left behind
      assert.equal(readFileSync(bodyPath, "utf8"), before);
      assert.ok(!existsSync(join(root, "emit", ".bodies.staging")));
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });

  test("successful rerun swaps staged bodies in and leaves no staging dir", () => {
    const root = freshRoot();
    try {
      writeGuide(root, "swap.en", {});
      const { result } = run(root);
      assert.equal(result.ok, true);
      assert.ok(existsSync(join(root, "emit", "bodies", "guides", "swap.en.html")));
      assert.ok(!existsSync(join(root, "emit", ".bodies.staging")));
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
});

/* ------------------------------------------------------------------ */
/* R-CT3 MED-1 — the ledger is the RUNTIME admission gate (§8.1)       */
/* ------------------------------------------------------------------ */

describe("article_locales.jsonl gates admission at runtime", () => {
  function writeEmitPair(root, { registryLocales, ledgerLocales, withLedger = true }) {
    mkdirSync(join(root, "emit"), { recursive: true });
    const locales = Object.fromEntries(
      registryLocales.map((code) => [
        code,
        {
          path: code === "en" ? "/guides/g" : `/${code}/guides/g`,
          title: `T ${code}`,
          description: `D ${code}`,
          word_count: 10,
          toc: [],
          body_ref: `guides/g.${code}.html`,
        },
      ])
    );
    writeFileSync(
      join(root, "emit", "articles.jsonl"),
      [
        JSON.stringify({ _meta: { schema: "miside.content.articles/1", row_count: 1 } }),
        JSON.stringify({ article_id: "guide:g", type: "guide", slug: "g", title_en: "T en", locales }),
      ].join("\n") + "\n",
      "utf8"
    );
    if (withLedger) {
      const lines = ledgerLocales.map((code) =>
        JSON.stringify({
          cell: `guide:g@${code}`,
          article_id: "guide:g",
          locale: code,
          path: code === "en" ? "/guides/g" : `/${code}/guides/g`,
          stale: false,
        })
      );
      writeFileSync(
        join(root, "emit", "article_locales.jsonl"),
        JSON.stringify({ _meta: { schema: "miside.content.article_locales/1", row_count: lines.length } }) +
          "\n" + lines.join("\n") + "\n",
        "utf8"
      );
    }
  }

  async function withContentRoot(root, fn) {
    const prev = process.env.MISIDE_CONTENT_ROOT;
    process.env.MISIDE_CONTENT_ROOT = root;
    try {
      return await fn(await import("../src/data/articles.ts"));
    } finally {
      if (prev === undefined) delete process.env.MISIDE_CONTENT_ROOT;
      else process.env.MISIDE_CONTENT_ROOT = prev;
    }
  }

  test("agreeing pair serves EXACTLY the ledger membership", async () => {
    const root = mkdtempSync(join(tmpdir(), "miside-ledger-"));
    try {
      await withContentRoot(root, async (articles) => {
        writeEmitPair(root, { registryLocales: ["en", "ru"], ledgerLocales: ["en", "ru"] });
        const rows = articles.publishedArticles();
        assert.equal(rows.length, 1);
        assert.deepEqual(Object.keys(rows[0].locales), ["en", "ru"]);
        assert.deepEqual(
          articles.articleLocaleCells().map((c) => c.cell),
          ["guide:g@en", "guide:g@ru"]
        );
      });
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });

  test("a registry-only cell refuses to serve (mirror never admits)", async () => {
    const root = mkdtempSync(join(tmpdir(), "miside-ledger-"));
    try {
      await withContentRoot(root, async (articles) => {
        writeEmitPair(root, { registryLocales: ["en", "ru"], ledgerLocales: ["en"] });
        assert.throws(() => articles.publishedArticles(), /guide:g@ru registry-only/);
      });
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });

  test("divergent artifacts throw naming the cells; half a pair throws too", async () => {
    const divergent = mkdtempSync(join(tmpdir(), "miside-ledger-"));
    const halfPair = mkdtempSync(join(tmpdir(), "miside-ledger-"));
    try {
      await withContentRoot(divergent, async (articles) => {
        writeEmitPair(divergent, { registryLocales: ["en", "ru"], ledgerLocales: ["de"] });
        assert.throws(() => articles.publishedArticles(), /locale-cell divergence/);
        assert.throws(() => articles.publishedArticles(), /guide:g@de ledger-only/);
      });
      await withContentRoot(halfPair, async (articles) => {
        writeEmitPair(halfPair, { registryLocales: ["en"], ledgerLocales: [], withLedger: false });
        assert.throws(() => articles.publishedArticles(), /articles\.jsonl present while article_locales\.jsonl MISSING/);
      });
    } finally {
      rmSync(divergent, { recursive: true, force: true });
      rmSync(halfPair, { recursive: true, force: true });
    }
  });

  test("no artifacts at all stays green at zero (stub policy)", async () => {
    const root = mkdtempSync(join(tmpdir(), "miside-ledger-"));
    try {
      await withContentRoot(root, async (articles) => {
        assert.deepEqual(articles.publishedArticles(), []);
        assert.deepEqual(articles.articleLocaleCells(), []);
      });
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
});

/* ------------------------------------------------------------------ */
/* C15 — pivot-move staleness (base_sha16 semantics)                   */
/* ------------------------------------------------------------------ */

describe("C15 translation staleness", () => {
  function writeStaleFixture(root, enBody, ruBody) {
    const fm = (lang, title, desc) =>
      [
        "---",
        "type: guide",
        "slug: stale-fixture",
        `title: "${title}"`,
        `description: "${desc}"`,
        "status: published",
        "published_at: 2026-08-26",
        'verified_build_id: "19029065"',
        "spoiler: none",
        "entities:",
        "  - locations: level13",
        "embeds: []",
        "---",
        "",
      ].join("\n") + "\n";
    writeFileSync(join(root, "guides", "stale-fixture.mdx"), fm("en", "Stale EN", "EN description.") + enBody, "utf8");
    writeFileSync(join(root, "guides", "stale-fixture.ru.mdx"), fm("ru", "Stale RU", "RU description.") + ruBody, "utf8");
  }

  test("admit → pivot move fires → re-admit quiets; sibling edit never fires", () => {
    const root = freshRoot();
    try {
      writeStaleFixture(root, "First EN body.\n", "Первое тело RU.\n");

      const run1 = run(root);
      assert.equal(run1.result.ok, true);
      let ledger = run1.result.ledgerRows;
      const cellRu1 = ledger.find((c) => c.cell === "guide:stale-fixture@ru");
      assert.ok(cellRu1?.base_sha16, "non-pivot cell carries base_sha16");
      assert.ok(!run1.logs.some((l) => l.startsWith("TRANSLATION-STALE")));

      // negative control FIRST (nothing moved yet): mutating a SIBLING
      // article's own file is not a pivot move and never flags this cell
      writeGuide(root, "sib.en", {});
      const runSib = run(root);
      assert.equal(runSib.result.ok, true);
      assert.ok(!runSib.logs.some((l) => l.includes("guide:stale-fixture@ru")));

      // mutate ONLY the pivot → next emit fires the exact token
      const pivotPath = join(root, "guides", "stale-fixture.mdx");
      writeFileSync(pivotPath, readFileSync(pivotPath, "utf8").replace("First EN body.", "Second EN body."), "utf8");
      const run2 = run(root);
      assert.equal(run2.result.ok, true);
      assert.ok(
        run2.logs.some((l) => l === "TRANSLATION-STALE: guide:stale-fixture@ru <- pivot moved"),
        `expected exact token, got: ${JSON.stringify(run2.logs)}`
      );
      const cellRu2 = run2.result.ledgerRows.find((c) => c.cell === "guide:stale-fixture@ru");
      assert.equal(cellRu2.stale, true);

      // re-admit the translation against the moved pivot → quiet again
      const ruPath = join(root, "guides", "stale-fixture.ru.mdx");
      writeFileSync(ruPath, readFileSync(ruPath, "utf8").replace("Первое тело RU.", "Второе тело RU."), "utf8");
      const run4 = run(root);
      assert.equal(run4.result.ok, true);
      assert.ok(!run4.logs.some((l) => l.startsWith("TRANSLATION-STALE")));
      const cellRu4 = run4.result.ledgerRows.find((c) => c.cell === "guide:stale-fixture@ru");
      assert.equal(cellRu4.stale, false);
      assert.equal(cellRu4.base_sha16, run4.result.ledgerRows.find((c) => c.cell === "guide:stale-fixture@en").body_sha16);
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
});

/* ------------------------------------------------------------------ */
/* C1 — validation law mutations                                       */
/* ------------------------------------------------------------------ */

describe("C1 entity + draft mutations", () => {
  test("bogus id fails loud naming file + id (V1)", () => {
    const root = freshRoot();
    try {
      writeGuide(root, "bogus.en", { front: "" });
      // overwrite entities with an unresolved id
      const p = join(root, "guides", "bogus.en.mdx");
      writeFileSync(p, readFileSync(p, "utf8").replace("- locations: level13", "- locations: no-such-id"), "utf8");
      const { result } = run(root);
      assert.equal(result.ok, false);
      assert.match((result.errors ?? []).join("\n"), /locations:no-such-id .*V1/);
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });

  test("synonym kind rejected outright (V2)", () => {
    const root = freshRoot();
    try {
      writeGuide(root, "syn.en", { front: "" });
      const p = join(root, "guides", "syn.en.mdx");
      // documents IS a corpus family but NOT a routed kind
      writeFileSync(p, readFileSync(p, "utf8").replace("- locations: level13", "- documents: paperpart-level13-0"), "utf8");
      const { result } = run(root);
      assert.equal(result.ok, false);
      assert.match((result.errors ?? []).join("\n"), /"documents" is not a routed kind \(V2\)/);
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });

  test("drafts never reach the registry (V5)", () => {
    const root = freshRoot();
    try {
      writeGuide(root, "published.en", {});
      const draftFm = FM_BASE.replace("{slug}", "drafted") + "\nentities:\n  - locations: level13\nembeds: []\n---\n\nBody.\n";
      writeFileSync(
        join(root, "guides", "drafted.mdx"),
        draftFm.replace("status: published", "status: draft"),
        "utf8"
      );
      const { result, logs } = run(root);
      assert.equal(result.ok, true);
      assert.equal(result.registryRows.length, 1);
      assert.equal(result.registryRows[0].slug, "published");
      assert.ok(logs.some((l) => l.includes("DRAFT-SKIPPED: guides/drafted.mdx")));
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  });
});

/* ------------------------------------------------------------------ */
/* C2 — admission equality (ledger ⇔ registry ⇔ route params)          */
/* ------------------------------------------------------------------ */

describe("C2 admission: registry locales == ledger cells, full diff both directions", () => {
  test("real emitted artifacts agree", async () => {
    const articles = await import("../src/data/articles.ts");
    const cells = articles.articleLocaleCells();
    const registryCells = new Set();
    for (const row of articles.publishedArticles()) {
      for (const code of Object.keys(row.locales)) {
        registryCells.add(`${row.article_id}@${code}`);
        // path format: locale prefix + section + slug
        assert.match(row.locales[code].path, /^\/(?:[a-z]{2}(-[A-Za-z]+)?\/)?(guides|news)\//);
      }
    }
    const ledgerSet = new Set(cells.map((c) => c.cell));
    assert.deepEqual([...ledgerSet].sort(), [...registryCells].sort());

    // sitemap partition URLs carry EXACTLY index + admitted paths per locale
    const { partitionUrls, sitemapPartitionIds } = await import("../src/lib/sitemapPartitions.ts");
    for (const section of ["guides", "news"]) {
      for (const id of sitemapPartitionIds()) {
        if (!id.startsWith(`${section}@`)) continue;
        const locale = id.slice(id.lastIndexOf("@") + 1);
        const urls = partitionUrls(id).slice(1); // drop the index URL
        const admitted = articles.admittedArticlePaths(section, locale);
        assert.deepEqual(urls.sort(), [...admitted].sort());
      }
    }
  });
});

/* ------------------------------------------------------------------ */
/* C5-lite — feeds shape                                               */
/* ------------------------------------------------------------------ */

describe("C5 RSS builder shape", () => {
  test("zero-item stream is a valid empty channel", () => {
    const xml = buildRssChannel({ title: "T", link: "/news", description: "d", items: [] });
    assert.ok(xml.includes("<rss"));
    assert.equal((xml.match(/<item>/g) ?? []).length, 0);
    assert.ok(xml.includes("<channel>"));
  });
  test("item count equals rows and text is escaped", () => {
    const xml = buildRssChannel({
      title: "T & T",
      link: "/news",
      description: "d",
      items: [
        { title: "A & B <x>", link: "http://x/1", guid: "http://x/1", pubDate: "2026-08-26", description: "d" },
        { title: "B", link: "http://x/2", guid: "http://x/2", pubDate: "2026-08-25" },
      ],
    });
    assert.equal((xml.match(/<item>/g) ?? []).length, 2);
    assert.ok(xml.includes("A &amp; B &lt;x&gt;"));
    assert.ok(xml.includes("&amp;"));
  });
});

/* ------------------------------------------------------------------ */
/* validator verdict parity (mjs twin ⇔ ts schema module)              */
/* ------------------------------------------------------------------ */

describe("frontmatter validator parity (scripts twin vs _schema module)", () => {
  const ids = new Set(["level13", "paperpart-level13-0"]);
  // ts schema module expects an array (ids.includes); the mjs twin a Set (.has)
  const routedIdsTs = (kind) => (kind === "locations" ? [...ids] : undefined);
  const routedIdsMjs = (kind) => (kind === "locations" ? ids : undefined);

  const cases = [
    [{ type: "guide", slug: "x", title: "t", description: "d", status: "published", published_at: "2026-08-26", verified_build_id: "19029065", spoiler: "none", entities: [{ kind: "locations", id: "level13" }] }, true],
    [{ type: "guide", slug: "x", title: "t", description: "d", status: "published", published_at: "2026-08-26", verified_build_id: "19029065", spoiler: "none", entities: [{ kind: "locations", id: "nope" }] }, false],
    [{ type: "guide", slug: "x", title: "t", description: "d", status: "published", published_at: "2026-08-26", verified_build_id: "19029065", spoiler: "none", entities: [] }, false],
    [{ type: "guide", slug: "x", title: "t", description: "d".repeat(161), status: "published", published_at: "2026-08-26", verified_build_id: "19029065", spoiler: "none", entities: [{ kind: "locations", id: "level13" }] }, false],
    [{ type: "database", slug: "x", title: "t", description: "d", status: "published", published_at: "2026-08-26", verified_build_id: "19029065", spoiler: "full", entities: [], embeds: [{ id: "e", module: "checklist", props: { items: [{ text: "a" }] } }] }, true],
    [{ type: "database", slug: "x", title: "t", description: "d", status: "published", published_at: "2026-08-26", verified_build_id: "19029065", spoiler: "full", entities: [], embeds: [{ id: "e", module: "map-scene", props: { bogus: 1 } }] }, false],
  ];

  for (const [fmRaw, expectOk] of cases) {
    test(`verdict ${expectOk ? "ok" : "fail"} parity`, () => {
      const tsVerdict = validateFrontmatter(fmRaw, routedIdsTs);
      assert.equal(tsVerdict.ok, expectOk, JSON.stringify(tsVerdict.errors));
      // normalize to the parser twin's cell shape and compare verdict only
      const cell = { relFile: "fixture.mdx", fm: structuredClone(fmRaw), body: "", code: "en" };
      const errors = [];
      validateCellShape(
        cell,
        routedIdsMjs,
        fmRaw.type === "guide" ? "guides" : "news",
        errors
      );
      assert.equal(errors.length === 0, expectOk, errors.join("; "));
    });
  }

  test("slugifyHeading keeps unicode anchors stable", () => {
    assert.equal(slugifyHeading("Как работают профильные фото?"), "как-работают-профильные-фото");
    assert.equal(slugifyHeading("Where do the five paper fragments sit?"), "where-do-the-five-paper-fragments-sit");
  });
});
