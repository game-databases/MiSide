/*
 * Public PostHog init: fail closed without a write key, stamp hostname on
 * $pageview, and talk to US Cloud directly (no first-party ingest proxy).
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const SITE_DIR = dirname(fileURLToPath(import.meta.url));

function makeClient() {
  /** @type {{ init: { key: string, config: Record<string, unknown> }[], register: Record<string, unknown>[] }} */
  const calls = { init: [], register: [] };
  const client = {
    /**
     * @param {string} key
     * @param {Record<string, unknown>} config
     */
    init(key, config) {
      calls.init.push({ key, config });
      if (typeof config.loaded === "function") {
        config.loaded(client);
      }
    },
    /**
     * @param {Record<string, unknown>} properties
     */
    register(properties) {
      calls.register.push(properties);
    },
  };
  return { client, calls };
}

test("missing write key is a no-op init (fail closed)", async () => {
  const { initPublicPosthog } = await import("../src/lib/posthogPublic.ts");
  const { client, calls } = makeClient();
  assert.equal(initPublicPosthog(client, { env: {} }), false);
  assert.equal(
    initPublicPosthog(client, { env: { NEXT_PUBLIC_POSTHOG_KEY: "" } }),
    false
  );
  assert.equal(
    initPublicPosthog(client, { env: { NEXT_PUBLIC_POSTHOG_KEY: "   " } }),
    false
  );
  assert.equal(calls.init.length, 0);
  assert.equal(calls.register.length, 0);
});

test("init sends $pageview config to US Cloud with hostname on the event", async () => {
  const {
    initPublicPosthog,
    POSTHOG_API_HOST,
    POSTHOG_UI_HOST,
  } = await import("../src/lib/posthogPublic.ts");
  const { client, calls } = makeClient();
  const ok = initPublicPosthog(client, {
    env: { NEXT_PUBLIC_POSTHOG_KEY: "test-write-key" },
    hostname: "ms2db.com",
  });
  assert.equal(ok, true);
  assert.equal(calls.init.length, 1);
  assert.equal(calls.init[0].key, "test-write-key");
  assert.equal(calls.init[0].config.api_host, "https://us.i.posthog.com");
  assert.equal(calls.init[0].config.ui_host, "https://us.posthog.com");
  assert.equal(calls.init[0].config.api_host, POSTHOG_API_HOST);
  assert.equal(calls.init[0].config.ui_host, POSTHOG_UI_HOST);
  assert.equal(calls.init[0].config.capture_pageview, "history_change");
  assert.deepEqual(calls.register[0], { hostname: "ms2db.com" });
  const pageview = calls.init[0].config.before_send({
    event: "$pageview",
    properties: { $current_url: "https://ms2db.com/mita" },
  });
  assert.equal(pageview.properties.hostname, "ms2db.com");
  assert.equal(pageview.properties.$current_url, "https://ms2db.com/mita");
  assert.equal(pageview.event, "$pageview");
});

test(".env.example names project 536998 and keeps the write key empty", () => {
  const example = readFileSync(join(SITE_DIR, "..", ".env.example"), "utf8");
  assert.match(example, /536998/);
  assert.match(example, /NEXT_PUBLIC_POSTHOG_KEY=\s*$/m);
  assert.doesNotMatch(example, /phc_[A-Za-z0-9]/);
  assert.match(example, /557596/);
});

test("committed site source does not contain a phc_ write key or ingest proxy", () => {
  const instrumentation = readFileSync(
    join(SITE_DIR, "..", "src", "instrumentation-client.ts"),
    "utf8"
  );
  assert.match(instrumentation, /initPublicPosthog/);
  assert.match(instrumentation, /posthog-js/);

  const nextConfig = readFileSync(join(SITE_DIR, "..", "next.config.ts"), "utf8");
  assert.doesNotMatch(nextConfig, /us\.i\.posthog\.com/);
  assert.doesNotMatch(nextConfig, /\/ingest/);

  const helper = readFileSync(
    join(SITE_DIR, "..", "src", "lib", "posthogPublic.ts"),
    "utf8"
  );
  assert.match(helper, /https:\/\/us\.i\.posthog\.com/);
  assert.match(helper, /https:\/\/us\.posthog\.com/);
  assert.doesNotMatch(helper, /phc_/);

  const skip = new Set(["node_modules", ".next", "public"]);
  /** @param {string} dir */
  function* walk(dir) {
    for (const entry of readdirSync(dir)) {
      if (skip.has(entry)) continue;
      const p = join(dir, entry);
      if (statSync(p).isDirectory()) yield* walk(p);
      else if (/\.(ts|tsx|js|mjs|md|example|json)$/.test(entry)) yield p;
    }
  }
  for (const file of walk(join(SITE_DIR, ".."))) {
    const text = readFileSync(file, "utf8");
    assert.doesNotMatch(
      text,
      /phc_[A-Za-z0-9]+/,
      `write key leaked in ${file}`
    );
  }
});
