"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// IMPORTANT: These imports are required for the cluster icons to look correct
import MarkerClusterGroup from "react-leaflet-cluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";

import { applyFilters } from "@/lib/filterUtils";
import type { FilterOptions } from "@/components/disaster-filter-widget";
import { DisasterEvent } from "@/lib/types/disaster";
import { useTranslations } from "next-intl";

// 1. Cluster Icon Generator (Moved outside to be globally accessible)
const createClusterCustomIcon = (cluster: any) => {
  const count = cluster.getChildCount();

  let size = "w-8 h-8";
  if (count >= 10) size = "w-10 h-10";
  if (count >= 50) size = "w-12 h-12";

  return L.divIcon({
    html: `
      <div class="flex items-center justify-center bg-red-600 border-2 border-white rounded-full shadow-lg text-white font-bold ${size}" style="width: 35px; height: 35px; display: flex; align-items: center; justify-content: center; border-radius: 50%;">
        ${count}
      </div>
    `,
    className: "custom-marker-cluster",
    iconSize: L.point(40, 40, true),
  });
};

// 2. Individual Marker Icon Generator
const getCustomIcon = () => {
  return L.divIcon({
    html: `
      <div style="
        width: 30px; 
        height: 30px; 
        background-color: #dc2626; /* Match your red cluster color */
        color: white; 
        border: 2px solid white; 
        border-radius: 50%; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        font-weight: bold;
        font-size: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
      ">
        1
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
  const t = useTranslations("map");
  const [events, setEvents] = useState<DisasterEvent[]>([]);
  const [loading, setLoading] = useState(false);

  const filteredMarkers = applyFilters(events, filters).filter((event) => {
    const type = event.classification_type?.toLowerCase();
    return type !== "none" && type !== "" && type !== null;
  });

  useEffect(() => {
    const fetchEvents = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (filters.disasterType)
          params.append("disaster_type", filters.disasterType);
        if (filters.state) params.append("state", filters.state);
        if (filters.startDate) params.append("start_date", filters.startDate);
        if (filters.endDate) params.append("end_date", filters.endDate);

        const response = await fetch(
          `http://localhost:8000/api/v1/events/filtered?${params.toString()}`
        );
        const data = await response.json();
        setEvents(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error("Error fetching events:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [filters]);

  return (
    <div className="relative w-full h-full">
      {loading && (
        <div className="absolute top-2 right-2 z-1000 bg-white px-2 py-1 rounded shadow text-xs font-bold">
          {t("update")}
        </div>
      )}

      <MapContainer center={[4.21, 101.69]} zoom={6} className="w-full h-full">
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

        <MarkerClusterGroup
          chunkedLoading
          spiderfyOnMaxZoom={true}
          iconCreateFunction={createClusterCustomIcon}
        >
          {filteredMarkers.map((event) => (
            <Marker
              key={event.event_id}
              position={[
                event.geometry.coordinates[1],
                event.geometry.coordinates[0],
              ]}
              icon={getCustomIcon()}
            >
              <Popup>
                <div className="text-sm">
                  {/* The 'S' or 'F' type is shown here now */}
                  <p className="font-bold uppercase text-red-600 mb-1">
                    {event.classification_type}
                  </p>
                  <p className="capitalize text-gray-700">
                    {event.location_district}, {event.location_state}
                  </p>
                  <p className="font-semibold text-blue-700 mt-1">
                    📅 {new Date(event.start_time).toLocaleDateString()}
                  </p>
                  <hr className="my-1" />
                  <p className="text-gray-500 text-xs">
                    {t("report")} {event.total_posts_count}
                  </p>
                </div>
              </Popup>
            </Marker>
          ))}
        </MarkerClusterGroup>

        <div className="absolute bottom-6 left-6 z-1000 bg-white/90 backdrop-blur-sm p-3 rounded-lg border border-gray-200 shadow-lg">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-red-600 rounded-full flex items-center justify-center text-[10px] text-white font-bold border border-white shadow-sm">
              #
            </div>
            <p className="text-xs text-gray-700 font-medium leading-tight">
              {t("number")} <br />
              <span className="text-red-700 font-bold text-sm">
                {t("incidents")}
              </span>{" "}
              {t("reported")}
            </p>
          </div>
        </div>
      </MapContainer>
    </div>
  );
}
