import LeafletMap from "./leaflet-map";

export default function MapSection({ chatbotEvent }: { chatbotEvent: string | null }) {
  console.log("MapSection received chatbotEvent:", chatbotEvent);
  return <LeafletMap chatbotEvent={chatbotEvent} />; // Pass down renamed prop
}