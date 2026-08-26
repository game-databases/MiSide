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
}): Promise<ReturnType<typeof EntityDetailContent>> {
  return EntityDetailContent({ kind: "books", param: "book_id", params, localeCode: "en" });
}
export async function generateMetadata(args: {
  params: Promise<Record<string, string>>;
}): Promise<Metadata> {
  return EntityDetailMetadata({ kind: "books", param: "book_id", ...args, localeCode: "en" });
}
export function generateStaticParams() {
  return entityIdParams("books", "book_id");
}

