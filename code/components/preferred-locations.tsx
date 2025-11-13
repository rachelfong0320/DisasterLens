"use client"

import { useState, useEffect, useMemo } from "react" // <-- ADD useMemo

interface PreferredLocationsProps {
  onLocationsChange: (locations: string[]) => void;
  initialAlerts: string[];
}

export default function PreferredLocations({ onLocationsChange, initialAlerts }: PreferredLocationsProps) {
  
  // Memoize the static list of locations
  const locations = useMemo(() => ([
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
  ]), []) // Empty dependency array: runs once

  // Memoize the initial state based on locations and initialAlerts
  const initialAlertsState = useMemo(() => {
    const state: Record<string, boolean> = {}
    for (const location of locations) {
      state[location.key] = initialAlerts.includes(location.label)
    }
    return state
  }, [initialAlerts, locations])

  const [alerts, setAlerts] = useState<Record<string, boolean>>(initialAlertsState)

  // This effect is now safe because `onLocationsChange` (from the parent) is stable.
  useEffect(() => {
    const selectedLabels = locations
      .filter(location => alerts[location.key])
      .map(location => location.label);
      
    onLocationsChange(selectedLabels); 
  }, [alerts, onLocationsChange, locations]); // Dependencies are now stable references


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