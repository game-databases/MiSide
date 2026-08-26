import type { Metadata } from "next";
import { notFound } from "next/navigation";

import {
  DialogueIndexContent,
  buildDialogueIndexMetadata,
} from "@/components/routes/sectionPages";
import { PREFIXED_LOCALES, getLocale } from "@/i18n/locales";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const def = getLocale(locale);
  if (!def) notFound();
  return <DialogueIndexContent localeCode={def.code} />;
}
export function generateStaticParams() {
  return PREFIXED_LOCALES.map((l) => ({ locale: l.code }));
}
// VC-3 fix #4: section-named title in the serving locale (never EN passthrough).
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const def = getLocale(locale);
  if (!def) notFound();
  return buildDialogueIndexMetadata(def.code);
}
