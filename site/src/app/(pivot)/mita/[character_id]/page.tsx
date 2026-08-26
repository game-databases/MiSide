import {
  EntityDetailContent,
  EntityDetailMetadata,
  entityIdParams,
} from "@/components/routes/entityPages";
import type { Metadata } from "next";

export default async function Page({
  params,
}: {
  params: Promise<Record<string, string>>;
}) {
  return EntityDetailContent({ kind: "mita", param: "character_id", params, localeCode: "en" });
}
export async function generateMetadata(args: {
  params: Promise<Record<string, string>>;
}): Promise<Metadata> {
  return EntityDetailMetadata({ kind: "mita", param: "character_id", ...args, localeCode: "en" });
}
export function generateStaticParams() {
  return entityIdParams("mita", "character_id");
}

