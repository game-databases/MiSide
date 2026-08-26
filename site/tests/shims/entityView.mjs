/*
 * TW-MV1 TEST SHIM for src/components/routes/entityView.tsx.
 *
 * Node's type-stripping cannot execute JSX (.tsx), but mapView.ts imports two
 * PURE helpers from it. This shim provides behavior-equivalent stubs so the
 * render-partition tests can run under node --test. It must NEVER be loaded
 * outside tests/ — the aliasLoader redirects only this one module.
 */

/** Re-spacing label law (desluggedLabel): separators become single spaces. */
export function desluggedLabel(id) {
  return String(id ?? "")
    .replace(/[-_]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/** Display name: whatever the owning row carries; callers fall back to the slug. */
export function displayName(_kind, row, _localeCode) {
  const r = row ?? {};
  return r.display_name ?? r.name ?? r.title ?? "";
}
