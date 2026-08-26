import {
  ArticleIndexContent,
  buildArticleIndexMetadata,
} from "@/components/routes/articlePages";
import type { Metadata } from "next";

export default function Page() {
  return ArticleIndexContent({ section: "news", localeCode: "en" });
}
export async function generateMetadata(): Promise<Metadata> {
  return buildArticleIndexMetadata("news", "en");
}

