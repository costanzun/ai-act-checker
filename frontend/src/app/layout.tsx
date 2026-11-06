import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { LanguageProvider } from "@/i18n";
import { CitationProvider } from "@/components/cite/CitationContext";
import { AppHeader } from "@/components/layout/AppHeader";
import { AppFooter } from "@/components/layout/AppFooter";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"], display: "swap" });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  title: "EU AI Act Checker",
  description: "Describe your AI system, get its EU AI Act risk tier, your obligations and the documents to prepare, each with the article behind it.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" data-scroll-behavior="smooth" suppressHydrationWarning className={`${geistSans.variable} ${geistMono.variable}`}>
      <body className="app-bg flex min-h-dvh flex-col">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <LanguageProvider>
            <TooltipProvider delay={250}>
              <CitationProvider>
                <AppHeader />
                <main id="main" className="mx-auto w-full max-w-5xl flex-1 px-4 sm:px-6">{children}</main>
                <AppFooter />
              </CitationProvider>
            </TooltipProvider>
            <Toaster />
          </LanguageProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
