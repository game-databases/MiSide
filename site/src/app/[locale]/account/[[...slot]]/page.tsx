import { AccountSlotContent } from "@/components/routes/sectionPages";
import { PREFIXED_LOCALES } from "@/i18n/locales";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; slot?: string[] }>;
}) {
  const { locale } = await params;
  return AccountSlotContent({ localeCode: locale });
}
export function generateStaticParams() {
  return PREFIXED_LOCALES.map((l) => ({ locale: l.code, slot: [] }));
}

