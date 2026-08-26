import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { DialogueGraphRoute, dialogueContainers, dialogueTitle } from "@/components/routes/DialogueGraphRoute";
import { getChrome } from "@/i18n/request";
import { getLocale, PREFIXED_LOCALES } from "@/i18n/locales";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; container: string }>;
}) {
  const { locale, container } = await params;
  const def = getLocale(locale);
  if (!def) notFound();
  const chrome = getChrome(def) as unknown as Record<string, string>;
  return (
    <DialogueGraphRoute
      container={container}
      localePrefix={def.prefix}
      homeLabel={chrome["breadcrumb.home"]}
      chrome={chrome}
      localeCode={def.code}
    />
  );
}
export function generateStaticParams() {
  const out: Array<{ locale: string; container: string }> = [];
  for (const l of PREFIXED_LOCALES)
    for (const container of dialogueContainers()) out.push({ locale: l.code, container });
  return out;
}

// VC-2 fix #5: entity-named title in the serving locale (never EN passthrough).
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; container: string }>;
}): Promise<Metadata> {
  const { locale, container } = await params;
  const def = getLocale(locale);
  if (!def) notFound();
  return { title: dialogueTitle(container, def.code) };
}
