import {
  StubSectionContent,
  buildSectionMetadata,
} from "@/components/routes/sectionPages";
import type { Metadata } from "next";

export default function Page() {
  return StubSectionContent({ segment: "feedback", localeCode: "en" });
}
export async function generateMetadata(): Promise<Metadata> {
  return buildSectionMetadata("en", "feedback", "nav.feedback");
}

