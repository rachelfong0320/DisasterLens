// src/lib/filterUtils.ts
import { DisasterEvent, FilterOptions } from "@/lib/types/disaster";

export function applyFilters(events: DisasterEvent[], filters: FilterOptions): DisasterEvent[] {
  if (!events || !Array.isArray(events)) return [];

  return events.filter((event) => {
    // 1. Type Filter: If filter is empty, let everything through
    if (filters.disasterType && event.classification_type !== filters.disasterType) {
      return false;
    }

    // 2. State
    if (filters.state && event.location_state.toLowerCase() !== filters.state.toLowerCase()) {
      return false;
    }

    // 3. Date Filter: Ensure the event falls BETWEEN start and end
    const eventDate = new Date(event.start_time);
    if (filters.startDate && eventDate < new Date(filters.startDate)) return false;
    if (filters.endDate) {
      const end = new Date(filters.endDate);
      end.setHours(23, 59, 59);
      if (eventDate > end) return false;
    }

    return true;
  });
}