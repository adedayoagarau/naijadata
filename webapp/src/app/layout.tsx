import type { Metadata } from "next";
import "./globals.css";
import MobileNav from "@/components/MobileNav";

export const metadata: Metadata = {
  title: "Decide9ja - Budget Transparency",
  description: "See where your money goes. AI-powered Nigerian budget analysis.",
  keywords: ["Nigeria", "budget", "transparency", "accountability", "corruption"],
  openGraph: {
    title: "Decide9ja - Budget Transparency",
    description: "See where your money goes",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
        <MobileNav />
        {/* Spacer for mobile nav */}
        <div className="h-16 md:hidden" />
      </body>
    </html>
  );
}
