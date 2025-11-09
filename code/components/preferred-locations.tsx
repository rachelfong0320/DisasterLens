"use client"

import { useState, useEffect } from "react"

interface PreferredLocationsProps {
  onLocationsChange: (locations: string[]) => void;
  initialAlerts: string[];
}

export default function PreferredLocations({ onLocationsChange, initialAlerts }: PreferredLocationsProps) {
  // Map the initial array of labels to the internal boolean record state
  const initialAlertsState = {
    kuala_lumpur: initialAlerts.includes("Kuala Lumpur"),
    selangor: initialAlerts.includes("Selangor"),
    johor: initialAlerts.includes("Johor"),
    sabah: initialAlerts.includes("Sabah"),
    sarawak: initialAlerts.includes("Sarawak"),
    kedah: initialAlerts.includes("Kedah"),
    penang: initialAlerts.includes("Penang"),
    pahang: initialAlerts.includes("Pahang"),
    terengganu: initialAlerts.includes("Terengganu"),
    melacca: initialAlerts.includes("Melacca"),
    kelantan: initialAlerts.includes("Kelantan"),
    perak: initialAlerts.includes("Perak"),
    negeri_sembilan: initialAlerts.includes("Negeri Sembilan"),
    perlis: initialAlerts.includes("Perlis"),
  }

  const [alerts, setAlerts] = useState<Record<string, boolean>>(initialAlertsState)

  const locations = [
    { key: "kuala_lumpur", label: "Kuala Lumpur"},
    { key: "selangor", label: "Selangor"},
    { key: "johor", label: "Johor"},
    { key: "sabah", label: "Sabah"},
    { key: "sarawak", label: "Sarawak"},
    { key: "kedah", label: "Kedah"},
    { key: "penang", label: "Penang"},
    { key: "pahang", label: "Pahang"},
    { key: "terengganu", label: "Terengganu"},
    { key: "melacca", label: "Melacca"},
    { key: "kelantan", label: "Kelantan"},
    { key: "perak", label: "Perak"},
    { key: "negeri_sembilan", label: "Negeri Sembilan"},
    { key: "perlis", label: "Perlis"},
  ]

  // Effect to call parent update function whenever local state changes
  useEffect(() => {
    const selectedLabels = locations
      .filter(location => alerts[location.key as keyof typeof alerts])
      .map(location => location.label);
    onLocationsChange(selectedLabels);
  }, [alerts, onLocationsChange, locations]);


  const handleToggle = (locationKey: string) => {
    setAlerts((prev) => ({
      ...prev,
      [locationKey]: !prev[locationKey as keyof typeof prev],
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
              <span className="font-medium">{location.label}</span>
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}