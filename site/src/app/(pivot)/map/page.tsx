import {
  MapSectionContent,
  buildSectionMetadata,
} from "@/components/routes/sectionPages";
import type { Metadata } from "next";

export default function Page() {
  return MapSectionContent({ localeCode: "en" });
}
export async function generateMetadata(): Promise<Metadata> {
  return buildSectionMetadata("en", "map", "nav.map");
}

