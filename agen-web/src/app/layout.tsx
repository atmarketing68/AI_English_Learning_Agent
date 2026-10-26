import type { Metadata, Viewport } from "next";
import "./globals.css";
import AppShell from "@/components/ui/AppShell";
import SkinProvider from "@/components/ui/SkinProvider";

/** Apply the cached look before React hydrates, so there is no flash between skins. */
const SKIN_BOOT = `try{var s=localStorage.getItem("agen-skin");if(s==="vivid"||s==="classic"){document.documentElement.dataset.skin=s}}catch(e){}`;

export const metadata: Metadata = {
  title: "AI AGENT ENGLISH — Học tiếng Anh cùng AI Coach cá nhân",
  description: "AI Personal English Learning Agent — người thầy, người bạn và huấn luyện viên tiếng Anh đồng hành lâu dài.",
  applicationName: "AI AGENT ENGLISH",
  appleWebApp: { capable: true, title: "AI English", statusBarStyle: "default" },
  formatDetection: { telephone: false },
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
