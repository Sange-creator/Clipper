import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/layout/Navbar";

export const metadata: Metadata = {
  title: "AI Video Clipper — High-Retention Short-Form Discovery",
  description: "Discover, score, and render high-retention 9:16 vertical clips for TikTok, Instagram Reels, and YouTube Shorts using AI.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#090A0F] text-slate-100 antialiased selection:bg-violet-500 selection:text-white">
        <div className="relative min-h-screen flex flex-col">
          {/* Ambient Glow Orbs */}
          <div className="fixed top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 glow-purple pointer-events-none z-0" />
          <Navbar />
          <main className="relative z-10 flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}
