"use client"

import type React from "react"

import { useState } from "react"

interface NewsletterSectionProps {
  preferredLocations: string[] // New prop to receive preferred locations
}

export default function NewsletterSection({ preferredLocations }: NewsletterSectionProps) {
  const [email, setEmail] = useState("")
  const [subscribed, setSubscribed] = useState(false)

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault()
    if (email) {
      // In a real application, you would send preferredLocations along with the email
      console.log("Subscribing email:", email, "for locations:", preferredLocations.join(", "))
      setSubscribed(true)
      setTimeout(() => {
        setEmail("")
        setSubscribed(false)
      }, 3000)
    }
  }

  return (
    <section className="w-full px-4 sm:px-6 lg:px-8 py-12 bg-primary">
      <div className="max-w-2xl mx-auto text-center">
        <h2 className="text-3xl font-bold text-primary-foreground mb-2">Subscribe to Our Newsletter</h2>
        <p className="text-primary-foreground opacity-90 mb-8">
          Get the latest disaster alerts and data insights delivered to your inbox
        </p>

        <form onSubmit={handleSubscribe} className="flex gap-2 flex-col sm:flex-row">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            required
            className="flex-1 px-4 py-3 border border-primary-foreground bg-primary-foreground text-foreground rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-primary focus:ring-primary-foreground"
          />
          <button
            type="submit"
            className="px-6 py-3 bg-accent text-accent-foreground rounded-lg font-medium hover:opacity-90 transition whitespace-nowrap"
          >
            {subscribed ? "Subscribed!" : "Subscribe"}
          </button>
        </form>

        {/* Display the selected locations */}
        {preferredLocations.length > 0 && (
          <p className="mt-4 text-sm text-primary-foreground/70">
            You will receive updates for: {preferredLocations.join(", ")}
          </p>
        )}

      </div>
    </section>
  )
}