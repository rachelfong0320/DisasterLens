"use client"

import React from 'react'
import { Filter, ChevronDown } from 'lucide-react'

interface DisasterFilterProps {
  value: string;
  onChange: (value: string) => void;
  options: Record<string, { label: string }>;
}

export default function DisasterFilter({ value, onChange, options }: DisasterFilterProps) {
  return (
    <div className="relative inline-block w-full md:w-auto">
      {/* Icon: Exactly 3 units from left, gray-400 to match TimeFilter */}
      <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
      
      <select 
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="
          appearance-none bg-white border border-gray-200 
          rounded-lg pl-9 pr-10 py-2 h-[38px]
          text-sm font-semibold text-gray-700 
          hover:border-gray-300 focus:ring-2 focus:ring-blue-500/20 
          outline-none transition-all cursor-pointer shadow-sm w-full min-w-[180px]
        "
      >
        <option value="all">All Disasters</option>
        {Object.entries(options).map(([key, config]) => (
          <option key={key} value={key}>
            {config.label}
          </option>
        ))}
      </select>

      {/* Trailing arrow: Exactly 3 units from right */}
      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
    </div>
  )
}