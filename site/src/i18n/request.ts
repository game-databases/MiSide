/*
 * getChrome(locale) — the ONLY chrome-text entry point.
 * Chrome is a namespace separate from game text (localization-architecture §4):
 * these strings never claim client provenance, and game categories are never
 * imported here. Exactly two declared aliases resolve to their target file;
 * any other locale falls through getLocale() validation upstream.
 */
import { getLocale, type LocaleDef } from "./locales";

import ar from "./chrome/ar.json";
import be from "./chrome/be.json";
import bg from "./chrome/bg.json";
import cs from "./chrome/cs.json";
import de from "./chrome/de.json";
import en from "./chrome/en.json";
import es419 from "./chrome/es-419.json";
import esES from "./chrome/es-ES.json";
import fa from "./chrome/fa.json";
import fil from "./chrome/fil.json";
import fr from "./chrome/fr.json";
import hr from "./chrome/hr.json";
import hu from "./chrome/hu.json";
import id from "./chrome/id.json";
import it from "./chrome/it.json";
import ja from "./chrome/ja.json";
import kk from "./chrome/kk.json";
import ko from "./chrome/ko.json";
import pl from "./chrome/pl.json";
import ptBR from "./chrome/pt-BR.json";
import ptPT from "./chrome/pt-PT.json";
import ro from "./chrome/ro.json";
import ru from "./chrome/ru.json";
import sk from "./chrome/sk.json";
import srLatn from "./chrome/sr-Latn.json";
import sv from "./chrome/sv.json";
import th from "./chrome/th.json";
import tr from "./chrome/tr.json";
import uk from "./chrome/uk.json";
import vi from "./chrome/vi.json";
import zhHans from "./chrome/zh-Hans.json";
import zhHant from "./chrome/zh-Hant.json";

const FILES: Record<string, Record<string, string>> = {
  ar,
  be,
  bg,
  cs,
  de,
  en,
  "es-419": es419,
  "es-ES": esES,
  fa,
  fil,
  fr,
  hr,
  hu,
  id,
  it,
  ja,
  kk,
  ko,
  pl,
  "pt-BR": ptBR,
  "pt-PT": ptPT,
  ro,
  ru,
  sk,
  "sr-Latn": srLatn,
  sv,
  th,
  tr,
  uk,
  vi,
  "zh-Hans": zhHans,
  "zh-Hant": zhHant,
};

export type Chrome = Readonly<Record<string, string>>;

/**
 * Resolve the chrome dictionary for a site locale. Alias locales
 * (ru-x-prerev, ar-EG) return their target file verbatim — the only two
 * aliases the spec permits.
 */
export function getChrome(localeOrDef: string | LocaleDef): Chrome {
  const def =
    typeof localeOrDef === "string" ? getLocale(localeOrDef) : localeOrDef;
  if (!def) throw new Error(`Unknown locale: ${String(localeOrDef)}`);
  const file = def.chromeAlias ?? def.code;
  const dict = FILES[file];
  if (!dict) throw new Error(`No chrome file for ${file}`);
  return dict;
}

/** Flat key lookup with an explicit fallback-to-pivot (never silent EN passthrough on non-EN pages: pivot use only). */
export function t(chrome: Chrome, key: string): string {
  const v = chrome[key];
  if (typeof v !== "string") throw new Error(`Missing chrome key: ${key}`);
  return v;
}
