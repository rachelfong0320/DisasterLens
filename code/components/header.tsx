"use client"

import { useState } from "react"
import Link from "next/link"

interface HeaderProps {
  onFilterClick: () => void
}

export default function Header({ onFilterClick }: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <header className="border-b border-border bg-card sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-primary">
            <span className="text-2xl">📍</span>
            <span>DisasterLens</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            <Link href="/" className="text-sm font-medium text-foreground hover:text-primary transition">
              Home
            </Link>
            <Link href="/dashboard" className="text-sm font-medium text-foreground hover:text-primary transition">
              Statistics
            </Link>
            <Link href="/access-data" className="text-sm font-medium text-foreground hover:text-primary transition">
              Access Data
            </Link>
            <Link href="/subscription" className="text-sm font-medium text-foreground hover:text-primary transition">
              Subscription
            </Link>
          </nav>

          {/* Right side actions */}
          <div className="hidden md:flex items-center gap-4">
            <select className="text-sm px-3 py-2 border border-border rounded-md bg-background">
              <option>ENG</option>
              <option>BM</option>
            </select>
            <button
              onClick={onFilterClick}
              className="px-4 py-2 text-sm font-medium text-primary-foreground bg-primary rounded-md hover:opacity-90 transition"
            >
              Filter
            </button>
            <Link
              href="#"
              className="px-4 py-2 text-sm font-medium text-primary border border-primary rounded-md hover:bg-primary hover:text-primary-foreground transition"
            >
              Login
            </Link>
          </div>

          {/* Mobile menu button */}
          <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="md:hidden p-2">
            <span className="text-2xl">{mobileMenuOpen ? "✕" : "≡"}</span>
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <nav className="md:hidden pb-4 space-y-2">
            <Link href="/" className="block px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary rounded">
              Home
            </Link>
            <Link
              href="/dashboard"
              className="block px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary rounded"
            >
              Statistics
            </Link>
            <Link
              href="/access-data"
              className="block px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary rounded"
            >
              Access Data
            </Link>
            <Link
              href="/subscription"
              className="block px-4 py-2 text-sm font-medium text-foreground hover:bg-secondary rounded"
            >
              Subscription
            </Link>
            <button
              onClick={() => {
                onFilterClick()
                setMobileMenuOpen(false)
              }}
              className="w-full px-4 py-2 text-sm font-medium text-primary-foreground bg-primary rounded hover:opacity-90 transition"
            >
              Filter
            </button>
          </nav>
        )}
      </div>
    </header>
  )
}
