"use client";

import { useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { mockDisasterMarkers } from "@/data/mockDisasters";
import { applyFilters } from "@/lib/filterUtils";
import type { FilterOptions } from "@/components/disaster-filter-widget";

// Create custom icons for different disaster types
const getCustomIcon = (type: string, severity?: string) => {
  const severityColors: Record<string, string> = {
    high: "#dc2626",
    medium: "#f97316",
    low: "#3b82f6",
  };

  const color = severityColors[severity || "low"] || "#3b82f6";

  return L.divIcon({
    html: `
      <div style="
        background-color: ${color};
        width: 30px;
        height: 30px;
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <span style="color: white; font-weight: bold; font-size: 12px;">
          ${type[0].toUpperCase()}
        </span>
      </div>
    `,
    className: "custom-icon",
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
  });
};

interface LeafletMapContentProps {
  filters?: FilterOptions;
}

export default function LeafletMapContent({
  filters = {
    disasterType: "",
    state: "",
    startDate: "",
    endDate: "",
  },
}: LeafletMapContentProps) {
  const filteredMarkers = applyFilters(filters);

  return (
    <MapContainer
      center={[4.21, 101.69]}
      zoom={6}
      style={{ width: "100%", height: "100%" }}
    >
      {/* OpenStreetMap tiles */}
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {/* Disaster markers */}
      {filteredMarkers.map((marker) => (
        <Marker
          key={marker.event_id}
          position={[marker.latitude, marker.longitude]}
          icon={getCustomIcon(marker.disaster_type)}
        >
          <Popup>
            <div className="p-2 max-w-xs">
              <h3 className="font-semibold text-sm">
                {marker.location_name || marker.location_id}
              </h3>
              <p className="text-xs text-gray-600 capitalize">
                Type: {marker.disaster_type.replace("_", " ")}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(marker.start_time).toLocaleDateString()}
              </p>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* No results message */}
      {filteredMarkers.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="bg-white/90 px-4 py-2 rounded-lg shadow">
            <p className="text-sm text-gray-600">
              No disasters found matching filters
            </p>
          </div>
        </div>
      )}
    </MapContainer>
  );
}
