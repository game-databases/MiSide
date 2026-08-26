import { notFound } from "next/navigation";

import { getChrome } from "@/i18n/request";
import { getLocale } from "@/i18n/locales";
import { ENTITY_KINDS, kindIds } from "@/data/contracts";
import {
  buildDetailData,
  buildEntityMetadata,
  buildIndexData,
} from "./entityView";
import { EntityIndexRoute } from "./EntityIndexRoute";
import { EntityDetailRoute } from "./EntityDetailRoute";

/*
 * Page-content factories shared by BOTH trees — the (pivot)/[locale] wrapper
 * files stay thin (<15 lines) and carry zero route logic.
 */

/** Chrome key per routed kind's index title. */
const KIND_TITLE_KEY: Record<string, string> = {
  mita: "nav.mita",
  players: "nav.players",
  cartridges: "nav.cartridges",
  minigames: "nav.minigames",
  achievements: "nav.achievements",
  endings: "nav.endings",
  books: "nav.books",
  locations: "nav.locations",
};

export async function EntityIndexContent({
  kind,
  localeCode,
}: {
  kind: string;
  localeCode: string;
}) {
  if (!ENTITY_KINDS[kind]) notFound();
  const def = getLocale(localeCode);
  if (!def) notFound();
  const chrome = getChrome(def);
  const data = buildIndexData(kind, def.code, chrome[KIND_TITLE_KEY[kind] ?? ""]);
  return (
    <EntityIndexRoute
      data={data}
      localePrefix={def.prefix}
      homeLabel={chrome["breadcrumb.home"]}
    />
  );
}

/** Static params for an index page: none (single route per tree). */
export function entityIdParams(kind: string, param: string) {
  return kindIds(kind).map((id) => ({ [param]: id }));
}

export async function EntityDetailContent({
  kind,
  param,
  params,
  localeCode,
}: {
  kind: string;
  param: string;
  params: Promise<Record<string, string>>;
  localeCode: string;
}) {
  const def = getLocale(localeCode);
  if (!def) notFound();
  const { [param]: id } = await params;
  const data = buildDetailData(kind, id, def.code);
  const chrome = getChrome(def);
  return (
    <EntityDetailRoute
      data={data}
      localeCode={def.code}
      localePrefix={def.prefix}
      chrome={chrome as unknown as Record<string, string>}
    />
  );
}

export async function EntityDetailMetadata({
  kind,
  param,
  params,
  localeCode,
}: {
  kind: string;
  param: string;
  params: Promise<Record<string, string>>;
  localeCode: string;
}) {
  const { [param]: id } = await params;
  return buildEntityMetadata(kind, id, localeCode);
}

/** Detail static params for the [locale] tree: locales × contract ids. */
export function entityIdParamsByLocale(
  kind: string,
  param: string,
  localeCodes: readonly string[]
) {
  const out: Array<Record<string, string>> = [];
  for (const locale of localeCodes) {
    for (const id of kindIds(kind)) out.push({ locale, [param]: id });
  }
  return out;
}
