import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Navbar } from "@/components/layout/Navbar";
import { BrandLogo } from "@/components/ui/BrandLogo";

export const viewport: Viewport = {
  themeColor: "#07090e",
  colorScheme: "dark",
};

export const metadata: Metadata = {
  metadataBase: new URL("https://ai-clipper-pro.vercel.app"),
  title: "AI Video Clipper Pro — High-Retention Short-Form Discovery",

  description: "Autonomous discovery, 12-factor ranking, smart 9:16 vertical reframing, and animated subtitle burn-in for TikTok, Reels, and Shorts.",
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
      { url: "/favicon.ico" },
    ],
    shortcut: "/icon.svg",
    apple: "/apple-icon.svg",
  },

  manifest: "/manifest.json",
  openGraph: {
    type: "website",
    title: "AI Video Clipper Pro — High-Retention Short-Form Discovery",
    description: "Turn Long-Form Videos into Viral Shorts with AI Reasoning and FFmpeg Render.",
    images: [{ url: "/brand-logo.jpg", width: 1024, height: 1024, alt: "AI Video Clipper Pro" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "AI Video Clipper Pro",
    description: "High-Retention Short-Form Discovery Engine",
    images: ["/brand-logo.jpg"],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="icon" href="/icon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-icon.svg" />
      </head>
      <body className="min-h-screen bg-[#07090E] text-slate-100 antialiased selection:bg-violet-500 selection:text-white">
        <div className="relative min-h-screen flex flex-col">
          {/* Ambient Glow Orbs */}
          <div className="fixed top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 glow-purple pointer-events-none z-0" />
          <Navbar />
          <main className="relative z-10 flex-1">{children}</main>
          
          {/* Branded Footer */}
          <footer className="relative z-10 border-t border-white/[0.06] bg-[#05070a]/90 backdrop-blur-xl mt-20 py-8">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
              <BrandLogo size="sm" showSubtitle={false} />
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span>Autonomous Short-Form Discovery & Reframing Engine</span>
                <span className="h-1 w-1 rounded-full bg-slate-600" />
                <span className="font-mono text-violet-400">v3.0.0 Production</span>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}

