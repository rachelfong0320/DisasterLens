export type DisasterType =
  | "flood"
  | "landslide"
  | "forest_fire"
  | "storm"
  | "haze"
  | "sinkhole"
  | "earthquake"
  | "tsunami";

export interface DisasterMarker {
    event_id: string;
    disaster_type: DisasterType;
    location_id: string;        
    location_name: string;      
    city: string;               
    state: string;              
    latitude: number;
    longitude: number;
    start_time: string;
    end_time?: string;
    source?: string;
}

export const mockDisasterMarkers: DisasterMarker[] = [
  {
    event_id: "evt-001",
    disaster_type: "flood",
    location_id: "kuala terengganu",
    location_name: "Bukit Terengganu",
    city: "kuala terengganu, terengganu, malaysia",
    state: "Terengganu",
    latitude: 5.330,
    longitude: 103.140,
    start_time: "2025-11-15T20:00:00Z",
    end_time: "2025-11-18T08:00:00Z",
  },
  {
    event_id: "evt-002",
    disaster_type: "flood",
    location_id: "johor bahru",
    location_name: "Johor Bahru",
    city: "johor bahru, johor, malaysia",
    state: "Johor",
    latitude: 1.4927,
    longitude: 103.7414,
    start_time: "2025-11-17T02:30:00Z",
  },
  {
    event_id: "evt-003",
    disaster_type: "landslide",
    location_id: "ranau",
    location_name: "Ranau",
    city: "ranau, sabah, malaysia",
    state: "Sabah",
    latitude: 5.980,
    longitude: 117.530,
    start_time: "2025-11-12T11:00:00Z",
    end_time: "2025-11-15T16:00:00Z",
  },
  {
    event_id: "evt-004",
    disaster_type: "haze",
    location_id: "kuching",
    location_name: "Kuching",
    city: "kuching, sarawak, malaysia",
    state: "Sarawak",
    latitude: 1.5533,
    longitude: 110.3592,
    start_time: "2025-11-10T00:00:00Z",
    end_time: "2025-11-18T00:00:00Z",
  },
  {
    event_id: "evt-005",
    disaster_type: "forest_fire",
    location_id: "seberang perai",
    location_name: "Seberang Perai",
    city: "seberang perai, penang, malaysia",
    state: "Penang",
    latitude: 5.4164,
    longitude: 100.3327,
    start_time: "2025-11-18T06:00:00Z",
  },
  {
    event_id: "evt-006",
    disaster_type: "storm",
    location_id: "kota kinabalu",
    location_name: "Kota Kinabalu",
    city: "kota kinabalu, sabah, malaysia",
    state: "Sabah",
    latitude: 5.9804,
    longitude: 116.0735,
    start_time: "2025-11-14T09:00:00Z",
  },
  {
    event_id: "evt-007",
    disaster_type: "earthquake",
    location_id: "offshore sumatra",
    location_name: "Offshore Sumatra",
    city: "offshore, sumatra, indonesia",
    state: "Penang",
    latitude: -0.950,
    longitude: 100.350,
    start_time: "2025-11-05T03:45:00Z",
  },
  {
    event_id: "evt-008",
    disaster_type: "tsunami",
    location_id: "george town",
    location_name: "George Town",
    city: "george town, penang, malaysia",
    state: "Penang",
    latitude: 4.000,
    longitude: 100.500,
    start_time: "2025-11-05T04:10:00Z",
  },
  {
    event_id: "evt-009",
    disaster_type: "sinkhole",
    location_id: "kuala lumpur",
    location_name: "Kuala Lumpur",
    city: "kuala lumpur, malaysia",
    state: "Kuala Lumpur",
    latitude: 3.1390,
    longitude: 101.6869,
    start_time: "2025-10-30T18:20:00Z",
  },
  {
    event_id: "evt-010",
    disaster_type: "storm",
    location_id: "melaka",
    location_name: "Melaka",
    city: "melaka, melaka, malaysia",
    state: "Melaka",
    latitude: 2.1896,
    longitude: 102.2501,
    start_time: "2025-11-01T15:00:00Z",
  },
  {
    event_id: "evt-011",
    disaster_type: "haze",
    location_id: "langkawi",
    location_name: "Langkawi",
    city: "langkawi, kedah, malaysia",
    state: "Kedah",
    latitude: 6.3496,
    longitude: 99.8375,
    start_time: "2025-11-08T06:00:00Z",
    end_time: "2025-11-12T20:00:00Z",
  },
  {
    event_id: "evt-012",
    disaster_type: "forest_fire",
    location_id: "sandakan",
    location_name: "Sandakan",
    city: "sandakan, sabah, malaysia",
    state: "Sabah",
    latitude: 5.8400,
    longitude: 118.1160,
    start_time: "2025-11-02T07:00:00Z",
  },
];


