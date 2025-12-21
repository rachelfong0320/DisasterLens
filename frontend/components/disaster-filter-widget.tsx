"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { X } from "lucide-react";
import { useTranslations } from "next-intl";

export type DisasterType =
  | "flood"
  | "landslide"
  | "forestFire"
  | "storm"
  | "haze"
  | "sinkhole"
  | "earthquake"
  | "tsunami"
  | "";

export const DISASTER_TYPES: DisasterType[] = [
  "",
  "flood",
  "landslide",
  "forestFire",
  "storm",
  "haze",
  "sinkhole",
  "earthquake",
  "tsunami",
];

export const MALAYSIAN_STATES = [
  "All States",
  "Johor",
  "Kedah",
  "Kelantan",
  "Kuala Lumpur",
  "Labuan",
  "Melaka",
  "Negeri Sembilan",
  "Pahang",
  "Penang",
  "Perak",
  "Perlis",
  "Putrajaya",
  "Sabah",
  "Sarawak",
  "Selangor",
  "Terengganu",
];

export interface FilterOptions {
  disasterType: DisasterType;
  state: string;
  startDate: string;
  endDate: string;
}

interface DisasterFilterWidgetProps {
  onFilterChange: (filters: FilterOptions) => void;
}

export default function DisasterFilterWidget({
  onFilterChange,
}: DisasterFilterWidgetProps) {
  const t = useTranslations("home");
  const r = useTranslations("access_data");
  const d = useTranslations("disasterType");
  const [filters, setFilters] = useState<FilterOptions>({
    disasterType: "",
    state: "",
    startDate: "",
    endDate: "",
  });

  const handleDisasterTypeChange = (value: string) => {
    // If user selects "All Types", we set it to empty string ""
    const finalValue = value === "All Types" ? "" : (value as DisasterType);
    const updated = { ...filters, disasterType: finalValue };
    setFilters(updated);
    onFilterChange(updated);
  };

  const handleStateChange = (value: string) => {
    // If user selects "All States", we set it to empty string ""
    const finalValue = value === "All States" ? "" : value;
    const updated = { ...filters, state: finalValue };
    setFilters(updated);
    onFilterChange(updated);
  };

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const updated = { ...filters, startDate: e.target.value };
    setFilters(updated);
    onFilterChange(updated);
  };

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const updated = { ...filters, endDate: e.target.value };
    setFilters(updated);
    onFilterChange(updated);
  };

  const handleReset = () => {
    const reset: FilterOptions = {
      disasterType: "",
      state: "",
      startDate: "",
      endDate: "",
    };
    setFilters(reset);
    onFilterChange(reset);
  };

  const hasActiveFilters =
    filters.disasterType ||
    filters.state ||
    filters.startDate ||
    filters.endDate;

  return (
    <div className="w-full space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-border">
        <h3 className="font-semibold text-sm text-foreground">
          {t("filterOptions")}
        </h3>
        {hasActiveFilters && (
          <button
            onClick={handleReset}
            className="text-xs text-red-600 hover:text-red-700 font-medium flex items-center gap-1"
          >
            <X className="w-3 h-3" /> {r("btnCancel")}
          </button>
        )}
      </div>

      {/* Grid layout for better use of space inside the slide-down */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Disaster Type */}
        <div className="space-y-1">
          <label className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground">
            {r("type")}
          </label>
          <Select
            value={filters.disasterType || "All Types"}
            onValueChange={handleDisasterTypeChange}
          >
            <SelectTrigger className="h-9">
              <SelectValue placeholder="Select type" />
            </SelectTrigger>
            <SelectContent className="z-2000">
              {DISASTER_TYPES.map((type) => (
                <SelectItem key={type || "all"} value={type || "All Types"}>
                  {type === "" ? d("allTypes") : d(type)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* State */}
        <div className="space-y-1">
          <label className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground">
            {t("state")}
          </label>
          <Select
            value={filters.state || "All States"}
            onValueChange={handleStateChange}
          >
            <SelectTrigger className="h-9">
              <SelectValue placeholder={t("selectState")} />
            </SelectTrigger>
            <SelectContent className="z-2000">
              {MALAYSIAN_STATES.map((state) => (
                <SelectItem key={state} value={state}>
                  {state === "All States" ? t("selectState") : state}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Dates */}
        <div className="space-y-1">
          <label className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground">
            {r("startDate")}
          </label>
          <Input
            type="date"
            value={filters.startDate}
            onChange={handleStartDateChange}
            className="h-9"
          />
        </div>
        <div className="space-y-1">
          <label className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground">
            {r("endDate")}
          </label>
          <Input
            type="date"
            value={filters.endDate}
            onChange={handleEndDateChange}
            className="h-9"
          />
        </div>
      </div>
    </div>
  );
}
