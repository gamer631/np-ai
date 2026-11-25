import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  ...(process.env.NEXT_PUBLIC_SITE_URL
    ? { metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL) }
    : {}),
  title: {
    default: "NIL.ai — Nepal Innovation Labs",
    template: "%s | NIL.ai",
  },
  description:
    "Nepal Innovation Labs researches and engineers useful, reliable AI technology. Born in Nepal. Built for the world.",
  openGraph: {
    title: "NIL.ai — Nepal Innovation Labs",
    description: "Intelligence. Innovation. Engineering.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
