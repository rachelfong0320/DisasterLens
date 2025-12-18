"use client";

import type React from "react";
import { useState } from "react";
import Header from "@/components/header";
import Footer from "@/components/footer";
import ChatbotWidget from "@/components/chatbot-widget";
import Link from "next/link";
import { toast } from "sonner";
import { useTranslations } from "next-intl";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Calendar, Hash, Search, MapPin, FileDown, X } from "lucide-react";

export default function AccessDataPage() {
  const t = useTranslations("access_data");

  const [isExporting, setIsExporting] = useState(false);

  // Filter States
  const [format, setFormat] = useState("csv");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [locationsSelected, setLocationsSelected] = useState<string[]>([]);
  const [category, setCategory] = useState<string | undefined>(undefined);
  const [severity, setSeverity] = useState<string | undefined>(undefined);
  const [keyword, setKeyword] = useState("");
  const [amount, setAmount] = useState("100");
  const [chatOpen, setChatOpen] = useState(false);

  const handleExport = async (e?: React.FormEvent) => {
    if (e && typeof e.preventDefault === "function") e.preventDefault();
    try {
      setIsExporting(true);

      // Use env variable or fallback
      const baseUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

      const params = new URLSearchParams();
      params.append("format", format);

      if (amount) params.append("limit", amount);
      if (startDate)
        params.append("start_date", new Date(startDate).toISOString());
      if (endDate) params.append("end_date", new Date(endDate).toISOString());

      if (locationsSelected.length > 0)
        params.append("location", locationsSelected.join(","));
      if (category && category !== "all")
        params.append("disaster_type", category);
      if (keyword) params.append("keyword", keyword);

      const response = await fetch(
        `${baseUrl}/api/v1/events/export?${params.toString()}`,
        {
          method: "GET",
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Export failed");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;

      const extension =
        format === "excel" ? "xlsx" : format === "raw" ? "json" : format;
      const dateStr = new Date().toISOString().split("T")[0];
      a.download = `disaster_data_${dateStr}.${extension}`;

      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success(`Successfully exported data as ${format.toUpperCase()}`);
    } catch (error) {
      console.error("Export error:", error);
      toast.error(
        error instanceof Error ? error.message : "Failed to download data"
      );
    } finally {
      setIsExporting(false);
    }
  };

  const locations = [
    "Selangor",
    "Kuala Lumpur",
    "Johor",
    "Sabah",
    "Sarawak",
    "Penang",
    "Kedah",
    "Terengganu",
    "Pahang",
    "Melacca",
    "Kelantan",
    "Perak",
    "Negeri Sembilan",
    "Perlis",
  ];
  const category_of_disaster = ["Flood", "Landslide", "Storm", "Earthquake"];
  const severity_levels = ["Warning", "Infomational", "Urgent"];

  return (
    <main className="min-h-screen bg-background flex flex-col">
      <Header onFilterClick={() => {}} />
      <ChatbotWidget isOpen={chatOpen} onToggle={setChatOpen} />

      <div className="flex-1">
        <section className="relative overflow-hidden bg-gradient-to-br from-primary via-primary/90 text-primary-foreground py-16 md:py-20">
          {/* Animated gradient orbs */}
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute -top-1/2 -left-1/4 w-96 h-96 bg-primary-foreground/10 rounded-full blur-3xl animate-pulse" />
            <div className="absolute top-1/4 -right-1/4 w-[32rem] h-[32rem] bg-primary/20 rounded-full blur-3xl animate-pulse delay-1000" />
            <div className="absolute -bottom-1/3 left-1/3 w-80 h-80 bg-primary-foreground/5 rounded-full blur-3xl animate-pulse delay-500" />
          </div>

          {/* Animated grid pattern */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:32px_32px] [mask-image:radial-gradient(ellipse_at_center,black_20%,transparent_80%)]" />

          {/* Content */}
          <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="relative">
                <FileDown className="w-12 h-12 animate-bounce" />
                <div className="absolute inset-0 w-12 h-12 bg-primary-foreground/20 rounded-full blur-xl animate-pulse" />
              </div>
              <div className="h-px flex-1 bg-gradient-to-r from-primary-foreground/50 to-transparent" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4 text-balance drop-shadow-lg">
              {t("title")}
            </h1>
            <p className="text-lg text-primary-foreground/95 max-w-2xl drop-shadow-md">
              {t("desc")}
            </p>
          </div>
        </section>

        {/* Main Content */}
        <section className="py-12 md:py-16">
          <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
            <form onSubmit={handleExport} className="space-y-6">
              {/* Date Range Section */}
              <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-6">
                  <Calendar className="w-5 h-5 text-primary" />
                  <h2 className="text-xl font-semibold text-foreground">
                    {t("form")}
                  </h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="startDate" className="text-sm font-medium">
                      {t("startDate")}
                    </Label>
                    <Input
                      id="startDate"
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="h-11"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="endDate" className="text-sm font-medium">
                      {t("endDate")}
                    </Label>
                    <Input
                      id="endDate"
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="h-11"
                    />
                  </div>
                </div>
              </div>

              {/* Filter Section */}
              <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
                <h2 className="text-xl font-semibold text-foreground mb-6">
                  Choose what you want
                </h2>

                <div className="space-y-6">
                  {/* Amount */}
                  <div className="space-y-2">
                    <Label
                      htmlFor="amount"
                      className="text-sm font-medium flex items-center gap-2"
                    >
                      <Hash className="w-4 h-4 text-muted-foreground" />
                      Amount of data
                    </Label>
                    <Input
                      id="amount"
                      type="number"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      placeholder="Enter number of records"
                      className="h-11"
                    />
                  </div>

                  {/* Keyword */}
                  <div className="space-y-2">
                    <Label
                      htmlFor="keyword"
                      className="text-sm font-medium flex items-center gap-2"
                    >
                      <Search className="w-4 h-4 text-muted-foreground" />
                      Keyword
                    </Label>
                    <Input
                      id="keyword"
                      type="text"
                      value={keyword}
                      onChange={(e) => setKeyword(e.target.value)}
                      placeholder="Search by keyword..."
                      className="h-11"
                    />
                  </div>

                  {/* Disaster Type */}
                  <div className="space-y-2">
                    <Label
                      htmlFor="disaster-type"
                      className="text-sm font-medium"
                    >
                      Disaster Type
                    </Label>
                    <Select value={category} onValueChange={setCategory}>
                      <SelectTrigger id="disaster-type" className="h-11">
                        <SelectValue placeholder="All Types" />
                      </SelectTrigger>
                      <SelectContent>
                        {category_of_disaster.map((cat) => (
                          <SelectItem key={cat} value={cat.toLowerCase()}>
                            {cat}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Severity */}
                  <div className="space-y-2">
                    <Label htmlFor="severity" className="text-sm font-medium">
                      Severity
                    </Label>
                    <Select value={severity} onValueChange={setSeverity}>
                      <SelectTrigger id="severity" className="h-11">
                        <SelectValue placeholder="Select Severity" />
                      </SelectTrigger>
                      <SelectContent>
                        {severity_levels.map((level) => (
                          <SelectItem key={level} value={level}>
                            {level}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              {/* Location Section */}
              <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-primary" />
                    <h2 className="text-xl font-semibold text-foreground">
                      {t("seclocation")}
                    </h2>
                  </div>
                  {locationsSelected.length > 0 && (
                    <button
                      type="button"
                      onClick={() => setLocationsSelected([])}
                      className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1"
                    >
                      <X className="w-4 h-4" />
                      Clear all
                    </button>
                  )}
                </div>
                <p className="text-sm text-muted-foreground mb-4">
                  {t("locDesc")}
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {locations.map((loc) => (
                    <label
                      key={loc}
                      className="flex items-center gap-3 p-3 border border-border rounded-md cursor-pointer hover:bg-secondary/50 transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={locationsSelected.includes(loc)}
                        onChange={() =>
                          setLocationsSelected((prev) =>
                            prev.includes(loc)
                              ? prev.filter((l) => l !== loc)
                              : [...prev, loc]
                          )
                        }
                        className="w-4 h-4 accent-primary rounded"
                      />
                      <span className="text-sm text-foreground font-medium">
                        {loc}
                      </span>
                    </label>
                  ))}
                </div>
                {locationsSelected.length > 0 && (
                  <p className="mt-3 text-sm text-muted-foreground">
                    {locationsSelected.length} location
                    {locationsSelected.length !== 1 ? "s" : ""} selected
                  </p>
                )}
              </div>

              {/* Export Format Section */}
              <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-6">
                  <FileDown className="w-5 h-5 text-primary" />
                  <h2 className="text-xl font-semibold text-foreground">
                    {t("expFormat")} <span className="text-destructive">*</span>
                  </h2>
                </div>
                <div className="space-y-3">
                  {[
                    {
                      id: "csv",
                      label: t("csvFormat"),
                      description: t("csvDesc"),
                    },
                    {
                      id: "json",
                      label: t("jsonFormat"),
                      description: t("jsonDesc"),
                    },
                    {
                      id: "raw",
                      label: t("zipFormat"),
                      description: t("zipDesc"),
                    },
                  ].map((fmt) => (
                    <label
                      key={fmt.id}
                      className={`flex items-start gap-3 p-4 border-2 rounded-lg cursor-pointer transition-all ${
                        format === fmt.id
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/50 hover:bg-secondary/30"
                      }`}
                    >
                      <input
                        type="radio"
                        name="exportFormat"
                        value={fmt.id}
                        checked={format === fmt.id}
                        onChange={(e) => setFormat(e.target.value)}
                        className="w-4 h-4 mt-1 accent-primary"
                      />
                      <div className="flex-1">
                        <p className="font-semibold text-foreground mb-1">
                          {fmt.label}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {fmt.description}
                        </p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Submit Button */}
              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <button
                  type="submit"
                  disabled={isExporting}
                  className="flex-1 h-11 px-6 bg-primary text-primary-foreground font-semibold rounded-md hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isExporting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      Exporting...
                    </>
                  ) : (
                    <>
                      <FileDown className="w-4 h-4" />
                      {t("btnDownload")}
                    </>
                  )}
                </button>
                <Link
                  href="/"
                  className="h-11 px-6 border-2 border-border text-foreground font-semibold rounded-md hover:bg-secondary transition-colors flex items-center justify-center"
                >
                  {t("btnCancel")}
                </Link>
              </div>
            </form>

            {/* Info Box */}
            <div className="mt-12 bg-secondary/50 border border-border rounded-lg p-6">
              <h3 className="font-semibold text-foreground mb-3">
                {t("infoFormat")}
              </h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span>{t("info1")}</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span>{t("info2")}</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span>{t("info3")}</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span>{t("info4")}</span>
                </li>
              </ul>
            </div>
          </div>
        </section>
      </div>

      <Footer />
    </main>
  );
}
