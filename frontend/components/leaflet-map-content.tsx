"use client";

import { useEffect, useState , useMemo} from "react";
import { MapContainer, TileLayer, Marker, Popup , useMap} from "react-leaflet";
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
import { AlertTriangle, X, CalendarX } from "lucide-react";

const DISASTER_COLORS: Record<string, string> = {
  flood: "#2563eb",
  "forest fire": "#f97316",
  storm: "#f59e0b",
  haze: "#71717a",
  sinkhole: "#7c3aed",
  earthquake: "#92400e",
  tsunami: "#0891b2",
};

function MapController({ event }: { event: DisasterEvent | null }) {
  const map = useMap(); //

  useEffect(() => {
    if (event) {
      map.flyTo(
        [event.geometry.coordinates[1], event.geometry.coordinates[0]],
        12,
        { duration: 1.5 }
      );
    }
  }, [event, map]);

  return null;
}

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
const getCustomIcon = (disasterType: string) => {
  // Normalize type and get color, fallback to black if type is unknown
  const typeKey = disasterType?.toLowerCase() || "";
  const markerColor = DISASTER_COLORS[typeKey] || "#000000";

  return L.divIcon({
    html: `
      <div style="
        width: 30px; 
        height: 30px; 
        background-color: ${markerColor}; 
        color: white; 
        border: 2px solid white; 
        border-radius: 50%; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        font-weight: bold;
        font-size: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.4);
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

// const getCustomIcon = () => {
//   return L.divIcon({
//     html: `
//       <div style="
//         width: 30px; 
//         height: 30px; 
//         background-color: #dc2626; /* Match your red cluster color */
//         color: white; 
//         border: 2px solid white; 
//         border-radius: 50%; 
//         display: flex; 
//         align-items: center; 
//         justify-content: center; 
//         font-weight: bold;
//         font-size: 12px;
//         box-shadow: 0 2px 5px rgba(0,0,0,0.3);
//       ">
//         1
//       </div>
//     `,
//     className: "custom-icon",
//     iconSize: [30, 30],
//     iconAnchor: [15, 15],
//     popupAnchor: [0, -15],
//   });
// };

interface LeafletMapContentProps {
  filters?: FilterOptions;
  chatbotEvent: string | null;
}

export default function LeafletMapContent({
  filters = {
    disasterType: "",
    state: "",
    startDate: "",
    endDate: "",
  },
  chatbotEvent
}: LeafletMapContentProps) {
  const t = useTranslations("map");
  const [events, setEvents] = useState<DisasterEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [highlightedEvent, setHighlightedEvent] = useState<DisasterEvent | null>(null);
  const [showLegend, setShowLegend] = useState(true);

  const isInvalidDateRange = useMemo(() => {
    if (!filters.startDate || !filters.endDate) return false;
    return new Date(filters.startDate) > new Date(filters.endDate);
  }, [filters.startDate, filters.endDate]);

  const filteredMarkers = applyFilters(events, filters).filter((event) => {
    const type = event.classification_type?.toLowerCase();
    return type !== "none" && type !== "" && type !== null;
  });

  const isMapEmpty = !loading && filteredMarkers.length === 0 && !isInvalidDateRange;

  useEffect(() => {
    if (chatbotEvent) return;
    const fetchEvents = async () => {
      setLoading(true);
      console.log("🔍 Fetching events with filters:", filters);
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
  }, [filters, chatbotEvent]);

  useEffect(() => {
    if (!chatbotEvent) return;

    const syncMap = async () => {
      if (!chatbotEvent) return;
      setLoading(true);
      setSyncError(null);
      setEvents([]);
      setHighlightedEvent(null);

      console.log("📡 Sending Sync Request for ID:", chatbotEvent);

      try {
        const res = await fetch(`http://localhost:8000/api/v1/map-sync`, {
          method: "POST", // Must be POST
          headers: {
            "Content-Type": "application/json",
          },
          // This body structure MUST match your MapSyncRequest model
          body: JSON.stringify({
            event_ids: [chatbotEvent], // Sending the ID as a single-item array
          }),
        });

        if (!res.ok) {
          // If status is 422, this will log exactly why the data was rejected
          const errorData = await res.json();
          console.error("❌ Server Error:", errorData);
          throw new Error(errorData.detail?.[0]?.msg || "Failed to sync map");
        }

        const data = await res.json();
        console.log("✅ Map Sync Data Received:", data);

        // Update markers and trigger the 'flyTo' animation
        if (Array.isArray(data) && data.length > 0) {
          setEvents(data); 
          setHighlightedEvent(data[0]); 
        } else {
          setEvents([]);
          setSyncError("No matching events found in database.");
        }
      } catch (err: any) {
        console.error("🔥 Sync Error:", err.message);
        setSyncError(err.message);
      } finally {
        setLoading(false);
      }
    };

    syncMap();
  }, [chatbotEvent]);

  return (
    <div className="relative w-full h-full">
      {loading && (
        <div className="absolute top-2 right-2 z-1000 bg-white px-2 py-1 rounded shadow text-xs font-bold">
          {t("update")}
        </div>
      )}

      {isInvalidDateRange && (
      <div className="absolute top-6 left-1/2 -translate-x-1/2 z-1001 w-[90%] max-w-md animate-in fade-in slide-in-from-top-4 duration-300">
        <div className="bg-red-50 border border-red-200 shadow-2xl rounded-2xl p-4 flex items-center gap-4">
          <div className="bg-red-100 p-3 rounded-full text-red-600">
            <CalendarX className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-bold text-red-900">Invalid Date Range</h3>
            <p className="text-xs text-red-700 leading-relaxed">
              The <b>Start Date</b> cannot be later than the <b>End Date</b>. Please check your filter settings.
            </p>
          </div>
        </div>
      </div>
      )}

      {isMapEmpty && !syncError && (
        <div className="absolute top-6 left-1/2 -translate-x-1/2 z-1001 w-[90%] max-w-md animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="bg-white/95 backdrop-blur-sm border border-amber-200 shadow-2xl rounded-2xl p-4 flex items-center gap-4">
            <div className="bg-amber-100 p-3 rounded-full">
              <AlertTriangle className="w-6 h-6 text-amber-600" />
            </div>
            
            <div className="flex-1">
              <h3 className="text-sm font-bold text-gray-900">
                No {filters.disasterType || "Events"} Found
              </h3>
              <p className="text-xs text-gray-500 leading-relaxed">
                There are no reports for this category in 
                <span className="font-semibold text-gray-700"> {filters.state || "all states"}</span>.
              </p>
            </div>
            
            {/* Optional: Add a button to reset to "All" */}
            <button 
              onClick={() => window.location.reload()} 
              className="text-xs font-bold text-amber-700 hover:underline"
            >
              Clear
            </button>
          </div>
        </div>
      )}

      <MapContainer center={[4.21, 101.69]} zoom={6} className="w-full h-full">
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

        <MapController event={highlightedEvent} />

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
              icon={getCustomIcon(event.classification_type)}
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

        <div className="absolute bottom-1 left-6 z-1000 flex flex-col items-start gap-2">
          {/* Modern Toggle Button */}
          <button 
            onClick={() => setShowLegend(!showLegend)}
            className="bg-white/95 backdrop-blur-md px-4 py-2 rounded-full border border-zinc-200 shadow-lg hover:bg-zinc-50 transition-all flex items-center gap-2 group active:scale-95"
          >
            <div className={`w-2 h-2 rounded-full bg-red-600 ${showLegend ? 'animate-pulse' : ''}`} />
            <span className="text-[12px] font-bold text-zinc-700">
              {showLegend ? "Hide Legend" : "Show Legend"} 
            </span>
          </button>

          {/* Smooth Transition Legend Bar */}
          <div className={`
            bg-white/95 backdrop-blur-md rounded-2xl border border-zinc-200 shadow-2xl 
            transition-all duration-500 ease-in-out origin-left overflow-hidden
            ${showLegend ? "max-w-[95vw] opacity-100 scale-100 p-1.5" : "max-w-0 opacity-0 scale-95 p-0 border-none"}
          `}>
            <div className="flex flex-row items-center gap-6 px-2 py-1 whitespace-nowrap">
              
              {/* SECTION 1: Incident Summary (Total Incidents Box) */}
              <div className="flex items-center gap-3 pr-6 border-r border-zinc-200 shrink-0">
                <div className="w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center text-[14px] text-white font-black border border-white/20 shadow-sm shrink-0">
                  #
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-tight leading-none">
                    Indicator
                  </span>
                  <span className="text-[13px] text-red-600 font-black leading-tight">
                    Incidents
                  </span>
                </div>
              </div>

              {/* SECTION 2: Disaster Type Keys (Clean Spacing) */}
              <div className="flex flex-row items-center gap-6">
                {Object.entries(DISASTER_COLORS).map(([type, color]) => (
                  <div key={type} className="flex items-center gap-2.5">
                    <div 
                      className="w-3.5 h-3.5 rounded-full border-2 border-white shadow-sm ring-1 ring-zinc-100 shrink-0" 
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-[12px] capitalize font-bold text-zinc-600">
                      {type}
                    </span>
                  </div>
                ))}
              </div>

              {/* SECTION 3: Cluster Explanation (Visual Groups) */}
              <div className="flex items-center gap-3 border-l border-zinc-200 pl-6 pr-2 shrink-0">
                <div className="flex -space-x-2">
                  <div className="w-5 h-5 bg-red-600 rounded-full border-2 border-white z-10 shadow-sm" />
                </div>
                <div className="flex flex-col">
                  <span className="text-[11px] font-bold text-zinc-800 leading-none">
                    Cluster Group
                  </span>
                  <span className="text-[9px] text-zinc-400 font-medium italic">
                    Zoom to expand
                  </span>
                </div>
              </div>

            </div>
          </div>
        </div>
      </MapContainer>
    </div>
  );
}
