import type { CaptureResult, PostHog } from "posthog-js";

/**
 * Public-page PostHog product analytics for Game Databases project 536998.
 *
 * Collector hosts are the US Cloud ingest and UI origins — this site has no
 * first-party /ingest proxy. The write key is read from
 * NEXT_PUBLIC_POSTHOG_KEY at runtime; a missing key is a no-op so the site
 * still renders. Every captured event, including autocaptured $pageview,
 * carries the page hostname so hosts sharing this project stay separable.
 */

export const POSTHOG_API_HOST = "https://us.i.posthog.com";
export const POSTHOG_UI_HOST = "https://us.posthog.com";
export const POSTHOG_WRITE_KEY_ENV = "NEXT_PUBLIC_POSTHOG_KEY";

/**
 * posthog-js surface used by the public init helper. Tests pass a mock with
 * the same two methods.
 */
export type PublicPosthogClient = Pick<PostHog, "init" | "register">;

export type InitPublicPosthogOptions = {
  env?: Record<string, string | undefined>;
  hostname?: string;
};

/**
 * Reads the public write key. Empty, whitespace-only, and unset values all
 * count as missing so init can fail closed.
 */
export function readPosthogWriteKey(
  env: Record<string, string | undefined> = process.env
): string | null {
  const raw = env[POSTHOG_WRITE_KEY_ENV];
  if (typeof raw !== "string") {
    return null;
  }
  const key = raw.trim();
  return key.length > 0 ? key : null;
}

/**
 * Resolves the hostname that must ride on every public event.
 */
export function resolvePageHostname(explicit?: string): string {
  if (typeof explicit === "string" && explicit.trim().length > 0) {
    return explicit.trim();
  }
  if (typeof window !== "undefined" && window.location?.hostname) {
    return window.location.hostname;
  }
  return "";
}

/**
 * Attaches the page hostname onto an event's properties object.
 */
export function withPageHostname(
  properties: Record<string, unknown>,
  hostname: string
): Record<string, unknown> {
  if (hostname) {
    properties.hostname = hostname;
  }
  return properties;
}

/**
 * Stamps hostname onto a capture payload so $pageview (and other events)
 * always carry the page host.
 */
export function stampHostnameOnCapture(
  event: CaptureResult | null,
  hostname: string
): CaptureResult | null {
  if (!event || !hostname) {
    return event;
  }
  event.properties = withPageHostname(event.properties ?? {}, hostname);
  return event;
}

/**
 * Initializes posthog-js for public pages. Returns false and skips init when
 * the write key is missing (fail closed).
 */
export function initPublicPosthog(
  client: PublicPosthogClient,
  options: InitPublicPosthogOptions = {}
): boolean {
  const env = options.env ?? process.env;
  const key = readPosthogWriteKey(env);
  if (!key) {
    console.log(
      "PostHog public analytics: NEXT_PUBLIC_POSTHOG_KEY missing; init is a no-op (fail closed)."
    );
    return false;
  }

  const hostname = resolvePageHostname(options.hostname);
  console.log("PostHog public analytics: initializing", {
    hostname,
    api_host: POSTHOG_API_HOST,
    ui_host: POSTHOG_UI_HOST,
    project: 536998,
  });

  if (hostname) {
    client.register({ hostname });
  }

  client.init(key, {
    api_host: POSTHOG_API_HOST,
    ui_host: POSTHOG_UI_HOST,
    defaults: "2026-05-30",
    capture_pageview: "history_change",
    before_send: (event) => stampHostnameOnCapture(event, resolvePageHostname(options.hostname) || hostname),
    loaded: (loadedClient) => {
      if (hostname) {
        loadedClient.register({ hostname });
      }
      console.log("PostHog public analytics: loaded", { hostname });
    },
  });

  return true;
}
