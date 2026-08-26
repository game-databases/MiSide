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
  return EntityDetailContent({ kind: "achievements", param: "achievement_id", params, localeCode: "en" });
}
export async function generateMetadata(args: {
  params: Promise<Record<string, string>>;
}): Promise<Metadata> {
  return EntityDetailMetadata({ kind: "achievements", param: "achievement_id", ...args, localeCode: "en" });
}
export function generateStaticParams() {
  return entityIdParams("achievements", "achievement_id");
}

