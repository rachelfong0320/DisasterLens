"use client"

import { useState } from "react"

interface DisasterPin {
  id: string
  type: "flood" | "landslide" | "fire" | "storm" | "haze"
  location: string
  severity: "low" | "medium" | "high"
  coordinates: { x: number; y: number }
}

const DISASTER_PINS: DisasterPin[] = [
  { id: "1", type: "flood", location: "Terengganu", severity: "high", coordinates: { x: 72, y: 35 } },
  { id: "2", type: "flood", location: "Johor", severity: "medium", coordinates: { x: 68, y: 80 } },
  { id: "3", type: "landslide", location: "Sabah", severity: "high", coordinates: { x: 85, y: 60 } },
  { id: "4", type: "haze", location: "Sarawak", severity: "medium", coordinates: { x: 78, y: 55 } },
  { id: "5", type: "fire", location: "Penang", severity: "low", coordinates: { x: 65, y: 42 } },
]

export default function MapSection() {
  const [selectedPin, setSelectedPin] = useState<string | null>(null)

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "high":
        return "#dc2626"
      case "medium":
        return "#f97316"
      case "low":
        return "#3b82f6"
      default:
        return "#3b82f6"
    }
  }

  return (
    <section className="w-full px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-7xl mx-auto">
        <div className="relative bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg overflow-hidden shadow-lg h-96 md:h-[500px]">
          {/* Simplified Malaysia Map Background */}
          <svg viewBox="0 0 100 100" className="w-full h-full opacity-20" preserveAspectRatio="xMidYMid slice">
            <rect width="100" height="100" fill="currentColor" />
            {/* Map outline approximation */}
            <path
              d="M 30 20 L 70 20 L 75 40 L 80 50 L 70 60 L 60 70 L 40 75 L 20 60 L 15 40 Z"
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
              opacity="0.5"
            />
          </svg>

          {/* Disaster pins */}
          <div className="absolute inset-0">
            {DISASTER_PINS.map((pin) => (
              <button
                key={pin.id}
                onClick={() => setSelectedPin(selectedPin === pin.id ? null : pin.id)}
                className="absolute transform -translate-x-1/2 -translate-y-1/2 group focus:outline-none"
                style={{
                  left: `${pin.coordinates.x}%`,
                  top: `${pin.coordinates.y}%`,
                }}
              >
                <div
                  className="w-4 h-4 rounded-full shadow-lg transition-all group-hover:scale-150 cursor-pointer"
                  style={{ backgroundColor: getSeverityColor(pin.severity) }}
                />
                <div
                  className="w-3 h-3 rounded-full absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 opacity-50 animate-pulse"
                  style={{ backgroundColor: getSeverityColor(pin.severity) }}
                />

                {/* Tooltip */}
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 bg-card border border-border px-3 py-2 rounded-md text-xs font-medium text-foreground whitespace-nowrap opacity-0 group-hover:opacity-100 transition pointer-events-none shadow-lg">
                  {pin.location}
                  <br />
                  <span className="text-muted-foreground">
                    {pin.type} - {pin.severity}
                  </span>
                </div>
              </button>
            ))}
          </div>

          {/* Search overlay */}
          <div className="absolute top-4 right-4 bg-white p-3 rounded-full shadow-md z-10">
            <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>

          {/* Selected pin details */}
          {selectedPin && (
            <div className="absolute bottom-4 left-4 bg-card border border-border rounded-lg p-4 shadow-lg max-w-xs">
              <div className="font-semibold text-foreground mb-2">
                {DISASTER_PINS.find((p) => p.id === selectedPin)?.location}
              </div>
              <div className="text-sm text-muted-foreground">
                <p>Type: {DISASTER_PINS.find((p) => p.id === selectedPin)?.type}</p>
                <p>Severity: {DISASTER_PINS.find((p) => p.id === selectedPin)?.severity}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
