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
  params: Promise<{ guide_slug: string }>;
}) {
  const { guide_slug } = await params;
  return ArticleContent({ section: "guides", slug: guide_slug, localeCode: "en" });
}
export async function generateMetadata(args: {
  params: Promise<{ guide_slug: string }>;
}): Promise<Metadata> {
  const { guide_slug } = await args.params;
  return buildArticleMetadata("guides", guide_slug, "en");
}
export function generateStaticParams() {
  return articleParamsPivot("guides");
}

