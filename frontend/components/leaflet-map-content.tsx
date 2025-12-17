"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { applyFilters } from "@/lib/filterUtils";
import type { FilterOptions } from "@/components/disaster-filter-widget";
import { DisasterEvent } from "@/lib/types/disaster";

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
  const [events, setEvents] = useState<DisasterEvent[]>([]);
  const [loading, setLoading] = useState(false);

  const filteredMarkers = applyFilters(events, filters);

  useEffect(()=>{
    const fetchEvents = async () => {
      setLoading(true);
      try{
        //Construct the query parameters based on filters
        const params = new URLSearchParams();
        if(filters.disasterType) params.append('disasterType', filters.disasterType);
        if(filters.state) params.append('state', filters.state);
        if(filters.startDate) params.append('start_date', filters.startDate);
        if(filters.endDate) params.append('end_date', filters.endDate);

        const response = await fetch(`http://localhost:8000/api/v1/events/filtered?${params.toString()}`);
        const data = await response.json();
        console.log("filters applied:", filters);
          console.log("response data:", data);
        setEvents(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error("Error fetching events:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  },[filters]);



return (
    <div className="relative w-full h-full">
      {loading && (
        <div className="absolute top-2 right-2 z-[1000] bg-white px-2 py-1 rounded shadow text-xs">
          Updating Map...
        </div>
      )}
      
      <MapContainer center={[4.21, 101.69]} zoom={6} style={{ width: "100%", height: "100%" }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

        {Array.isArray(events) && events.map((event) => (
          <Marker
            key={event.event_id}
            // Note: Your backend returns 'geometry', adjust if it's GeoJSON or lat/lng
            position={[event.geometry.coordinates[1], event.geometry.coordinates[0]]}
            icon={getCustomIcon(event.classification_type)}
          >
            <Popup>
              <div className="p-2">
                <h3 className="font-bold uppercase text-red-600">{event.classification_type}</h3>
                <p className="text-sm">{event.location_district}, {event.location_state}</p>
                <p className="text-xs text-gray-500">Reports: {event.total_posts_count}</p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
