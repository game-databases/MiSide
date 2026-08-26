import posthog from "posthog-js";

import { initPublicPosthog } from "./lib/posthogPublic";

/*
 * Next.js client instrumentation (15.3+ / 16): runs once on every public
 * page's browser bundle, including both root layouts and the global 404.
 * Init is a no-op when NEXT_PUBLIC_POSTHOG_KEY is unset.
 */
initPublicPosthog(posthog);
