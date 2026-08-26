/*
 * Site origin config (spec §10.1): every machine-plane URL the build emits
 * — sitemap <loc> values and the robots.txt Sitemap line — is ABSOLUTE, so
 * the origin lives in ONE place instead of per-route literals.
 * Localhost-first until placement is assigned (owner D3 gate);
 * NEXT_PUBLIC_SITE_ORIGIN overrides at build time.
 */
export const SITE_ORIGIN = (
  process.env.NEXT_PUBLIC_SITE_ORIGIN ?? "http://localhost:3000"
).replace(/\/+$/, "");
