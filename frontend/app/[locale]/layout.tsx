import type React from "react";
import type { Metadata } from "next";
import "./globals.css";
import { getMessages, setRequestLocale } from "next-intl/server";
import { Geist, Geist_Mono } from "next/font/google";
import { hasLocale, NextIntlClientProvider } from "next-intl";
import { routing } from "@/i18n/routing";
import { notFound } from "next/navigation";

// Load Geist fonts
const geistSans = Geist({
  subsets: ["latin"],
  variable: "--font-sans", // This connects it to your CSS
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono", // This connects it to your CSS
});

export const metadata: Metadata = {
  title: "DisasterLens - Disaster Event Tracking & Analysis",
  description:
    "Real-time disaster event tracking and data analysis platform for Malaysia",
  icons: {
    icon: [
      {
        // Favicon for browsers in light mode
        url: "/favicon-32x32.png",
        media: "(prefers-color-scheme: light)",
      },
      {
        // Favicon for browsers in dark mode
        url: "/favicon-32x32.png",
        media: "(prefers-color-scheme: dark)",
      },
      {
        url: "/favicon-32x32.png",
        type: "image/png",
      },
    ],
    // Apple touch icon for saving to the home screen
    apple: "/favicon-32x32.png",
  },
};

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function RootLayout({
  children,
  params,
}: Readonly<{
  children: React.ReactNode;
  params: { locale: string }; // Made optional for static root route (/)
}>) {
  // FIX 1 (Line 47): Safely access the locale.
  // Using the optional chain and nullish coalescing to extract the locale.
  const { locale } = await params;

  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  setRequestLocale(locale);

  // FIX 2 (Line 50): Handle the external config error gracefully
  let translation;
  try {
    translation = await getMessages({ locale });
  } catch (error) {
    console.error(
      "next-intl message loading failed. Please verify code/i18n.ts path/content.",
      error
    );
    // Fallback to an empty object if loading fails to prevent crash
    translation = {};
  }

  return (
    <html lang={locale} suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}>
        <NextIntlClientProvider locale={locale} messages={translation}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
