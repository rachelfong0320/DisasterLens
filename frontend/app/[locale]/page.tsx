"use client";

import { useState, useCallback } from "react";
import Header from "@/components/header";
import MapSection from "@/components/map-section";
import FilterModal from "@/components/filter-modal";
import ChatbotWidget from "@/components/chatbot-widget";
import PreferredLocations from "@/components/preferred-locations";
import NewsletterSection from "@/components/newsletter-section";
import Footer from "@/components/footer";

export default function Home() {
  const [filterOpen, setFilterOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [selectedLocations, setSelectedLocations] = useState<string[]>([
    "Kuala Lumpur",
    "Johor",
    "Sarawak",
  ]);

  const handleLocationsChange = useCallback(
    (locations: string[]) => {
      setSelectedLocations(locations);
    },
    [setSelectedLocations]
  );

  return (
    <main className="min-h-screen bg-background">
      <Header />

      <section className="relative">
        <MapSection />
        <ChatbotWidget isOpen={chatOpen} onToggle={setChatOpen} />
      </section>

      {/* Pass the stable function and initial state to PreferredLocations */}
      <PreferredLocations
        onLocationsChange={handleLocationsChange}
        initialAlerts={selectedLocations}
      />
      {/* Pass the state down to NewsletterSection */}
      <NewsletterSection preferredLocations={selectedLocations} />
      <Footer />

      <FilterModal isOpen={filterOpen} onClose={() => setFilterOpen(false)} />
    </main>
  );
}
