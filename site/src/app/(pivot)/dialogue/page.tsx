import type { Metadata } from "next";

import {
  DialogueIndexContent,
  buildDialogueIndexMetadata,
} from "@/components/routes/sectionPages";

export default function Page() {
  return <DialogueIndexContent localeCode="en" />;
}
// VC-3 fix #4: the section index is section-named, never the sitewide default.
export async function generateMetadata(): Promise<Metadata> {
  return buildDialogueIndexMetadata("en");
}
