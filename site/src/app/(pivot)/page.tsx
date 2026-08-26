import {
  HomePageContent,
  buildHomeMetadata,
} from "@/components/routes/sectionPages";
import type { Metadata } from "next";

export default function Page() {
  return HomePageContent({ localeCode: "en" });
}
export async function generateMetadata(): Promise<Metadata> {
  return buildHomeMetadata("en");
}

