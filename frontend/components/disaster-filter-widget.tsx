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
import { Button } from "@/components/ui/button";
import { ChevronDown, X } from "lucide-react";

export type DisasterType =
  | "flood"
  | "landslide"
  | "forest_fire"
  | "storm"
  | "haze"
  | "sinkhole"
  | "earthquake"
  | "tsunami"
  | ""
  | "All Types";

export const DISASTER_TYPES: DisasterType[] = [
  "All Types",
  "flood",
  "landslide",
  "forest_fire",
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
  const [isOpen, setIsOpen] = useState(true);
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

  const clearField = (fieldName: keyof FilterOptions) => {
    const updated = { ...filters, [fieldName]: "" };
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
    <div className="w-full z-20">
      <Button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full bg-white text-foreground hover:bg-gray-50 border border-border shadow-md"
      >
        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
        </svg>
        Filters
        <ChevronDown className={`w-4 h-4 ml-auto transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </Button>

      {isOpen && (
        <div className="bg-white border border-border rounded-lg shadow-lg p-4 space-y-4 mt-2">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <h3 className="font-semibold text-sm text-foreground">Filter Disasters</h3>
            {hasActiveFilters && (
              <button onClick={handleReset} className="text-xs text-red-600 hover:text-red-700 font-medium flex items-center gap-1">
                <X className="w-3 h-3" /> Reset All
              </button>
            )}
          </div>

          {/* Disaster Type */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-foreground">Disaster Type</label>
            <Select value={filters.disasterType || "All Types"} onValueChange={handleDisasterTypeChange}>
              <SelectTrigger className="h-8 text-sm">
                <SelectValue placeholder="All types" />
              </SelectTrigger>
              <SelectContent className="z-50 max-h-48 overflow-y-auto">
                {DISASTER_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type === "" ? "All Types" : type.replace("_", " ").charAt(0).toUpperCase() + type.replace("_", " ").slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* State */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-foreground">State / Location</label>
            <Select value={filters.state || "All States"} onValueChange={handleStateChange}>
              <SelectTrigger className="h-8 text-sm">
                <SelectValue placeholder="All states" />
              </SelectTrigger>
              <SelectContent className="z-50 max-h-48 overflow-y-auto">
                {MALAYSIAN_STATES.map((state) => (
                  <SelectItem key={state} value={state}>
                    {state}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Start Date with Individual Clear */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-foreground">Start Date</label>
            <div className="relative group">
              <Input
                type="date"
                value={filters.startDate}
                onChange={handleStartDateChange}
                className="h-8 text-sm pr-8"
              />
              {filters.startDate && (
                <button 
                  onClick={() => clearField('startDate')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>

          {/* End Date with Individual Clear */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-foreground">End Date</label>
            <div className="relative group">
              <Input
                type="date"
                value={filters.endDate}
                onChange={handleEndDateChange}
                className="h-8 text-sm pr-8"
              />
              {filters.endDate && (
                <button 
                  onClick={() => clearField('endDate')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}