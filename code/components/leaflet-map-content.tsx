"use client";

import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

interface DisasterMarker {
  id: string;
  type: "flood" | "landslide" | "fire" | "storm" | "haze";
  location: string;
  severity: "low" | "medium" | "high";
  latitude: number;
  longitude: number;
  description?: string;
}

const DISASTER_MARKERS: DisasterMarker[] = [
  {
    id: "1",
    type: "flood",
    location: "Terengganu",
    severity: "high",
    latitude: 5.31,
    longitude: 103.32,
    description: "Severe flooding reported",
  },
  {
    id: "2",
    type: "flood",
    location: "Johor",
    severity: "medium",
    latitude: 1.48,
    longitude: 103.74,
    description: "Moderate water levels",
  },
  {
    id: "3",
    type: "landslide",
    location: "Sabah",
    severity: "high",
    latitude: 5.98,
    longitude: 117.53,
    description: "Major landslide risk",
  },
  {
    id: "4",
    type: "haze",
    location: "Sarawak",
    severity: "medium",
    latitude: 1.55,
    longitude: 110.34,
    description: "Air quality deteriorating",
  },
  {
    id: "5",
    type: "fire",
    location: "Penang",
    severity: "low",
    latitude: 5.41,
    longitude: 100.33,
    description: "Minor fire incidents",
  },
];

// Create custom icons for different disaster types
const getCustomIcon = (type: string, severity: string) => {
  const severityColors: Record<string, string> = {
    high: "#dc2626",
    medium: "#f97316",
    low: "#3b82f6",
  };

  const color = severityColors[severity] || "#3b82f6";

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

export default function LeafletMapContent() {
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
      {DISASTER_MARKERS.map((marker) => (
        <Marker
          key={marker.id}
          position={[marker.latitude, marker.longitude]}
          icon={getCustomIcon(marker.type, marker.severity)}
        >
          <Popup>
            <div className="p-2">
              <h3 className="font-semibold text-sm">{marker.location}</h3>
              <p className="text-xs text-gray-600 capitalize">
                Type: {marker.type}
              </p>
              <p className="text-xs text-gray-600 capitalize">
                Severity: {marker.severity}
              </p>
              {marker.description && (
                <p className="text-xs text-gray-600 mt-1">
                  {marker.description}
                </p>
              )}
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
