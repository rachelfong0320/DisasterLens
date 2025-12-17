"use client";

import type React from "react";
import { useState } from "react";
import Header from "@/components/header";
import Footer from "@/components/footer";
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

      <div className="flex-1">
        {/* Hero Section */}
        <section className="bg-gradient-to-r from-primary to-primary/80 text-primary-foreground py-12 md:py-16">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 text-balance">
              {t("title")}
            </h1>
            <p className="text-lg text-primary-foreground/90 max-w-2xl">
              {t("desc")}
            </p>
          </div>
        </section>

        {/* Main Content */}
        <section className="py-12 md:py-16">
          <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
            <form onSubmit={handleExport} className="space-y-8">
              {/* Date Range Section */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold text-foreground mb-4">
                  {t("form")}
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      {t("startDate")}
                    </label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full px-4 py-2 border border-border rounded-md bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      {t("endDate")}
                    </label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full px-4 py-2 border border-border rounded-md bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                </div>
              </div>

              <div className="bg-card border border-border rounded-lg p-6 space-y-6">
                <h2 className="text-xl font-semibold text-foreground mb-4">
                  Choose what you want
                </h2>

                {/* Amount */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Amount of data
                  </label>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full px-4 py-2 border border-border rounded-md bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                {/* Keyword */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Keyword
                  </label>
                  <input
                    type="text"
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    className="w-full px-4 py-2 border border-border rounded-md bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                {/* Disaster Type */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Disaster Type
                  </label>
                  <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger>
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
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Severity
                  </label>
                  <Select value={severity} onValueChange={setSeverity}>
                    <SelectTrigger>
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

              {/* Location Section */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold text-foreground mb-4">
                  {t("seclocation")}
                </h2>
                <p className="text-sm text-muted-foreground mb-4">
                  {t("locDesc")}
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {locations.map((loc) => (
                    <label
                      key={loc}
                      className="flex items-center gap-3 cursor-pointer"
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
                        className="w-5 h-5 accent-primary rounded"
                      />
                      <span className="text-foreground font-medium">{loc}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Export Format Section */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold text-foreground mb-4">
                  {t("expFormat")} <span className="text-red-500">*</span>
                </h2>
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
                      className="flex items-start gap-3 p-3 border border-border rounded-md cursor-pointer hover:bg-secondary/50 transition"
                    >
                      <input
                        type="radio"
                        name="exportFormat"
                        value={fmt.id}
                        checked={format === fmt.id}
                        onChange={(e) => setFormat(e.target.value)}
                        className="w-5 h-5 mt-0.5 accent-primary"
                      />
                      <div className="flex-1">
                        <p className="font-medium text-foreground">
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
              <div className="flex gap-4">
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-primary text-primary-foreground font-semibold rounded-md hover:opacity-90 transition"
                >
                  {t("btnDownload")}
                </button>
                <Link
                  href="/"
                  className="px-6 py-3 border border-border text-foreground font-semibold rounded-md hover:bg-secondary transition text-center"
                >
                  {t("btnCancel")}
                </Link>
              </div>
            </form>

            {/* Info Box */}
            <div className="mt-12 bg-secondary/50 border border-border rounded-lg p-6">
              <h3 className="font-semibold text-foreground mb-2">
                {t("infoFormat")}
              </h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>{t("info1")}</li>
                <li>{t("info2")}</li>
                <li>{t("info3")}</li>
                <li>{t("info4")}</li>
              </ul>
            </div>
          </div>
        </section>
      </div>

      <Footer />
    </main>
  );
}
