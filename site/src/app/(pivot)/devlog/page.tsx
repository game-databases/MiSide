import {
  StubSectionContent,
  buildSectionMetadata,
} from "@/components/routes/sectionPages";
import type { Metadata } from "next";

export default function Page() {
  return StubSectionContent({ segment: "devlog", localeCode: "en" });
}
export async function generateMetadata(): Promise<Metadata> {
  return buildSectionMetadata("en", "devlog", "nav.devlog");
}

