"use client";

import { useState, useEffect, useMemo } from "react";
import { useLocale, useTranslations } from "next-intl";
import {
  Waves, Mountain, Wind, CloudRain, Flame, CircleSlash, Activity, AlertTriangle,
} from "lucide-react";

import Header from "@/components/header";
import Footer from "@/components/footer";
import ChatbotWidget from "@/components/chatbot-widget";
import MetricsCard from "@/components/metrics-card";
import EventsChart from "@/components/events-chart";
import TimeFilter from "@/components/time-filter";
import MetricListChart from "@/components/metrics-list-charts";
import DisasterFilter from "@/components/disaster-stats-filter";
import { useReportGenerator } from "@/hooks/use-report-generator";

interface StatsType {
  monthly_events?: {
    _id: { year: number; month: number };
    total_events: number;
  }[];
  district_ranking?: { district: string; state: string; event_count: number }[];
  type_counts?: { type: string; frequency: number }[];
  sentiment_counts?: { label: string; frequency: number }[];
}

interface KeywordType {
  keyword: string;
  frequency: number;
}

export default function Dashboard() {
  const locale = useLocale();
  const t = useTranslations("dashboard");
  const d = useTranslations("disasterType");
  const s = useTranslations("sentiment");
  const { generateReport, isGenerating } = useReportGenerator();

  // --- Core State ---
  const [stats, setStats] = useState<StatsType | null>(null);
  const [keywords, setKeywords] = useState<KeywordType[]>([]);
  const [disasterType, setDisasterType] = useState<string>("all");
  const [trendType, setTrendType] = useState<"keyword" | "hashtag">("keyword");
  const [dateRange, setDateRange] = useState({ start: "2025-01-01", end: "2025-12-31" });
  const [chatOpen, setChatOpen] = useState(false);

  // --- UX & Error Handling States ---
  const [globalLoading, setGlobalLoading] = useState(true);
  const [wordsLoading, setWordsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEmpty, setIsEmpty] = useState(false);

  const currentViewYear = new Date(dateRange.start).getFullYear();
  const baseUrl = `http://localhost:8000/api/v1/analytics`;

  const disasterConfig = {
    flood: { icon: Waves, color: "text-blue-500" },
    landslide: { icon: Mountain, color: "text-amber-600" },
    forestFire: { icon: Flame, color: "text-red-500" },
    storm: { icon: CloudRain, color: "text-indigo-500" },
    haze: { icon: Wind, color: "text-gray-500" },
    sinkhole: { icon: CircleSlash, color: "text-brown-600" },
    earthquake: { icon: Activity, color: "text-orange-600" },
    tsunami: { icon: AlertTriangle, color: "text-cyan-600" },
  } as const;

  // --- Effect 1: Global Statistics (Synchronized Fetch) ---
  useEffect(() => {
    async function getGlobalStats() {
      setGlobalLoading(true);
      setError(null);
      setIsEmpty(false);
      try {
        // Robust check for "all" regardless of casing or extra words (e.g., "All Types")
        const isAll = !disasterType || disasterType.toLowerCase().includes("all");
        const typeParam = isAll ? "" : `&disaster_type=${disasterType}`;
        
        const res = await fetch(`${baseUrl}/filtered?start_date=${dateRange.start}&end_date=${dateRange.end}${typeParam}`);
        
        if (!res.ok) throw new Error("Connection to server failed.");
        const statsData: StatsType = await res.json();

        // Determine if data is empty based on array lengths
        const hasNoData = 
          (statsData.type_counts?.length ?? 0) === 0 && 
          (statsData.monthly_events?.length ?? 0) === 0;

        setIsEmpty(hasNoData);
        setStats(statsData);
      } catch (e) {
        setError("Unable to load statistics. Please try again later.");
      } finally {
        setGlobalLoading(false);
      }
    }
    getGlobalStats();
  }, [dateRange, disasterType]);

  // --- Effect 2: Trending Words (Keywords/Hashtags) ---
  useEffect(() => {
    async function getTrendingWords() {
      setWordsLoading(true);
      try {
        const isAll = !disasterType || disasterType.toLowerCase().includes("all");
        const typeParam = isAll ? "" : `&disaster_type=${disasterType}`;
        const res = await fetch(
          `${baseUrl}/trending/filtered?start_date=${dateRange.start}&end_date=${dateRange.end}&limit=5&trend_type=${trendType}${typeParam}`
        );
        const keywordData = await res.json();
        setKeywords(keywordData);
      } catch (e) {
        console.error("Keyword Fetch error", e);
      } finally {
        setWordsLoading(false);
      }
    }
    getTrendingWords();
  }, [dateRange, disasterType, trendType]);

  // --- Memoized Data Transformations ---
  const trendData = useMemo(() => {
    const months = Array.from({ length: 12 }, (_, i) =>
      new Intl.DateTimeFormat(locale, { month: "short" }).format(new Date(2000, i))
    );
    return months.map((month, index) => {
      const found = stats?.monthly_events?.find(
        (item) => item._id.year === currentViewYear && item._id.month === index + 1
      );
      return { name: month, value: found ? found.total_events : 0 };
    });
  }, [stats, currentViewYear, locale]);

  const districtData = useMemo(() => {
    if (!stats?.district_ranking || stats.district_ranking.length === 0) return [];
    return [...stats.district_ranking]
      .sort((a, b) => b.event_count - a.event_count)
      .slice(0, 5)
      .map((item) => ({
        name: item.district.split(" ").map(s => s.charAt(0).toUpperCase() + s.substring(1)).join(" "),
        value: item.event_count,
        state: item.state,
      }));
  }, [stats]);

  const sentimentData = useMemo(() => {
    const categories = ["urgent", "warning", "informational"] as const;
    const labelMap: Record<string, string> = { Urgent: "urgent", Warning: "warning", Informational: "informational" };
    return categories.map((key) => {
      const found = stats?.sentiment_counts?.find((item) => labelMap[item.label] === key);
      return { name: s(key), value: found ? found.frequency : 0 };
    });
  }, [stats, s]);

  const keywordChartData = useMemo(() => {
    if (!keywords || keywords.length === 0) return [];
    return [...keywords]
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 5)
      .map((item) => ({
        name: trendType === "hashtag" 
          ? `#${item.keyword.replace(/\s+/g, "").toLowerCase()}` 
          : item.keyword.split(" ").map(w => w.charAt(0).toUpperCase() + w.substring(1).toLowerCase()).join(" "),
        value: item.frequency,
      }));
  }, [keywords, trendType]);

  return (
    <main className="min-h-screen bg-background">
      <Header />
      <ChatbotWidget isOpen={chatOpen} onToggle={setChatOpen} />

      <section className="w-full px-4 sm:px-6 lg:px-8 py-12">
        <div className="max-w-7xl mx-auto">

          {/* PDF Report Header */}
          <div className="hidden print:flex flex-col mb-8 border-b pb-4">
            <h1 className="text-3xl font-bold">DisasterLens Analysis Report</h1>
            <p className="text-gray-500">
              Generated on: {new Date().toLocaleString(locale, { 
                dateStyle: 'full', 
                timeStyle: 'short' 
              })}
            </p>
            <p className="text-sm text-gray-400 mt-2">
              Data Range: {dateRange.start} to {dateRange.end} | Disaster Type: {disasterType}
            </p>
          </div>
          
          {/* Dashboard Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
              <p className="text-muted-foreground mt-1">{t("desc")}</p>
            </div>

            <div className="flex items-center gap-3 print:hidden text-sm font-medium">
              <DisasterFilter value={disasterType} onChange={setDisasterType} options={disasterConfig} />
              <TimeFilter onRangeChange={(start, end) => setDateRange({ start, end })} />
              <button
                onClick={generateReport}
                disabled={isGenerating || globalLoading || isEmpty || !!error}
                className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground h-10 px-4 transition-all shadow-sm disabled:opacity-50"
              >
                {isGenerating ? t("preparing") : t("reportBtn")}
              </button>
            </div>
          </div>

          <div className="relative min-h-[500px]">
            
            {/* 1. LOADING: Skeleton Pulse Grid */}
            {globalLoading && (
              <div className="animate-in fade-in duration-500">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                  {[...Array(8)].map((_, i) => (
                    <div key={i} className="h-32 bg-gray-100/80 animate-pulse rounded-xl" />
                  ))}
                </div>
              </div>
            )}

            {/* 2. ERROR: Technical Failure Interface */}
            {!globalLoading && error && (
              <div className="animate-in fade-in zoom-in-95 duration-500 flex flex-col items-center justify-center p-16 bg-red-50 border border-red-200 rounded-xl text-red-700 text-center">
                <AlertTriangle className="w-12 h-12 mb-4 opacity-50" />
                <h3 className="text-xl font-bold">{t.has("errorTitle") ? t("errorTitle") : "System Connection Issue"}</h3>
                <p className="text-sm mb-6">{error}</p>
                <button onClick={() => window.location.reload()} className="px-6 py-2 bg-red-600 text-white rounded-md font-medium hover:bg-red-700 transition-colors">
                  Retry Connection
                </button>
              </div>
            )}

            {/* 3. EMPTY: Success but zero results found */}
            {!globalLoading && !error && isEmpty && (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 flex flex-col items-center justify-center p-20 bg-gray-50 border border-dashed border-gray-300 rounded-xl text-gray-500 text-center">
                <div className="bg-white p-4 rounded-full shadow-sm mb-4">
                  <CircleSlash className="w-10 h-10 text-gray-300" />
                </div>
                <h3 className="text-xl font-bold text-gray-700">{t.has("noDataTitle") ? t("noDataTitle") : "No Records Found"}</h3>
                <p className="text-sm mt-2">
                   No data available for <span className="font-bold text-primary uppercase">{disasterType}</span> for this period.
                </p>
              </div>
            )}

            {/* 4. DATA SUCCESS: Render only when verified and loaded */}
            {!globalLoading && !error && !isEmpty && stats && (
              <div className="animate-in fade-in duration-1000">
                
                {/* Metrics Grid - Fixed Activity Logic */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                  {Object.entries(disasterConfig).map(([key, config]) => {
                    const dataItem = stats?.type_counts?.find(item => item.type === key);
                    
                    const isAllView = !disasterType || disasterType.toLowerCase().includes("all");
                    const isActive = isAllView || disasterType === key;

                    return (
                      <div key={key} className={`transition-all duration-300 ${isActive ? "opacity-100 grayscale-0 scale-100" : "opacity-30 grayscale scale-95"}`}>
                        <MetricsCard
                          label={d(key)}
                          value={dataItem ? dataItem.frequency.toString() : "0"}
                          icon={config.icon}
                          iconColor={config.color}
                        />
                      </div>
                    );
                  })}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                  <EventsChart title={`${t("eventTrend")} (${currentViewYear})`} type="area" data={trendData} color="#3b82f6" />
                  <EventsChart title={t("affected")} type="bar" data={districtData} color="#3b82f6" />
                  <MetricListChart title={t("sentiment")} data={sentimentData} color="#3b82f6" unit="Post" />
                  
                  {/* Independent Keyword Chart Container */}
                  <div className={`relative transition-all duration-300 ${wordsLoading ? "opacity-50" : "opacity-100"}`}>
                    <div className="absolute top-4 right-4 z-10 flex bg-gray-100 p-1 rounded-lg border border-gray-200 shadow-inner w-[180px]">
                      <div className={`absolute top-1 bottom-1 left-1 w-[86px] bg-white rounded-md shadow-sm transition-transform duration-300 ease-in-out ${trendType === "hashtag" ? "translate-x-[88px]" : "translate-x-0"}`} />
                      <button onClick={() => setTrendType("keyword")} className={`relative z-20 flex-1 px-2 py-1.5 text-[10px] font-bold uppercase transition-colors duration-200 ${trendType === "keyword" ? "text-blue-600" : "text-gray-500"}`}>Keywords</button>
                      <button onClick={() => setTrendType("hashtag")} className={`relative z-20 flex-1 px-2 py-1.5 text-[10px] font-bold uppercase transition-colors duration-200 ${trendType === "hashtag" ? "text-blue-600" : "text-gray-500"}`}>Hashtags</button>
                    </div>
                    
                    {keywordChartData.length === 0 && !wordsLoading ? (
                      <div className="flex flex-col items-center justify-center h-[300px] border rounded-xl bg-gray-50/50 text-gray-400 text-center">
                        <CircleSlash size={32} className="mb-2 opacity-20" />
                        <p className="text-sm italic">No trending items found for this selection.</p>
                      </div>
                    ) : (
                      <MetricListChart title={trendType === "keyword" ? t("keyword") : "Trending Hashtags"} data={keywordChartData} color="#3b82f6" unit="Hit" />
                    )}
                  </div>

                  <div className="hidden print:grid grid-cols-2 gap-6 mb-8">
                      <MetricListChart 
                          title="Trending Hashtags" 
                          data={keywords.slice(0, 5).map(item => ({
                              name: `#${item.keyword.replace(/\s+/g, "").toLowerCase()}`,
                              value: item.frequency
                          }))} 
                          color="#3b82f6" 
                          unit="Hit" 
                      />
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
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}