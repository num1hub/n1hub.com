import { Geist, Geist_Mono } from "next/font/google";
import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";
import { Providers } from "./providers";
import { Navigation } from "@/components/navigation";

const geist = Geist({ subsets: ["latin"] });
const geistMono = Geist_Mono({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "N1Hub v0.2",
  description: "Anything → Capsules → Graph → Chat, now powered by the consolidated UI + DeepMine engine."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geist.className} antialiased`}>
      <body className={`${geistMono.className} min-h-screen bg-slate-950 text-slate-100`}>
        <Providers>
          <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-6">
            <Navigation />
            {children}
          </div>
        </Providers>
        <Analytics />
      </body>
    </html>
  );
}
