"use client";

import { Inter } from "next/font/google";
import "./[locale]/globals.css"; // Path to your globals

const inter = Inter({ subsets: ["latin"] });

export default function NotFound() {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex flex-col items-center justify-center min-h-screen text-center px-4">
          <h1 className="text-4xl font-bold mb-4">404 - Page Not Found</h1>
          <p className="text-muted-foreground mb-8">
            The link you followed may be broken, or the page may have been
            removed.
          </p>
          <a
            href="/en"
            className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity"
          >
            Return to Dashboard
          </a>
        </div>
      </body>
    </html>
  );
}
