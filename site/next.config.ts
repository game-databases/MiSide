import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // DR-2026-08-20-locale-urls: /{pivot}/* URLs do not exist — 301 to bare paths.
  // Defensive second gate lives in src/app/[locale]/layout.tsx (unknown locale 404).
  async redirects() {
    return [
      {
        source: "/en",
        destination: "/",
        // 301 exactly (seo-standard §1 redirect discipline); `permanent`
        // alone would emit a 308.
        statusCode: 301,
      },
      {
        source: "/en/:path*",
        destination: "/:path*",
        statusCode: 301,
      },
    ];
  },
  typedRoutes: true,
};

export default nextConfig;
