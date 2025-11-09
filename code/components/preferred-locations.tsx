"use client"

import { useState } from "react"

export default function PreferredLocations() {
  const [alerts, setAlerts] = useState<Record<string, boolean>>({
    kuala_lumpur: true,
    selangor: false,
    johor: true,
    sabah: false,
    sarawak: true,
  })

  const locations = [
    { key: "kuala_lumpur", label: "Kuala Lumpur", icon: "📌" },
    { key: "selangor", label: "Selangor", icon: "📌" },
    { key: "johor", label: "Johor", icon: "📌" },
    { key: "sabah", label: "Sabah", icon: "📌" },
    { key: "sarawak", label: "Sarawak", icon: "📌" },
  ]

  const handleToggle = (location: string) => {
    setAlerts((prev) => ({
      ...prev,
      [location]: !prev[location as keyof typeof prev],
    }))
  }

  return (
    <section className="w-full px-4 sm:px-6 lg:px-8 py-12 bg-secondary">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-2xl font-bold text-foreground mb-2">Set Preferred Locations</h2>
        <p className="text-muted-foreground mb-8">Choose areas to receive alerts and updates</p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {locations.map((location) => (
            <button
              key={location.key}
              onClick={() => handleToggle(location.key)}
              className={`p-4 rounded-lg border-2 transition ${
                alerts[location.key as keyof typeof alerts]
                  ? "border-primary bg-primary/10 text-foreground"
                  : "border-border bg-background text-muted-foreground hover:border-primary"
              }`}
            >
              <span className="text-2xl mr-2">{location.icon}</span>
              <span className="font-medium">{location.label}</span>
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}
