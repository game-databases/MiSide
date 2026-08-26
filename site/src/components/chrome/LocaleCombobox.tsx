"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { LOCALES } from "@/i18n/locales";
import { asRoute } from "@/lib/utils";

/*
 * Locale combobox (design-standard §5.3): native names in the list, accepts
 * typed text (Radix typeahead stock), closed chip shows the CURRENT CODE.
 * Switching navigates to the same page in the chosen locale when available;
 * otherwise to that locale's home — localization-architecture §4.
 */
export function LocaleCombobox({
  chrome,
  localeCode,
  currentPath,
  availableLocales,
}: {
  chrome: Record<string, string>;
  localeCode: string;
  currentPath: string;
  availableLocales: readonly string[];
}) {
  const router = useRouter();

  function switchTo(code: string) {
    const def = LOCALES.find((l) => l.code === code)!;
    const available = availableLocales.includes(code);
    // Same page when the ledger admits it there; else the locale's home.
    const target = available ? `${def.prefix}${currentPath}` || "/" : `${def.prefix}/` || "/";
    router.push(asRoute(target));
  }

  // Radix does NOT inherit the page's dir attribute — pass the current
  // locale's direction or trigger/content stay LTR inside RTL pages.
  const def = LOCALES.find((l) => l.code === localeCode);
  return (
    <Select value={localeCode} onValueChange={switchTo} dir={def?.dir}>
      <SelectTrigger
        size="sm"
        aria-label={chrome["a11y.localeSwitcher"]}
        className="w-auto min-w-16 gap-1 font-lcd"
      >
        {/* closed chip shows the current code */}
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {LOCALES.filter((l) => availableLocales.includes(l.code)).map((l) => (
          <SelectItem key={l.code} value={l.code} className="font-sans">
            {NATIVE_NAMES[l.code] ?? l.code}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

/** Native names for the list (chrome is authored per locale; names are data). */
const NATIVE_NAMES: Record<string, string> = {
  en: "English",
  ru: "Русский",
  uk: "Українська",
  be: "Беларуская",
  bg: "Български",
  "zh-Hans": "简体中文",
  "zh-Hant": "繁體中文",
  hr: "Hrvatski",
  cs: "Čeština",
  fil: "Filipino",
  fr: "Français",
  de: "Deutsch",
  hu: "Magyar",
  id: "Bahasa Indonesia",
  it: "Italiano",
  ja: "日本語",
  kk: "Қазақша",
  ko: "한국어",
  fa: "فارسی",
  pl: "Polski",
  "pt-PT": "Português (Portugal)",
  "pt-BR": "Português (Brasil)",
  ro: "Română",
  "sr-Latn": "Srpski (latinica)",
  sk: "Slovenčina",
  "es-419": "Español (Latinoamérica)",
  "es-ES": "Español (España)",
  sv: "Svenska",
  th: "ไทย",
  tr: "Türkçe",
  vi: "Tiếng Việt",
  ar: "العربية",
  "ar-EG": "العربية (مصر)",
  "ru-x-prerev": "Русский (дореф.)",
};
