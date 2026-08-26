import { NotFoundView } from "@/components/routes/NotFoundView";

/*
 * Group-local 404: renders inside this group's root layout, so the served
 * document keeps the serving tree's chrome and document element. Unknown
 * locale codes never reach here (dynamicParams=false + layout notFound) —
 * they land on the global 404, the honest document for a URL that was never
 * ours.
 */
export default function NotFound() {
  return <NotFoundView homeHref="/" />;
}
