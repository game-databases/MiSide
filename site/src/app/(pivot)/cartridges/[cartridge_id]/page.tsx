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
  return EntityDetailContent({ kind: "cartridges", param: "cartridge_id", params, localeCode: "en" });
}
export async function generateMetadata(args: {
  params: Promise<Record<string, string>>;
}): Promise<Metadata> {
  return EntityDetailMetadata({ kind: "cartridges", param: "cartridge_id", ...args, localeCode: "en" });
}
export function generateStaticParams() {
  return entityIdParams("cartridges", "cartridge_id");
}

