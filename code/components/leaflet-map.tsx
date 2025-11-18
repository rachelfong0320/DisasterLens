"use client";

import dynamic from "next/dynamic";
import { Suspense } from "react";

const LeafletMapContent = dynamic(() => import("./leaflet-map-content"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-gray-100 flex items-center justify-center">
      <p className="text-gray-500">Loading map...</p>
    </div>
  ),
});

export default function LeafletMap() {
  return (
    <section className="w-full px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-2xl font-bold text-foreground mb-4">
          Disaster Map
        </h2>
        <div className="rounded-lg overflow-hidden shadow-lg h-96 md:h-[500px] border border-border">
          <Suspense
            fallback={
              <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                <p className="text-gray-500">Loading map...</p>
              </div>
            }
          >
            <LeafletMapContent />
          </Suspense>
        </div>
      </div>
    </section>
  );
}
