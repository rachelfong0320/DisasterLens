"use client"

import type React from "react"

import { useState } from "react"
import Header from "@/components/header"
import Footer from "@/components/footer"
import Link from "next/link"

export default function AccessDataPage() {
  type AccessForm = {
    startDate: string
    endDate: string
    locations: string[]
    exportFormat: string
  }

  const [formData, setFormData] = useState<AccessForm>({
    startDate: "2024-01-01",
    endDate: "2024-12-31",
    locations: [],
    exportFormat: "csv",
  })

  const [submitted, setSubmitted] = useState(false)

  const locations = ["Selangor", "Kuala Lumpur", "Johor", "Sabah", "Sarawak", "Penang", "Kedah", "Terengganu", "Pahang", "Melacca", "Kelantan", "Perak", "Negeri Sembilan", "Perlis"]

  const handleLocationToggle = (location: string) => {
    setFormData((prev) => ({
      ...prev,
      locations: prev.locations.includes(location)
        ? prev.locations.filter((l) => l !== location)
        : [...prev.locations, location],
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log("Downloading data:", formData)
    setSubmitted(true)
    setTimeout(() => setSubmitted(false), 3000)
  }

  return (
    <main className="min-h-screen bg-background flex flex-col">
      <Header onFilterClick={() => {}} />

      <div className="flex-1">
        {/* Hero Section */}
        <section className="bg-gradient-to-r from-primary to-primary/80 text-primary-foreground py-12 md:py-16">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 text-balance">Download Raw Disaster Data</h1>
            <p className="text-lg text-primary-foreground/90 max-w-2xl">
              Access comprehensive disaster event data for your research, analysis, and reporting needs. Select your
              preferred time period, locations, and export format to get started.
            </p>
          </div>
        </section>

        {/* Main Content */}
        <section className="py-12 md:py-16">
          <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
            <form onSubmit={handleSubmit} className="space-y-8">
              {/* Date Range Section */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold text-foreground mb-4">Select Time Frame</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">Start Date</label>
                    <input
                      type="date"
                      value={formData.startDate}
                      onChange={(e) => setFormData((prev) => ({ ...prev, startDate: e.target.value }))}
                      className="w-full px-4 py-2 border border-border rounded-md bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">End Date</label>
                    <input
                      type="date"
                      value={formData.endDate}
                      onChange={(e) => setFormData((prev) => ({ ...prev, endDate: e.target.value }))}
                      className="w-full px-4 py-2 border border-border rounded-md bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                </div>
              </div>

              {/* Location Section */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold text-foreground mb-4">Select Locations</h2>
                <p className="text-sm text-muted-foreground mb-4">
                  Choose one or more locations to include in your download
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {locations.map((location) => (
                    <label key={location} className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.locations.includes(location)}
                        onChange={() => handleLocationToggle(location)}
                        className="w-5 h-5 accent-primary rounded"
                      />
                      <span className="text-foreground font-medium">{location}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Export Format Section */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold text-foreground mb-4">Export Format</h2>
                <div className="space-y-3">
                  {[
                    {
                      id: "csv",
                      label: "CSV Format",
                      description: "Comma-separated values, compatible with Excel and most analysis tools",
                    },
                    {
                      id: "json",
                      label: "JSON Format",
                      description: "Structured JSON data for programmatic access and API integration",
                    },
                    {
                      id: "raw",
                      label: "Raw Data (.zip)",
                      description: "Complete raw data dump with all fields and metadata",
                    },
                  ].map((format) => (
                    <label
                      key={format.id}
                      className="flex items-start gap-3 p-3 border border-border rounded-md cursor-pointer hover:bg-secondary/50 transition"
                    >
                      <input
                        type="radio"
                        name="exportFormat"
                        value={format.id}
                        checked={formData.exportFormat === format.id}
                        onChange={(e) => setFormData((prev) => ({ ...prev, exportFormat: e.target.value }))}
                        className="w-5 h-5 mt-0.5 accent-primary"
                      />
                      <div className="flex-1">
                        <p className="font-medium text-foreground">{format.label}</p>
                        <p className="text-sm text-muted-foreground">{format.description}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Submit Button */}
              <div className="flex gap-4">
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-primary text-primary-foreground font-semibold rounded-md hover:opacity-90 transition"
                >
                  Download Data
                </button>
                <Link
                  href="/"
                  className="px-6 py-3 border border-border text-foreground font-semibold rounded-md hover:bg-secondary transition text-center"
                >
                  Cancel
                </Link>
              </div>

              {/* Success Message */}
              {submitted && (
                <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-md">
                  ✓ Download started! Check your downloads folder for the data file.
                </div>
              )}
            </form>

            {/* Info Box */}
            <div className="mt-12 bg-secondary/50 border border-border rounded-lg p-6">
              <h3 className="font-semibold text-foreground mb-2">Data Format Information</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• CSV files include: event_id, event_type, location, severity, date, description</li>
                <li>• JSON files contain structured data with nested metadata and coordinates</li>
                <li>• Raw data includes complete event records with all available fields</li>
                <li>• Data is updated daily and reflects events from the past 5 years</li>
              </ul>
            </div>
          </div>
        </section>
      </div>

      <Footer />
    </main>
  )
}
