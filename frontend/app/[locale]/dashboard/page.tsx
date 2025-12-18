"use client";

import Header from "@/components/header";
import Footer from "@/components/footer";
import ChatbotWidget from "@/components/chatbot-widget";
import MetricsCard from "@/components/metrics-card";
import ExportModal from "@/components/export-modal";
import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { 
  Waves, 
  Mountain, 
  Wind, 
  CloudFog, 
  Flame, 
  CircleSlash, 
  Activity, 
  AlertTriangle 
} from "lucide-react"
import { LucideIcon } from "lucide-react"
import TimeFilter from "@/components/time-filter"

export default function Dashboard() {
  const t = useTranslations("dashboard");
  const [exportOpen, setExportOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [stats, setStats] = useState<any>(null); // Replace 'any' with your stats type
  const [loading, setLoading] = useState(true);
  const currentYear = new Date().getFullYear();
  const today = new Date().toISOString().split('T')[0];

  // Start with 2025-01-01 by default
  const [dateRange, setDateRange] = useState({ 
    start: "2024-01-01", 
    end: "2024-12-31" 
  });

    const disasterConfig: Record<string, { label: string; icon: LucideIcon; color: string }> = {
    flood: { label: "Flood", icon: Waves, color: "text-blue-500" },
    landslide: { label: "Landslide", icon: Mountain, color: "text-amber-700" },
    storm: { label: "Storm", icon: Wind, color: "text-purple-500" },
    haze: { label: "Haze", icon: CloudFog, color: "text-orange-400" },
    "forest fire": { label: "Forest Fire", icon: Flame, color: "text-red-500" },
    sinkhole: { label: "Sinkhole", icon: CircleSlash, color: "text-emerald-800" },
    earthquake: { label: "Earthquake", icon: Activity, color: "text-stone-600" },
    tsunami: { label: "Tsunami", icon: AlertTriangle, color: "text-cyan-600" },
  };

  useEffect(() => {
      async function getStats() {
        try {
          const response = await fetch('http://localhost:8000/api/v1/analytics/filtered?start_date=2023-01-01&end_date=2025-12-31');
          const data = await response.json();
          
          // 1. Get the list from backend
          let counts = [...(data.type_counts || [])];

          // 2. Check if "tsunami" exists in the list
          const hasTsunami = counts.some(item => item.type.toLowerCase() === "tsunami");

          // 3. If missing, put 0 as default
          if (!hasTsunami) {
            counts.push({
              type: "tsunami",
              frequency: 0
            });
          }

          setStats({ ...data, type_counts: counts });

        } catch (e) {
          console.error("Fetch failed", e);
        } finally {
          setLoading(false);
        }
      }
      getStats();
    }, []);  

  return (
    <main className="min-h-screen bg-background">
      <Header onFilterClick={() => {}} />
      <ChatbotWidget isOpen={chatOpen} onToggle={setChatOpen} />

      <section className="w-full px-4 sm:px-6 lg:px-8 py-12">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-foreground">
                {t("title")}
              </h1>
              <p className="text-muted-foreground mt-1">{t("desc")}</p>
            </div>
            <div className="flex items-center gap-3">
              <TimeFilter 
                onRangeChange={(start, end) => setDateRange({ start, end })} 
              />
              <button onClick={() => setExportOpen(true)} className="...">
                Export Data
              </button>
            </div>
          </div>

          {/* Grid for 8 Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
             {Object.entries(disasterConfig).map(([key, config]) => {
              const dataItem = stats?.type_counts?.find((item: any) => item.type === key);
              return (
                <MetricsCard
                  key={key}
                  label={config.label}
                  value={dataItem ? dataItem.frequency.toString() : "0"}
                  icon={config.icon}
                  iconColor={config.color}
                />
                );
              })}
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Bar Chart */}
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">
                Events by Month
              </h3>
              <div className="space-y-2">
                {[
                  { month: "Jan", count: 45 },
                  { month: "Feb", count: 52 },
                  { month: "Mar", count: 38 },
                  { month: "Apr", count: 61 },
                  { month: "May", count: 55 },
                  { month: "Jun", count: 67 },
                ].map((item) => (
                  <div
                    key={item.month}
                    className="flex items-center justify-between text-sm"
                  >
                    <span className="w-8 text-muted-foreground font-medium">
                      {item.month}
                    </span>
                    <div className="flex-1 mx-4 bg-secondary rounded h-6 relative overflow-hidden">
                      <div
                        className="bg-chart-1 h-full rounded"
                        style={{ width: `${(item.count / 67) * 100}%` }}
                      />
                    </div>
                    <span className="w-8 text-right text-foreground font-medium">
                      {item.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Type Distribution */}
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">
                Events by Type
              </h3>
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
                      <span className="text-muted-foreground">
                        {item.count}
                      </span>
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
              <h3 className="text-lg font-semibold text-foreground mb-4">
                Events Over Time
              </h3>
              <div className="space-y-2">
                {[
                  { week: "Week 1", count: 20 },
                  { week: "Week 2", count: 35 },
                  { week: "Week 3", count: 28 },
                  { week: "Week 4", count: 45 },
                ].map((item) => (
                  <div key={item.week} className="flex items-center gap-3">
                    <span className="w-12 text-sm text-muted-foreground">
                      {item.week}
                    </span>
                    <div className="flex-1 bg-secondary rounded h-6 relative">
                      <div
                        className="bg-chart-2 h-full rounded"
                        style={{ width: `${(item.count / 45) * 100}%` }}
                      />
                    </div>
                    <span className="w-8 text-right text-sm text-foreground">
                      {item.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Districts */}
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">
                Top Affected Districts
              </h3>
              <div className="space-y-3">
                {[
                  { district: "Kuala Lumpur", count: 45 },
                  { district: "Selangor", count: 38 },
                  { district: "Johor Bahru", count: 32 },
                  { district: "Penang", count: 28 },
                  { district: "Klang", count: 22 },
                ].map((item) => (
                  <div
                    key={item.district}
                    className="flex items-center justify-between"
                  >
                    <span className="text-sm text-foreground">
                      {item.district}
                    </span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-secondary rounded h-4">
                        <div
                          className="bg-chart-4 h-4 rounded"
                          style={{ width: `${(item.count / 45) * 100}%` }}
                        />
                      </div>
                      <span className="w-8 text-right text-xs text-muted-foreground">
                        {item.count}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Trending Data */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">
                Trending Hashtags
              </h3>
              <div className="space-y-3">
                {[
                  { tag: "#DisasterRelief", count: 234 },
                  { tag: "#FloodAlert", count: 189 },
                  { tag: "#MalaysiaDisasters", count: 156 },
                  { tag: "#SafetyFirst", count: 142 },
                  { tag: "#EmergencyResponse", count: 128 },
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-primary">
                      {item.tag}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {item.count} mentions
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">
                Sentiment Analysis
              </h3>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-foreground">
                      Positive
                    </span>
                    <span className="text-sm font-semibold text-chart-1">
                      42
                    </span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div
                      className="bg-chart-1 h-2 rounded-full"
                      style={{ width: "60%" }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-foreground">
                      Neutral
                    </span>
                    <span className="text-sm font-semibold text-chart-2">
                      28
                    </span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div
                      className="bg-chart-2 h-2 rounded-full"
                      style={{ width: "40%" }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-foreground">
                      Negative
                    </span>
                    <span className="text-sm font-semibold text-chart-4">
                      8
                    </span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div
                      className="bg-chart-4 h-2 rounded-full"
                      style={{ width: "12%" }}
                    />
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
  );
}



