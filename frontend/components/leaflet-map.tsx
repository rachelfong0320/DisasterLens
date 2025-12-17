"use client";

import dynamic from "next/dynamic";
import { Suspense, useState } from "react";
import DisasterFilterWidget, { FilterOptions } from "./disaster-filter-widget";
import { ChevronDown } from "lucide-react"; // If you have lucide-react, otherwise use text "▼"
import { Filter } from "lucide-react"; // Filter icon

const LeafletMapContent = dynamic(() => import("./leaflet-map-content"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-gray-100 flex items-center justify-center">
      <p className="text-gray-500">Loading map...</p>
    </div>
  ),
});

export default function LeafletMap() {
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
          <h2 className="text-3xl font-bold text-foreground">Disaster Map</h2>
          
         <button
            onClick={() => setIsFilterOpen(!isFilterOpen)}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg shadow-md border transition-all duration-300 ease-in-out
              ${isFilterOpen 
                ? "bg-blue-600 border-blue-600 text-white" // State when OPEN
                : "bg-white border-gray-200 text-gray-700 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-600" // State when CLOSED
              }
            `}
          >
            {/* Filter Icon */}
            <Filter className={`w-4 h-4 transition-colors duration-300 ${isFilterOpen ? "text-white" : "text-gray-500 group-hover:text-blue-600"}`} />
            
            <span className="font-semibold text-sm">Filters</span>
            
            {/* Chevron Icon - rotates and changes color */}
            <ChevronDown 
              className={`w-4 h-4 transition-all duration-300 ${
                isFilterOpen ? "rotate-180 text-white" : "rotate-0 text-gray-400 group-hover:text-blue-600"
              }`} 
            />
          </button>
        </div>

        <div className="space-y-3">
          {/* 2. Sliding Container Logic */}
          <div 
            className={`grid transition-all duration-500 ease-in-out ${
              isFilterOpen ? "grid-rows-[1fr] opacity-100 mb-4" : "grid-rows-[0fr] opacity-0 mb-0"
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
                  <p className="text-gray-500 font-medium">Loading map assets...</p>
                </div>
              }
            >
              <LeafletMapContent filters={filters} />
            </Suspense>
          </div>
        </div>
      </div>
    </section>
  );
}