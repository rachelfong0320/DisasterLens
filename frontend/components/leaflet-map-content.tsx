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
import { AlertTriangle, CalendarX } from "lucide-react";

interface MarkerCluster {
  getChildCount(): number;
}

const DISASTER_COLORS: Record<string, string> = {
  flood: "#2563eb",       // Blue
  "forest fire": "#f97316", // Orange
  storm: "#f59e0b",       // Amber
  haze: "#71717a",        // Gray
  landslide: "#78350f",    // Brown
  earthquake: "#880e4f",   // Deep Burgundy (New choice to avoid Cluster Red)
  tsunami: "#0891b2",      // Cyan
  sinkhole: "#7c3aed",     // Violet
};

function MapController({ events }: { events: DisasterEvent[] }) {
  const map = useMap();

  useEffect(() => {
    // Filter out any events with invalid coordinates for calculation
    const validEvents = events.filter(e => 
      e.geometry?.coordinates && 
      e.geometry.coordinates.length === 2 &&
      e.geometry.coordinates[0] !== null
    );

    if (validEvents.length === 0) {
      map.flyTo([4.21, 101.69], 6, { duration: 1.5 });
      return;
    }

    if (validEvents.length === 1) {
      const event = validEvents[0];
      map.flyTo(
        [event.geometry.coordinates[1], event.geometry.coordinates[0]],
        12,
        { duration: 1.5 }
      );
    } else {
      const bounds = L.latLngBounds(
        validEvents.map((e) => [
          e.geometry.coordinates[1],
          e.geometry.coordinates[0],
        ] as L.LatLngExpression)
      );

      map.flyToBounds(bounds, {
        padding: [50, 50],
        duration: 1.5,
      });
    }
  }, [events, map]);

  return null;
}

// 1. Cluster Icon Generator (Moved outside to be globally accessible)
const createClusterCustomIcon = (cluster: MarkerCluster) => {
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
  const d = useTranslations("disasterType");
  const [events, setEvents] = useState<DisasterEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [highlightedEvent, setHighlightedEvent] = useState<DisasterEvent | null>(null);
  const [showLegend, setShowLegend] = useState(true);

  const isInvalidDateRange = useMemo(() => {
    if (!filters.startDate || !filters.endDate) return false;
    return new Date(filters.startDate) > new Date(filters.endDate);
  }, [filters.startDate, filters.endDate]);

const filteredMarkers = useMemo(() => {
  // If a chatbot event is active, show ONLY that marker
  if (chatbotEvent && events.length > 0) {
  return events;
  }

  // Otherwise, return to default filtered view
  return applyFilters(events, filters).filter((event) => {
    const type = event.classification_type?.toLowerCase();
    const district = event.location_district?.toLowerCase();
    const state = event.location_state?.toLowerCase();

    return (
      type !== "none" && type !== "" && type !== null &&
      district !== "unknown district" && district !== "" &&
      state !== "unknown state" && state !== ""
    );
  });
}, [events, filters, chatbotEvent]);

  const isMapEmpty = !loading && filteredMarkers.length === 0 && !isInvalidDateRange && !chatbotEvent;

  useEffect(() => {
  // If we are currently syncing with the chatbot, DON'T fetch global background events
  if (chatbotEvent) return; 

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.disasterType) params.append("disaster_type", filters.disasterType);
      if (filters.state) params.append("state", filters.state);
      if (filters.startDate) params.append("start_date", filters.startDate);
      if (filters.endDate) params.append("end_date", filters.endDate);
      const response = await fetch(`http://localhost:8000/api/v1/events/filtered?${params.toString()}`);
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
    setLoading(true);
    setSyncError(null);
    setEvents([]);
    setHighlightedEvent(null);

    // FIX: Extract all IDs if chatbotEvent is an array, otherwise wrap the single ID in an array
    const eventIds = Array.isArray(chatbotEvent) 
      ? chatbotEvent 
      : [chatbotEvent];

    console.log("📡 Sending Sync Request for IDs:", eventIds);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/map-sync`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        // The backend MapSyncRequest model expects "event_ids" as a list
        body: JSON.stringify({
          event_ids: eventIds, 
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail?.[0]?.msg || "Failed to sync map");
      }

      const data = await res.json();
      
      if (Array.isArray(data) && data.length > 0) {
        const validMapEvents = data.filter((event: any) => {
            const district = event.location_district?.toLowerCase();
            const state = event.location_state?.toLowerCase();
            const unknownTerms = ["unknown district", "unknown state", "unknown", ""];

            return !unknownTerms.includes(district) && !unknownTerms.includes(state);
        });

        if (validMapEvents.length > 0) {
            setEvents(validMapEvents); 
            setHighlightedEvent(validMapEvents[0]); 
        } else {
            setEvents([]);
            setSyncError("Found events, but they lack specific location data to display on the map.");
        }
      }else {
          setEvents([]);
          setSyncError("No matching events found in database.");
      }
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Failed to sync map");
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

      {/* 3. EMPTY: Success but zero results found */}
{isMapEmpty && !syncError && (
  <div className="absolute top-6 left-1/2 -translate-x-1/2 z-[1001] w-[90%] max-w-md animate-in fade-in slide-in-from-top-4 duration-300">
    <div className="bg-white/95 backdrop-blur-sm border border-amber-200 shadow-2xl rounded-2xl p-4 flex items-start gap-4 text-left">
      
      {/* Icon */}
      <div className="bg-amber-100 p-3 rounded-full shrink-0">
        <AlertTriangle className="w-6 h-6 text-amber-600" />
      </div>
      
      {/* Content Column */}
      <div className="flex-1 flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-gray-900">
            {/* FORMATTING FIX: forestFire -> Forest Fire */}
            No {filters.disasterType 
              ? filters.disasterType.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()) 
              : "Events"} Found
          </h3>
          <button 
            onClick={() => window.location.reload()} 
            className="text-[10px] uppercase tracking-wider font-black text-amber-700 hover:text-amber-800 underline shrink-0"
          >
            Clear
          </button>
        </div>

        <p className="text-xs text-gray-500 leading-relaxed">
          There are no reports for this category in 
          <span className="font-semibold text-gray-700"> 
            {/* FORMATTING FIX: pahang -> Pahang */}
            {filters.state 
              ? filters.state.charAt(0).toUpperCase() + filters.state.slice(1) 
              : "all states"}
          </span>.
        </p>

        {/* CONDITIONAL QUICK TIP: Only shows if start and end dates match */}
        {filters.startDate !== "" && filters.startDate === filters.endDate && (
          <div className="mt-2">
            <p className="text-[10px] uppercase font-black text-amber-800 mb-0.5">Quick Tip:</p>
            <p className="text-[11px] text-amber-700 font-bold leading-tight italic">
              "You're searching a single day. Try expanding your date range to see more results."
            </p>
          </div>
        )}
      </div>
    </div>
  </div>
)}
      <MapContainer center={[4.21, 101.69]} zoom={6} className="w-full h-full">
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

        <MapController events={filteredMarkers} />

        <MarkerClusterGroup
          chunkedLoading
          spiderfyOnMaxZoom={true}
          iconCreateFunction={createClusterCustomIcon}
        >
          {filteredMarkers.map((event) => {
            // ADD THIS SAFETY CHECK:
            const coords = event.geometry?.coordinates;
            const isValid = coords && 
                            coords.length === 2 && 
                            coords[0] !== null && 
                            coords[1] !== null;

            if (!isValid) return null;

            return (
              <Marker
                key={event.event_id}
                position={[
                  event.geometry.coordinates[1], // Latitude
                  event.geometry.coordinates[0], // Longitude
                ]}
                icon={getCustomIcon(event.classification_type)}
              >
              <Popup>
                <div className="text-sm">
                  <p className="font-bold uppercase text-red-600 mb-1">
                    {event.classification_type && event.classification_type.toLowerCase() !== "none" 
                      ? d(event.classification_type.toLowerCase().replace(/\s+(.)/g, (_, char) => char.toUpperCase()))
                      : "EVENT" // Replace t("unknownEvent") with a simple string
                    }
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
          );
          })}
        </MarkerClusterGroup>

        {/* Main Positioning Container - bottom-2 makes it sit very close to the map edge */}
<div className="absolute bottom-2 left-6 z-1000 flex flex-col items-start gap-1">
  
  {/* Toggle Button with Hover Effects */}
  <button 
    onClick={() => setShowLegend(!showLegend)}
    className="bg-white/95 backdrop-blur-md px-4 py-2 rounded-full border border-zinc-200 shadow-lg 
               flex items-center gap-2 group transition-all duration-200
               hover:bg-zinc-100 hover:border-zinc-300 hover:shadow-xl active:scale-95 cursor-pointer"
  >
    {/* Status Indicator Dot */}
    <div className={`w-2 h-2 rounded-full bg-red-600 ${showLegend ? 'animate-pulse' : ''} 
                    group-hover:scale-110 transition-transform`} />
    
    <span className="text-[12px] font-bold text-zinc-700 group-hover:text-zinc-900 transition-colors">
      {showLegend ? t("hideLegend") : t("showLegend")}
    </span>
  </button>

  {/* Smooth Transition Bar */}
  <div className={`
    bg-white/95 backdrop-blur-md rounded-xl border border-zinc-200 shadow-2xl 
    transition-all duration-500 ease-in-out origin-top-left overflow-hidden
    ${showLegend 
      ? "w-[calc(100vw-3rem)] md:w-auto max-h-[200px] opacity-100 scale-100 py-1.5 px-2 mt-0.5" 
      : "w-0 max-h-0 opacity-0 scale-95 p-0 mt-0 border-none"}
  `}>
    {/* Add 'overflow-x-auto' and 'no-scrollbar' to allow horizontal sliding on mobile */}
    <div className="flex flex-row items-center gap-4 px-1 whitespace-nowrap overflow-x-auto no-scrollbar">
      
      {/* SECTION 1: Incident Summary */}
      <div className="flex items-center gap-2.5 pr-4 border-r border-zinc-200 shrink-0">
        <div className="w-7 h-7 bg-red-600 rounded-lg flex items-center justify-center text-[12px] text-white font-black border border-white/20 shadow-sm">
          #
        </div>
        <div className="flex flex-col">
          <span className="text-[9px] text-zinc-400 font-bold uppercase tracking-tight leading-none">
            {t("number")}
          </span>
          <span className="text-[12px] text-red-600 font-black leading-tight">
            {t("incidents")}
          </span>
        </div>
      </div>

      {/* SECTION 2: Disaster Type Keys - Shrinkable labels for tablet */}
      <div className="flex flex-row items-center gap-3 md:gap-4">
        {Object.entries(DISASTER_COLORS).map(([type, color]) => {
          // Convert "forest fire" to "forestFire" to match your JSON keys
          const translationKey = type.replace(/\s+(.)/g, (_, char) => char.toUpperCase());

          return (
            <div key={type} className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full border-2 border-white shadow-sm ring-1 ring-zinc-100 shrink-0" 
                style={{ backgroundColor: color }}
              />
              <span className="text-[11px] font-bold text-zinc-600">
                {/* Use d hook for types */}
                {d(translationKey)} 
              </span>
            </div>
          );
        })}
      </div>

      {/* SECTION 3: Cluster Explanation */}
      <div className="flex items-center gap-2.5 border-l border-zinc-200 pl-4 pr-1 shrink-0">
        <div className="flex -space-x-1.5">
          <div className="w-4 h-4 bg-red-600 rounded-full border-2 border-white z-10 shadow-sm" />
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] font-bold text-zinc-800 leading-none">
            {t("cluster")}
          </span>
          <span className="text-[8px] text-zinc-400 font-medium italic">
            {t("zoomToExpand")}
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
