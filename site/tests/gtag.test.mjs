/*
 * GA4 gtag gate: every module that emits <html> must load
 * googletagmanager.com/gtag/js?id=G-YTGCLB29ZV via next/script
 * afterInteractive and call gtag('config', 'G-YTGCLB29ZV').
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const SNIPPET = join(SRC, "components/routes/GtagSnippet.tsx");

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* walk(p);
    else if (/\.(tsx|jsx|html)$/.test(name)) yield p;
  }
}

test("GtagSnippet loads G-YTGCLB29ZV via next/script afterInteractive", () => {
  const src = readFileSync(SNIPPET, "utf8");
  assert.match(src, /from ["']next\/script["']/);
  assert.match(src, /googletagmanager\.com\/gtag\/js\?id=G-YTGCLB29ZV/);
  assert.match(src, /gtag\('config', 'G-YTGCLB29ZV'\)/);
  assert.match(src, /strategy=["']afterInteractive["']/);
});

test("every <html>-emitting module mounts GtagSnippet", () => {
  const htmlFiles = [];
  for (const file of walk(SRC)) {
    const text = readFileSync(file, "utf8");
    if (/<html\s/.test(text)) htmlFiles.push({ file, text });
  }
  assert.ok(
    htmlFiles.length >= 2,
    "expected at least HtmlShell and global-not-found"
  );
  for (const { file, text } of htmlFiles) {
    assert.ok(
      text.includes("GtagSnippet"),
      `${file} emits <html> but does not mount GtagSnippet`
    );
  }
});

test("both root layouts render through HtmlShell (shared gtag mount)", () => {
  for (const rel of ["app/(pivot)/layout.tsx", "app/[locale]/layout.tsx"]) {
    const text = readFileSync(join(SRC, rel), "utf8");
    assert.match(text, /from ["']@\/components\/routes\/HtmlShell["']/);
    assert.match(text, /<HtmlShell\b/);
  }
});
