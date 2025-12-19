"use client";

"use client";

import Header from "@/components/header";
import Footer from "@/components/footer";
import ChatbotWidget from "@/components/chatbot-widget";
import MetricsCard from "@/components/metrics-card";
import ExportModal from "@/components/export-modal";
import EventsChart from "@/components/events-chart"; 
import TimeFilter from "@/components/time-filter";
import { useState, useEffect, useMemo } from "react";
import { useTranslations } from "next-intl";
import { 
  Waves, 
  Mountain, 
  Wind, 
  CloudFog, 
  Flame, 
  CircleSlash, 
  Activity, 
  AlertTriangle,
  LucideIcon 
} from "lucide-react";
import MetricListChart from "@/components/metrics-list-charts";

export default function Dashboard() {
  const t = useTranslations("dashboard");
  const [exportOpen, setExportOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [stats, setStats] = useState<any>(null); // Replace 'any' with your stats type
  const [loading, setLoading] = useState(true);
  const currentYear = new Date().getFullYear();
  const today = new Date().toISOString().split('T')[0];
  const [keywords, setKeywords] = useState<any[]>([]); // Replace 'any' with your keyword type

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
    async function getData() {
      setLoading(true);
      try {
        // 1. Fetch Main Stats
        const statsRes = await fetch(`http://localhost:8000/api/v1/analytics/filtered?start_date=${dateRange.start}&end_date=${dateRange.end}`);
        const statsData = await statsRes.json();
        setStats(statsData);

        // 2. Fetch Keywords (Limited to 5 as you requested)
        const keywordRes = await fetch(`http://localhost:8000/api/v1/analytics/keywords/filtered?start_date=${dateRange.start}&end_date=${dateRange.end}&limit=5`);
        const keywordData = await keywordRes.json();
        setKeywords(keywordData);
        console.log("Fetched stats:", statsData);
        console.log("Fetched keywords:", keywordData);
      } catch (e) {
        console.error("Data fetch failed", e);
      } finally {
        setLoading(false);
      }
    }
    getData();
  }, [dateRange]); // Both fetchers trigger when date changes


// Transform data for Chart 1: Event Trends (Area)
  const trendData = useMemo(() => {
    if (!stats?.monthly_events) return [];

    return stats.monthly_events
      .filter((item: any) => {
        // Create a comparable YYYY-MM string
        const itemDate = `${item._id.year}-${String(item._id.month).padStart(2, '0')}-01`;
        return itemDate >= dateRange.start && itemDate <= dateRange.end;
      })
      // 1. SORT: Ensure dates are in order so the line doesn't jump
      .sort((a: any, b: any) => {
        return (a._id.year - b._id.year) || (a._id.month - b._id.month);
      })
      // 2. MAP: Format for the chart
      .map((item: any) => ({
        name: new Date(item._id.year, item._id.month - 1).toLocaleString('default', { 
          month: 'short', 
          year: '2-digit' 
        }),
        value: item.total_events,
      }));
  }, [stats, dateRange]);

    // Transform data for Chart 2: Top Districts (Bar)
  const districtData = useMemo(() => {
    if (!stats?.district_ranking) return [];

    return [...stats.district_ranking]
      .sort((a: any, b: any) => {
        // 1. Primary sort: Frequency (Descending)
        if (b.event_count !== a.event_count) {
          return b.event_count - a.event_count;
        }
        // 2. Tie-breaker: Alphabetical (A-Z)
        return a.district.localeCompare(b.district);
      })
      .slice(0, 5) // Keep only the top 5
      .map((item: any) => ({
        name: item.district.split(' ').map((s: string) => s.charAt(0).toUpperCase() + s.substring(1)).join(' '),
        value: item.event_count,
      }));
  }, [stats]);

  const sentimentData = useMemo(() => {
    if (!stats?.sentiment_counts) return [];

    return [...stats.sentiment_counts]
      .sort((a: any, b: any) => {
        // Custom priority order: Urgent (1) -> Warning (2) -> Informational (3)
        const priority: Record<string, number> = { "Urgent": 1, "Warning": 2, "Informational": 3 };
        return priority[a.label] - priority[b.label];
      })
      .map((item: any) => ({
        name: item.label,
        value: item.frequency
      }));
  }, [stats]);

  const keywordChartData = useMemo(() => {
    if (!keywords) return [];

    return [...keywords]
      .sort((a: any, b: any) => {
        // 1. Primary Sort: Frequency (Highest first)
        if (b.frequency !== a.frequency) {
          return b.frequency - a.frequency;
        }
        // 2. Tie-breaker: Alphabetical Order
        return a.keyword.localeCompare(b.keyword);
      })
      .slice(0, 5) 
      .map((item: any) => ({
        name: item.keyword.split(' ').map((s: string) => s.charAt(0).toUpperCase() + s.substring(1)).join(' '),
        value: item.frequency
      }));
  }, [keywords]);

return (
    <main className="min-h-screen bg-background">
      <Header onFilterClick={() => {}} />
      <ChatbotWidget isOpen={chatOpen} onToggle={setChatOpen} />

      <section className="w-full px-4 sm:px-6 lg:px-8 py-12">
        <div className="max-w-7xl mx-auto">
          {/* Header & Filters */}
          <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
            <div>
              <h1 className="text-3xl font-bold text-foreground">{t("title")}</h1>
              <p className="text-muted-foreground mt-1">{t("desc")}</p>
            </div>
            <div className="flex items-center gap-3">
              <TimeFilter 
                onRangeChange={(start, end) => setDateRange({ start, end })} 
              />
              <button 
                onClick={() => setExportOpen(true)} 
                className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
              >
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
                  value={loading ? "..." : (dataItem ? dataItem.frequency.toString() : "0")}
                  icon={config.icon}
                  iconColor={config.color}
                />
              );
            })}
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            
            {/* Chart 1: Event Trends */}
            <EventsChart 
              title="Event Trends" 
              type="area" 
              data={trendData} 
              color="#3b82f6" 
            />

            {/* Chart 2: Top Districts */}
            <EventsChart 
              title="Top Affected Districts" 
              type="bar" 
              data={districtData} 
              color="#3b82f6" 
            />

           {/* Chart 3: Sentiment Analysis */}
          <MetricListChart 
            title="Sentiment Analysis" 
            data={sentimentData} 
            color="#3b82f6"
            unit="Posts" 
          />

          {/* Chart 4: Trending Keywords */}
          <MetricListChart 
            title="Trending Keywords" 
            data={keywordChartData} 
            color="#3b82f6"
            unit="Hits"
          />

          </div>
        </div>
      </section>

      <Footer />

      <ExportModal isOpen={exportOpen} onClose={() => setExportOpen(false)} />
    </main>
  );
}



