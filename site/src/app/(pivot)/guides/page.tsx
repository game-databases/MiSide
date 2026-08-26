import {
  ArticleIndexContent,
  buildArticleIndexMetadata,
} from "@/components/routes/articlePages";
import type { Metadata } from "next";

export default function Page() {
  return ArticleIndexContent({ section: "guides", localeCode: "en" });
}
export async function generateMetadata(): Promise<Metadata> {
  return buildArticleIndexMetadata("guides", "en");
}

