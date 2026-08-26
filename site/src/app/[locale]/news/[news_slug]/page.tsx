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
  params: Promise<{ locale: string; news_slug: string }>;
}) {
  const { locale, news_slug } = await params;
  return ArticleContent({ section: "news", slug: news_slug, localeCode: locale });
}
export async function generateMetadata(args: {
  params: Promise<{ locale: string; news_slug: string }>;
}): Promise<Metadata> {
  const { locale, news_slug } = await args.params;
  return buildArticleMetadata("news", news_slug, locale);
}
export function generateStaticParams() {
  return articleParamsByLocale("news");
}

