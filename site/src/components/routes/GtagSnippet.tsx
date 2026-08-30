import Script from "next/script";

/*
 * GA4 gtag for miside.wiki. One measurement ID; afterInteractive so the
 * tag is not render-blocking. Mounted from every <html>-owning surface
 * (HtmlShell for the two root layouts; global-not-found for the uncaught 404).
 */
export function GtagSnippet() {
  return (
    <>
      <Script
        src="https://www.googletagmanager.com/gtag/js?id=G-YTGCLB29ZV"
        strategy="afterInteractive"
      />
      <Script id="ga4-gtag" strategy="afterInteractive">
        {`
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-YTGCLB29ZV');
`}
      </Script>
    </>
  );
}
