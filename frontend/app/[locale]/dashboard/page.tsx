"use client";

import Header from "@/components/header";
import Footer from "@/components/footer";
import ChatbotWidget from "@/components/chatbot-widget";
import MetricsCard from "@/components/metrics-card";
import EventsChart from "@/components/events-chart"; 
import TimeFilter from "@/components/time-filter";
import { useState, useEffect, useMemo } from "react";
import { useReportGenerator } from "@/hooks/use-report-generator";
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
import DisasterFilter from "@/components/disaster-stats-filter";

export default function Dashboard() {
  const t = useTranslations("dashboard");
  const { generateReport, isGenerating } = useReportGenerator();
  
  const [chatOpen, setChatOpen] = useState(false);
  const [stats, setStats] = useState<any>(null); 
  const [loading, setLoading] = useState(true);
  const [keywords, setKeywords] = useState<any[]>([]); 
  const [disasterType, setDisasterType] = useState<string>("all");

  const [dateRange, setDateRange] = useState({ 
    start: "2025-01-01", 
    end: "2025-12-31" 
  });

  const currentViewYear = new Date(dateRange.start).getFullYear(); 

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
        const typeParam = disasterType !== "all" ? `&disaster_type=${disasterType}` : "";
        const baseUrl = `http://localhost:8000/api/v1/analytics`;

        const [statsRes, keywordRes] = await Promise.all([
          fetch(`${baseUrl}/filtered?start_date=${dateRange.start}&end_date=${dateRange.end}${typeParam}`),
          fetch(`${baseUrl}/keywords/filtered?start_date=${dateRange.start}&end_date=${dateRange.end}&limit=5${typeParam}`)
        ]);

        const statsData = await statsRes.json();
        const keywordData = await keywordRes.json();

        setStats(statsData);
        setKeywords(keywordData);
      } catch (e) {
        console.error("Fetch error", e);
      } finally {
        setLoading(false);
      }
    }
    getData();
  }, [dateRange, disasterType]); 

// Transform data for Chart 1: Event Trends (Area)
  const trendData = useMemo(() => {
    const filterYear = new Date(dateRange.start).getFullYear();
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

    return months.map((month, index) => {
      const found = stats?.monthly_events?.find(
        (item: any) => item._id.year === filterYear && item._id.month === index + 1
      );
      return { name: month, value: found ? found.total_events : 0 };
    });
  }, [stats, dateRange.start]);

  const districtData = useMemo(() => {    
    if (!stats?.district_ranking || stats.district_ranking.length === 0) {
      return ["Area 1", "Area 2", "Area 3", "Area 4", "Area 5"].map(name => ({ name, value: 0, state: "" }));
    }
    return [...stats.district_ranking]
      .sort((a: any, b: any) => b.event_count - a.event_count)
      .slice(0, 5)
      .map((item: any) => ({
        name: item.district.split(' ').map((s: string) => s.charAt(0).toUpperCase() + s.substring(1)).join(' '),
        value: item.event_count,
        state: item.state
      }));
  }, [stats]);

  const sentimentData = useMemo(() => {
    const categories = ["Urgent", "Warning", "Informational"];
    return categories.map(label => {
      const found = stats?.sentiment_counts?.find((item: any) => item.label === label);
      return { name: label, value: found ? found.frequency : 0 };
    });
  }, [stats]);

  const keywordChartData = useMemo(() => {
    if (!keywords || keywords.length === 0) {
      return Array(5).fill(null).map((_, i) => ({ name: `Slot ${i + 1}`, value: 0 }));
    }
    return [...keywords]
      .sort((a: any, b: any) => b.frequency - a.frequency)
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
          <div className="hidden print:flex flex-col mb-10 border-b-2 border-primary pb-6">
          <h1 className="text-4xl font-bold text-blue-900">DisasterLens Analysis Report</h1>
          <div className="flex justify-between mt-4 text-sm text-gray-600">
            <p>Filtered by: <span className="font-bold uppercase text-primary">{disasterType}</span></p>
            <p>Period: {dateRange.start} — {dateRange.end}</p>
            <p>Generated: {new Date().toLocaleDateString()}</p>
          </div>
        </div>

          {/* Header & Filters */}
          <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
            <div className="print:block">
              <h1 className="text-3xl font-bold text-foreground">{t("title")}</h1>
              <p className="text-muted-foreground mt-1">{t("desc")}</p>
            </div>
            
            <div className="flex items-center gap-3 print:hidden">
              <DisasterFilter value={disasterType} onChange={setDisasterType} options={disasterConfig} />
              <TimeFilter onRangeChange={(start, end) => setDateRange({ start, end })} />
              <button 
                onClick={generateReport}
                disabled={isGenerating}
                className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 disabled:opacity-50 transition-all shadow-sm"
              >
                {isGenerating ? "Preparing..." : "Generate Report"}
              </button>
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {Object.entries(disasterConfig).map(([key, config]) => {
              const dataItem = stats?.type_counts?.find((item: any) => item.type === key);
              const isActive = disasterType === "all" || disasterType === key;
              return (
                <div key={key} className={`transition-all duration-500 ${isActive ? "opacity-100 scale-100" : "opacity-30 scale-95 grayscale print:hidden"}`}>
                  <MetricsCard
                    label={config.label}
                    value={loading ? "..." : (dataItem ? dataItem.frequency.toString() : "0")}
                    icon={config.icon}
                    iconColor={config.color}
                  />
                </div>
              );
            })}
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <EventsChart title={`Event Trends (${currentViewYear})`} type="area" data={trendData} color="#3b82f6" />
            <EventsChart title="Top Affected Districts" type="bar" data={districtData} color="#3b82f6" />
            <MetricListChart title="Sentiment Analysis" data={sentimentData} color="#3b82f6" unit="Post" />
            <MetricListChart title="Trending Keywords" data={keywordChartData} color="#3b82f6" unit="Hit" />
          </div>
        </div>

        <div className="hidden print:block pt-8 border-t border-gray-200">
          <h2 className="text-xl font-bold mb-4">Monthly Event Summary ({currentViewYear})</h2>
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-50">
                <th className="border p-2 text-left">Month</th>
                {trendData.map(d => <th key={d.name} className="border p-2 text-center text-xs">{d.name}</th>)}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="border p-2 font-semibold">Total Events</td>
                {trendData.map(d => <td key={d.name} className="border p-2 text-center">{d.value}</td>)}
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <Footer />
    </main>
  );
}