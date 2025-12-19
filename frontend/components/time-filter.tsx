"use client"

import { useState } from "react";
import { CalendarDays, ChevronDown, ArrowRight, Clock } from "lucide-react";
import { getTimeRange } from "@/lib/date-utils";

interface TimeFilterProps {
  onRangeChange: (start: string, end: string) => void;
}

export default function TimeFilter({ onRangeChange }: TimeFilterProps) {
  const [isCustom, setIsCustom] = useState(false);
  const [customDates, setCustomDates] = useState({ start: "", end: "" });

  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const range = e.target.value;
    if (range === "custom") {
      setIsCustom(true);
    } else {
      setIsCustom(false);
      const { start, end } = getTimeRange(range);
      onRangeChange(start, end);
    }
  };

  const handleCustomDateChange = (type: "start" | "end", value: string) => {
    const newDates = { ...customDates, [type]: value };
    setCustomDates(newDates);
    // Only trigger API if both dates are filled
    if (newDates.start && newDates.end) {
      onRangeChange(newDates.start, newDates.end);
    }
  };

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2">
      <div className="relative inline-block">
        <CalendarDays className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        <select
            onChange={handleSelectChange}
            className="appearance-none bg-white border border-gray-200 rounded-lg pl-9 pr-10 py-2 text-sm font-semibold text-gray-700 hover:border-gray-300 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all cursor-pointer shadow-sm"
            defaultValue="this-year"
            >
            <option value="this-year">This Year</option>
            <option value="this-month">This Month</option>
            <option value="this-week">This Week</option>
            <option value="last-week">Last Week</option>
            <option value="last-30-days">Last 30 Days</option>
            <option value="custom">Custom Range</option>
        </select>
    
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
      </div>

      {isCustom && (
        <div className="flex items-center gap-2 animate-in fade-in slide-in-from-left-2 duration-300">
          <input
            type="date"
            onChange={(e) => handleCustomDateChange("start", e.target.value)}
            className="border border-gray-200 rounded-lg px-2 py-1.5 text-xs font-medium focus:ring-2 focus:ring-blue-500/20 outline-none"
          />
          <ArrowRight className="w-3 h-3 text-gray-400" />
          <input
            type="date"
            onChange={(e) => handleCustomDateChange("end", e.target.value)}
            className="border border-gray-200 rounded-lg px-2 py-1.5 text-xs font-medium focus:ring-2 focus:ring-blue-500/20 outline-none"
          />
        </div>
      )}
    </div>
  );
}