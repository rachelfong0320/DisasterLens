// disaster.ts

export interface Geometry {
  type: "Point";
  coordinates: [number, number]; // [longitude, latitude]
}

export interface DisasterEvent {
  event_id: string;
  classification_type: string;
  location_district: string;
  location_state: string;
  start_time: string;
  most_recent_report: string;
  geometry: Geometry;
  total_posts_count: number;
  related_post_ids: string[];
}

export interface FilterOptions {
  disasterType: string;
  state: string;
  startDate: string;
  endDate: string;
}