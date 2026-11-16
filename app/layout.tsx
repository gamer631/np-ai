import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NP.ai — Think beyond",
  description: "One thoughtful AI workspace. Multiple models. Your choice."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
