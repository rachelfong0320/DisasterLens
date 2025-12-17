"use client";

import dynamic from "next/dynamic";
import { Suspense, useState } from "react";
import DisasterFilterWidget, { FilterOptions } from "./disaster-filter-widget";

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
    startDate: "",
    endDate: "",
  });

  return (
    <section className="w-full px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-7xl mx-auto space-y-4">
        <h2 className="text-3xl font-bold text-foreground">Disaster Map</h2>

        {/* Container with Filter Above Map */}
        <div className="space-y-3">
          {/* Filter Widget - Above the map */}
          <DisasterFilterWidget onFilterChange={setFilters} />

          {/* Map Container */}
          <div className="rounded-lg overflow-hidden shadow-lg h-96 md:h-[500px] border border-border">
            <Suspense
              fallback={
                <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                  <p className="text-gray-500">Loading map...</p>
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
