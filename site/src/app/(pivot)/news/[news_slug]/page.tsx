import {
  ArticleContent,
  buildArticleMetadata,
  articleParamsPivot,
} from "@/components/routes/articlePages";
import type { Metadata } from "next";

export const dynamicParams = false;

export default async function Page({
  params,
}: {
  params: Promise<{ news_slug: string }>;
}) {
  const { news_slug } = await params;
  return ArticleContent({ section: "news", slug: news_slug, localeCode: "en" });
}
export async function generateMetadata(args: {
  params: Promise<{ news_slug: string }>;
}): Promise<Metadata> {
  const { news_slug } = await args.params;
  return buildArticleMetadata("news", news_slug, "en");
}
export function generateStaticParams() {
  return articleParamsPivot("news");
}

