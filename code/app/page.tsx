"use client"

import { useState } from "react"
import Header from "@/components/header"
import MapSection from "@/components/map-section"
import FilterModal from "@/components/filter-modal"
import ChatbotWidget from "@/components/chatbot-widget"
import PreferredLocations from "@/components/preferred-locations"
import NewsletterSection from "@/components/newsletter-section"
import Footer from "@/components/footer"

export default function Home() {
  const [filterOpen, setFilterOpen] = useState(false)
  const [chatOpen, setChatOpen] = useState(false)

  return (
    <main className="min-h-screen bg-background">
      <Header onFilterClick={() => setFilterOpen(true)} />

      <section className="relative">
        <MapSection />
        <ChatbotWidget isOpen={chatOpen} onToggle={setChatOpen} />
      </section>

      <PreferredLocations />
      <NewsletterSection />
      <Footer />

      <FilterModal isOpen={filterOpen} onClose={() => setFilterOpen(false)} />
    </main>
  )
}
