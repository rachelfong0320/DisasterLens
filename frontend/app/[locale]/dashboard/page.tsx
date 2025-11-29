"use client"

import Header from "@/components/header"
import Footer from "@/components/footer"
import MetricsCard from "@/components/metrics-card"
import ExportModal from "@/components/export-modal"
import { useState } from "react"
import { useTranslations } from "next-intl"

export default function Dashboard() {
  const t = useTranslations("dashboard");
  const [exportOpen, setExportOpen] = useState(false)

  return (
    <main className="min-h-screen bg-background">
      <Header onFilterClick={() => {}} />

      <section className="w-full px-4 sm:px-6 lg:px-8 py-12">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-foreground">{t("title")}</h1>
              <p className="text-muted-foreground mt-1">{t("desc")}</p>
            </div>
            <button
              onClick={() => setExportOpen(true)}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition font-medium"
            >
              {t("btnExportData")}
            </button>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <MetricsCard label={t("totalEvent")} value="250" change="20%" trend="up" icon="📊" />
            <MetricsCard label={t("activeAlerts")} value="12" change="5%" trend="down" icon="🚨" />
            <MetricsCard label={t("affectedArea")} value="47" change="12%" trend="up" icon="📍" />
            <MetricsCard label={t("responseTime")} value="2.4h" change="8%" trend="down" icon="⏱️" />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Bar Chart */}
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">Events by Month</h3>
              <div className="space-y-2">
                {[
                  { month: "Jan", count: 45 },
                  { month: "Feb", count: 52 },
                  { month: "Mar", count: 38 },
                  { month: "Apr", count: 61 },
                  { month: "May", count: 55 },
                  { month: "Jun", count: 67 },
                ].map((item) => (
                  <div key={item.month} className="flex items-center justify-between text-sm">
                    <span className="w-8 text-muted-foreground font-medium">{item.month}</span>
                    <div className="flex-1 mx-4 bg-secondary rounded h-6 relative overflow-hidden">
                      <div className="bg-chart-1 h-full rounded" style={{ width: `${(item.count / 67) * 100}%` }} />
                    </div>
                    <span className="w-8 text-right text-foreground font-medium">{item.count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Type Distribution */}
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">Events by Type</h3>
              <div className="space-y-3">
                {[
                  { type: "Flood", count: 120, color: "bg-chart-1" },
                  { type: "Landslide", count: 85, color: "bg-chart-2" },
                  { type: "Fire", count: 25, color: "bg-chart-3" },
                  { type: "Haze", count: 15, color: "bg-chart-4" },
                  { type: "Storm", count: 5, color: "bg-accent" },
                ].map((item) => (
                  <div key={item.type}>
                    <div className="flex items-center justify-between mb-1 text-sm">
                      <span className="text-foreground">{item.type}</span>
                      <span className="text-muted-foreground">{item.count}</span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-2">
                      <div
                        className={`${item.color} h-2 rounded-full`}
                        style={{ width: `${(item.count / 120) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Weekly Trend */}
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">Events Over Time</h3>
              <div className="space-y-2">
                {[
                  { week: "Week 1", count: 20 },
                  { week: "Week 2", count: 35 },
                  { week: "Week 3", count: 28 },
                  { week: "Week 4", count: 45 },
                ].map((item) => (
                  <div key={item.week} className="flex items-center gap-3">
                    <span className="w-12 text-sm text-muted-foreground">{item.week}</span>
                    <div className="flex-1 bg-secondary rounded h-6 relative">
                      <div className="bg-chart-2 h-full rounded" style={{ width: `${(item.count / 45) * 100}%` }} />
                    </div>
                    <span className="w-8 text-right text-sm text-foreground">{item.count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Districts */}
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">Top Affected Districts</h3>
              <div className="space-y-3">
                {[
                  { district: "Kuala Lumpur", count: 45 },
                  { district: "Selangor", count: 38 },
                  { district: "Johor Bahru", count: 32 },
                  { district: "Penang", count: 28 },
                  { district: "Klang", count: 22 },
                ].map((item) => (
                  <div key={item.district} className="flex items-center justify-between">
                    <span className="text-sm text-foreground">{item.district}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-secondary rounded h-4">
                        <div className="bg-chart-4 h-4 rounded" style={{ width: `${(item.count / 45) * 100}%` }} />
                      </div>
                      <span className="w-8 text-right text-xs text-muted-foreground">{item.count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Trending Data */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">Trending Hashtags</h3>
              <div className="space-y-3">
                {[
                  { tag: "#DisasterRelief", count: 234 },
                  { tag: "#FloodAlert", count: 189 },
                  { tag: "#MalaysiaDisasters", count: 156 },
                  { tag: "#SafetyFirst", count: 142 },
                  { tag: "#EmergencyResponse", count: 128 },
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-primary">{item.tag}</span>
                    <span className="text-sm text-muted-foreground">{item.count} mentions</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">Sentiment Analysis</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-foreground">Positive</span>
                    <span className="text-sm font-semibold text-chart-1">42</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div className="bg-chart-1 h-2 rounded-full" style={{ width: "60%" }} />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-foreground">Neutral</span>
                    <span className="text-sm font-semibold text-chart-2">28</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div className="bg-chart-2 h-2 rounded-full" style={{ width: "40%" }} />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-foreground">Negative</span>
                    <span className="text-sm font-semibold text-chart-4">8</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div className="bg-chart-4 h-2 rounded-full" style={{ width: "12%" }} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Footer />

      <ExportModal isOpen={exportOpen} onClose={() => setExportOpen(false)} />
    </main>
  )
}
