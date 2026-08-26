import type { Metadata } from "next";

import { DialogueGraphRoute, dialogueContainers, dialogueTitle } from "@/components/routes/DialogueGraphRoute";
import { getChrome } from "@/i18n/request";

export default async function Page({
  params,
}: {
  params: Promise<{ container: string }>;
}) {
  const { container } = await params;
  const chrome = getChrome("en") as unknown as Record<string, string>;
  return (
    <DialogueGraphRoute
      container={container}
      localePrefix=""
      homeLabel={chrome["breadcrumb.home"]}
      chrome={chrome}
      localeCode="en"
    />
  );
}
export function generateStaticParams() {
  return dialogueContainers().map((container) => ({ container }));
}

// VC-2 fix #5: the transcript names its own carrier — never the sitewide
// default title.
export async function generateMetadata({
  params,
}: {
  params: Promise<{ container: string }>;
}): Promise<Metadata> {
  const { container } = await params;
  return { title: dialogueTitle(container, "en") };
}
