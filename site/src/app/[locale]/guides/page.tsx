import {
  ArticleIndexContent,
  buildArticleIndexMetadata,
} from "@/components/routes/articlePages";
import { PREFIXED_LOCALES } from "@/i18n/locales";
import type { Metadata } from "next";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  return ArticleIndexContent({ section: "guides", localeCode: locale });
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return buildArticleIndexMetadata("guides", locale);
}
export function generateStaticParams() {
  return PREFIXED_LOCALES.map((l) => ({ locale: l.code }));
}

