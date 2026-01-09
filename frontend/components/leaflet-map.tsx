"use client";

import dynamic from "next/dynamic";
import { Suspense, use, useState } from "react";
import DisasterFilterWidget, { FilterOptions } from "./disaster-filter-widget";
import { ChevronDown } from "lucide-react"; // If you have lucide-react, otherwise use text "▼"
import { Filter } from "lucide-react"; // Filter icon
import { useTranslations } from "next-intl";

const LeafletMapContent = dynamic(() => import("./leaflet-map-content"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-gray-100 flex items-center justify-center">
      <p className="text-gray-500">Loading map...</p>
    </div>
  ),
});

export default function LeafletMap({ chatbotEvent }: { chatbotEvent: string | null }) {
  const t = useTranslations("map");
  const h = useTranslations("home");
  const d = useTranslations("disasterType");
  const [filters, setFilters] = useState<FilterOptions>({
    disasterType: "",
    state: "",
    startDate: "2023-01-01",
    endDate: "2025-12-31",
  });
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  return (
    <section className="w-full px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-7xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-foreground">{h("map")}</h2>

          <button
            onClick={() => setIsFilterOpen(!isFilterOpen)}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg shadow-md border transition-all duration-300 ease-in-out
              ${
                isFilterOpen
                  ? "bg-primary text-white" // State when OPEN
                  : "flex w-fit items-center justify-between gap-3 rounded-xl border border-zinc-200 bg-white/50 px-4 py-2 text-sm font-medium transition-all outline-none hover:bg-zinc-50 focus:ring-2 focus:ring-zinc-950/10 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-800 dark:bg-zinc-950/50 dark:hover:bg-zinc-900" // State when CLOSED
              }
            `}
          >
            {/* Filter Icon */}
            <Filter
              className={`w-4 h-4 transition-colors duration-300 ${
                isFilterOpen
                  ? "text-white"
                  : "text-gray-500 group-hover:text-blue-600"
              }`}
            />

            <span className="font-semibold text-sm">{h("filter")}</span>

            {/* Chevron Icon - rotates and changes color */}
            <ChevronDown
              className={`w-4 h-4 transition-all duration-300 ${
                isFilterOpen
                  ? "rotate-180 text-white"
                  : "rotate-0 text-gray-400 group-hover:text-blue-600"
              }`}
            />
          </button>
        </div>

        <div className="space-y-3">
          {/* 2. Sliding Container Logic */}
          <div
            className={`grid transition-all duration-500 ease-in-out ${
              isFilterOpen
                ? "grid-rows-[1fr] opacity-100 mb-4"
                : "grid-rows-[0fr] opacity-0 mb-0"
            }`}
          >
            <div className="overflow-hidden">
              <div className="p-4 bg-card border border-border rounded-lg shadow-inner">
                <DisasterFilterWidget onFilterChange={setFilters} />
              </div>
            </div>
          </div>

          {/* Map Container */}
          <div className="rounded-lg overflow-hidden shadow-lg h-96 md:h-[600px] border border-border relative">
            {/* Loading Overlay */}
            <Suspense
              fallback={
                <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                  <p className="text-gray-500 font-medium">
                    Loading map assets...
                  </p>
                </div>
              }
            >
              <LeafletMapContent filters={filters} chatbotEvent={chatbotEvent} />
            </Suspense>
          </div>

          {/* Dynamic Filter Summary Ribbon */}
          <div className="bg-gray-50 border-l-4 border-blue-500 p-3 mb-4 rounded-r-lg shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="text-sm text-gray-700">
              <span className="font-medium">{t("view")}</span>

              {/* Disaster Type */}
              <span className="font-bold text-blue-600">
                {filters.disasterType ? d(filters.disasterType) : d("allTypes")}
              </span>

              <span> {t("in")} </span>

              {/* State */}
              <span className="font-bold text-gray-900">
                {filters.state || h("allStates")}
              </span>

              {/* Date Range */}
              <span className="text-gray-500 ml-1">
                {/* If date is empty, it shows a default string, otherwise shows the date */}
                {filters.startDate || "2023-01-01"}
                <span className="mx-1 text-gray-400">→</span>
                {filters.endDate || "2025-12-31"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
