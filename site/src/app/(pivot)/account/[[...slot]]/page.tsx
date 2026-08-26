import { AccountSlotContent } from "@/components/routes/sectionPages";

export default function Page() {
  // Reserved tracker/account slot — auth provider is a per-pack build-time call.
  return AccountSlotContent({ localeCode: "en" });
}

