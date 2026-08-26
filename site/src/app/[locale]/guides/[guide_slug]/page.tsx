import {
  ArticleContent,
  buildArticleMetadata,
  articleParamsByLocale,
} from "@/components/routes/articlePages";
import type { Metadata } from "next";

export const dynamicParams = false;

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; guide_slug: string }>;
}) {
  const { locale, guide_slug } = await params;
  return ArticleContent({ section: "guides", slug: guide_slug, localeCode: locale });
}
export async function generateMetadata(args: {
  params: Promise<{ locale: string; guide_slug: string }>;
}): Promise<Metadata> {
  const { locale, guide_slug } = await args.params;
  return buildArticleMetadata("guides", guide_slug, locale);
}
export function generateStaticParams() {
  return articleParamsByLocale("guides");
}

