"use client"

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface MetricListChartProps {
  title: string;
  data: { name: string; value: number }[];
  color?: string;
  unit?: string; // e.g., "Hits" or "Events"
}

export default function MetricListChart({ 
  title, 
  data, 
  color = "#3b82f6",
  unit = "Hits"
}: MetricListChartProps) {
  // Finds the highest value to make the bars proportionally accurate
  const maxValue = data.length > 0 ? Math.max(...data.map(d => d.value)) : 0;

  return (
    <Card className="w-full shadow-sm border-gray-100">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-bold text-gray-500 uppercase tracking-wider">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {data.map((item, index) => (
            <div key={item.name} className="group">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold text-gray-700 group-hover:text-blue-600 transition-colors">
                  {item.name}
                </span>
                <span className="text-xs font-bold px-2 py-1 rounded bg-blue-50 text-blue-600">
                  {item.value} {unit}
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                <div 
                  className="h-full rounded-full transition-all duration-1000 ease-out"
                  style={{ 
                    backgroundColor: color,
                    // Calculates width relative to the largest item in this specific list
                    width: maxValue > 0 ? `${(item.value / maxValue) * 100}%` : '0%' 
                  }}
                />
              </div>
            </div>
          ))}
          {data.length === 0 && (
            <div className="flex items-center justify-center h-32">
              <p className="text-sm text-muted-foreground italic">No data available for this range</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}