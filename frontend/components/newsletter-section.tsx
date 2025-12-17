"use client"

import type React from "react"
import { useState } from "react"
import { useTranslations } from "next-intl"

interface NewsletterSectionProps {
  preferredLocations: string[] 
}

export default function NewsletterSection({ preferredLocations }: NewsletterSectionProps) {
  const t = useTranslations("newsletterSection");

  const [email, setEmail] = useState("")
  const [subscribed, setSubscribed] = useState(false)
  const [loading, setLoading] = useState(false) // Add loading state

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // 1. Validation: Ensure user picked a location
    if (preferredLocations.length === 0) {
      alert("Please select at least one location from the section above.");
      return;
    }

    if (email) {
      setLoading(true);
      try {
        // 2. Call the Backend API
        const response = await fetch("http://localhost:8000/api/v1/subscribe", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: email,
            locations: preferredLocations.map(loc => loc.toLowerCase()),
          }),
        })

        if (response.ok) {
          console.log("Subscribing email:", email, "for locations:", preferredLocations.join(", "))
          setSubscribed(true)
          // Reset form after 3 seconds
          setTimeout(() => {
            setEmail("")
            setSubscribed(false)
          }, 3000)
        } else {
          alert("Subscription failed. Please try again.");
        }
      } catch (error) {
        console.error("Error connecting to server:", error)
        alert("Server error. Please check your connection.");
      } finally {
        setLoading(false);
      }
    }
  }

  return (
    <section className="w-full px-4 sm:px-6 lg:px-8 py-12 bg-primary">
      <div className="max-w-2xl mx-auto text-center">
        <h2 className="text-3xl font-bold text-primary-foreground mb-2">{t("title")}</h2>
        <p className="text-primary-foreground opacity-90 mb-8">
          {t("desc")}
        </p>

        <form onSubmit={handleSubscribe} className="flex gap-2 flex-col sm:flex-row">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t("email")}
            required
            className="flex-1 px-4 py-3 border border-primary-foreground bg-primary-foreground text-foreground rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-primary focus:ring-primary-foreground"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-accent text-accent-foreground rounded-lg font-medium hover:opacity-90 transition whitespace-nowrap disabled:opacity-50"
          >
            {loading ? "..." : (subscribed ? t("Subscribed") : t("Subscribe"))}
          </button>
        </form>

        {preferredLocations.length > 0 && (
          <p className="mt-4 text-sm text-primary-foreground/70">
            {t("receiveUpdate")} {preferredLocations.join(", ")}
          </p>
        )}
      </div>
    </section>
  )
}