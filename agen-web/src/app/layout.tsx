import type { Metadata, Viewport } from "next";
import "./globals.css";
import AppShell from "@/components/ui/AppShell";
import SkinProvider from "@/components/ui/SkinProvider";
import { OG_IMAGE, SITE_DESCRIPTION, SITE_NAME, SITE_TAGLINE, SITE_URL } from "@/lib/seo/site";

/** Apply the cached look before React hydrates, so there is no flash between skins. */
const SKIN_BOOT = `try{var s=localStorage.getItem("agen-skin");if(s==="vivid"||s==="classic"){document.documentElement.dataset.skin=s}}catch(e){}`;

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: `${SITE_NAME} — ${SITE_TAGLINE}`, template: `%s · ${SITE_NAME}` },
  description: SITE_DESCRIPTION,
  applicationName: SITE_NAME,
  appleWebApp: { capable: true, title: "AI English", statusBarStyle: "default" },
  formatDetection: { telephone: false },
  openGraph: { type: "website", siteName: SITE_NAME, locale: "vi_VN", images: [OG_IMAGE] },
  twitter: { card: "summary_large_image", images: [OG_IMAGE.url] },
  // Google Search Console: đặt NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION (mã trong thẻ meta xác minh) trên Vercel.
  verification: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION ? { google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION } : undefined,
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#F5F5F7" },
    { media: "(prefers-color-scheme: dark)", color: "#000000" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: SKIN_BOOT }} />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <SkinProvider />
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
