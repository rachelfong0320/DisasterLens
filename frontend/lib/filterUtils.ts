import { mockDisasterMarkers, DisasterMarker } from "@/data/mockDisasters";
import type { FilterOptions } from "@/components/disaster-filter-widget";

export function applyFilters(filters: FilterOptions): DisasterMarker[] {
  return mockDisasterMarkers.filter((marker) => {
    // Filter by disaster type
    if (filters.disasterType && marker.disaster_type !== filters.disasterType) {
      return false;
    }

    // Filter by state
    if (filters.state && marker.state !== filters.state) {
      return false;
    }

    // Filter by date range
    const markerStart = new Date(marker.start_time);
    const markerEnd = marker.end_time ? new Date(marker.end_time) : markerStart;

    if (filters.startDate) {
      const filterStart = new Date(filters.startDate + "T00:00:00Z");
      if (markerEnd < filterStart) return false;
    }

    if (filters.endDate) {
      const filterEnd = new Date(filters.endDate + "T23:59:59Z");
      if (markerStart > filterEnd) return false;
    }

    return true;
  });
}
