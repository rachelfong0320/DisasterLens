"use client"

import { useState } from "react"

interface ExportModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function ExportModal({ isOpen, onClose }: ExportModalProps) {
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [type, setType] = useState("")
  const [location, setLocation] = useState("")
  const [timeRange, setTimeRange] = useState("all")

  if (!isOpen) return null

  const handleExport = () => {
    console.log("Exporting with filters:", { dateFrom, dateTo, type, location, timeRange })
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">Export Data</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition text-2xl">
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div className="flex gap-2">
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="flex-1 px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm"
              placeholder="From"
            />
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="flex-1 px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm"
              placeholder="To"
            />
          </div>

          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm"
          >
            <option value="">Select disaster type</option>
            <option value="flood">Flood</option>
            <option value="landslide">Landslide</option>
            <option value="fire">Fire</option>
            <option value="haze">Haze</option>
            <option value="storm">Storm</option>
          </select>

          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Location"
            className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm"
          />

          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm"
          >
            <option value="all">All Time</option>
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
          </select>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t border-border bg-secondary">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted transition"
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 transition"
          >
            Export Data
          </button>
        </div>
      </div>
    </div>
  )
}
