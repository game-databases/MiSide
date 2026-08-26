import { EntityIndexContent } from "@/components/routes/entityPages";
import { buildSectionMetadata } from "@/components/routes/sectionPages";
import type { Metadata } from "next";

export default function Page() {
  return <EntityIndexContent kind="achievements" localeCode="en" />;
}
export async function generateMetadata(): Promise<Metadata> {
  return buildSectionMetadata("en", "achievements", "nav.achievements");
}

