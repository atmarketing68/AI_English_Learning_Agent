import type { Metadata } from "next";
import "./globals.css";
import MobileNav from "@/components/ui/MobileNav";

export const metadata: Metadata = {
  title: "AI AGENT ENGLISH — Học tiếng Anh cùng AI Coach cá nhân",
  description: "AI Personal English Learning Agent — người thầy, người bạn và huấn luyện viên tiếng Anh đồng hành lâu dài.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        {children}
        <MobileNav />
      </body>
    </html>
  );
}
