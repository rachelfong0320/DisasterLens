"use client";

import { useState } from "react";
import { Link } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import LocaleSwitcher from "./locale-switcher";

interface HeaderProps {
  onFilterClick: () => void;
}

export default function Header({ onFilterClick }: HeaderProps) {
  const t = useTranslations("header");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="border-b border-border bg-card sticky top-0 z-2000">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center gap-2 font-bold text-3xl text-primary"
          >
            <span>DisasterLens</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            <Link
              href="/"
              className="text-sm font-medium text-foreground hover:text-primary transition"
            >
              {t("home")}
            </Link>
            <Link
              href="/dashboard"
              className="text-sm font-medium text-foreground hover:text-primary transition"
            >
              {t("statistics")}
            </Link>
            <Link
              href="/access-data"
              className="text-sm font-medium text-foreground hover:text-primary transition"
            >
              {t("access_data")}
            </Link>
          </nav>

          {/* Right side actions */}
          <div className="hidden md:flex items-center gap-4">
            <LocaleSwitcher />
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2"
          >
            <span className="text-2xl">{mobileMenuOpen ? "✕" : "≡"}</span>
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <nav className="md:hidden pb-4 space-y-2">
            <Link
              href="/"
              className="block px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary rounded"
            >
              {t("home")}
            </Link>
            <Link
              href="/dashboard"
              className="block px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary rounded"
            >
              {t("statistics")}
            </Link>
            <Link
              href="/access-data"
              className="block px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary rounded"
            >
              {t("access_data")}
            </Link>
            <Link
              href="/subscription"
              className="block px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary rounded"
            >
              {t("subscription")}
            </Link>
          </nav>
        )}
      </div>
    </header>
  );
}
