"use client"

import { LucideIcon } from "lucide-react"

interface MetricsCardProps {
  label: string
  value: string
  icon: LucideIcon // Expects a Lucide component
  iconColor: string
}

export default function MetricsCard({ label, value, icon: Icon, iconColor }: MetricsCardProps) {
  return (
    <div className="bg-white border border-gray-100 rounded-xl p-5 shadow-sm hover:shadow-md transition-all flex items-center justify-between">
      <div className="space-y-1">
        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{label}</p>
        <h4 className="text-2xl font-bold text-gray-900">{value}</h4>
      </div>
      <div className={`p-3 rounded-lg bg-opacity-10 ${iconColor.replace('text', 'bg')}`}>
        <Icon className={`w-6 h-6 ${iconColor}`} />
      </div>
    </div>
  )
}