import {
  EntityDetailContent,
  EntityDetailMetadata,
  entityIdParamsByLocale,
} from "@/components/routes/entityPages";
import { PREFIXED_LOCALES } from "@/i18n/locales";
import type { Metadata } from "next";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string } & Record<string, string>>;
}) {
  const { locale, ...rest } = await params;
  return EntityDetailContent({ kind: "endings", param: "ending_id", params: Promise.resolve(rest), localeCode: locale });
}
export async function generateMetadata(args: {
  params: Promise<{ locale: string } & Record<string, string>>;
}): Promise<Metadata> {
  const { locale, ...rest } = await args.params;
  return EntityDetailMetadata({ kind: "endings", param: "ending_id", params: Promise.resolve(rest), localeCode: locale });
}
export function generateStaticParams() {
  return entityIdParamsByLocale("endings", "ending_id", PREFIXED_LOCALES.map((l) => l.code));
}

