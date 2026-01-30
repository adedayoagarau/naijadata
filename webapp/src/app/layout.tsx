import type { Metadata } from "next";
import { Space_Mono, VT323 } from "next/font/google";
import "./globals.css";

const spaceMono = Space_Mono({
  weight: ["400", "700"],
  subsets: ["latin"],
  variable: "--font-space-mono",
});

const vt323 = VT323({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-vt323",
});

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
      <body className={`${spaceMono.variable} ${vt323.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
