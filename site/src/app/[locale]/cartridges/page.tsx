import { EntityIndexContent } from "@/components/routes/entityPages";
import { buildSectionMetadata } from "@/components/routes/sectionPages";
import { PREFIXED_LOCALES } from "@/i18n/locales";
import type { Metadata } from "next";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  return EntityIndexContent({ kind: "cartridges", localeCode: locale });
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return buildSectionMetadata(locale, "cartridges", "nav.cartridges");
}
export function generateStaticParams() {
  return PREFIXED_LOCALES.map((l) => ({ locale: l.code }));
}

