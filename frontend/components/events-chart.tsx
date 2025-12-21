"use client";

import React from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  LabelList,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface EventTrendChartProps {
  title?: string;
  type?: "area" | "bar" | "line";
  color?: string;
  data: {
    _id?: { year: number; month: number };
    total_events?: number;
    name?: string;
    value?: number;
  }[];
}

export default function EventTrendChart({
  data,
  title = "Event Trends",
  type = "area", // Default to area
  color = "#3b82f6",
}: EventTrendChartProps) {
  const chartData =
    data?.map((item) => {
      if (item.name && item.value !== undefined) return item;

      return {
        name: item._id
          ? new Date(item._id.year, item._id.month - 1).toLocaleString(
              "default",
              {
                month: "short",
                year: "2-digit",
              }
            )
          : "",
        value: item.total_events || 0,
      };
    }) || [];

  return (
    <Card className="w-full shadow-sm border-gray-100">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-bold text-gray-500 uppercase tracking-wider">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[350px] w-full">
          {" "}
          {/* Increased height slightly for rotated labels */}
          <ResponsiveContainer width="100%" height="100%">
            {type === "bar" ? (
              <BarChart
                data={chartData}
                margin={{ top: 10, right: 10, left: -20, bottom: 60 }}
              >
                <CartesianGrid
                  vertical={false}
                  strokeDasharray="3 3"
                  className="stroke-muted/50"
                />
                <XAxis
                  dataKey="name"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: "#9ca3af" }}
                  interval={0} // Forces every label (Kuala Lumpur, etc.) to show
                  angle={-45} // Rotates names to prevent overlapping
                  textAnchor="end" // Aligns rotated text to the end of the tick
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: "#9ca3af" }}
                />
                <Tooltip
                  cursor={{ fill: "transparent" }}
                  contentStyle={{
                    borderRadius: "8px",
                    border: "none",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                  }}
                />
                <Bar
                  dataKey="value"
                  fill={color}
                  radius={[4, 4, 0, 0]}
                  barSize={40}
                >
                  <LabelList
                    dataKey="value"
                    position="top"
                    content={(props: any) => {
                      const { x, y, width, value } = props;
                      return (
                        <text
                          x={x + width / 2}
                          y={y - 10}
                          fill={color}
                          textAnchor="middle"
                          fontSize="12"
                          fontWeight="bold"
                          className="hidden print:block" // Hidden on UI, visible in PDF
                        >
                          {value > 0 ? value : ""}
                        </text>
                      );
                    }}
                  />
                </Bar>
              </BarChart>
            ) : (
              <AreaChart
                data={chartData}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={color} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  vertical={false}
                  strokeDasharray="3 3"
                  className="stroke-muted/50"
                />
                <XAxis
                  dataKey="name"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: "#9ca3af" }}
                  // Ensure we only show the month name
                  tickFormatter={(value) => value.split(" ")[0]}
                  minTickGap={20}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: "#9ca3af" }}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: "8px",
                    border: "none",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={color}
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#colorValue)"
                >
                  <LabelList
                    dataKey="value"
                    position="top"
                    content={(props: any) => {
                      const { x, y, value } = props;
                      return (
                        <text
                          x={x}
                          y={y - 10}
                          fill="#4b5563"
                          textAnchor="middle"
                          fontSize="11"
                          fontWeight="bold"
                          className="hidden print:block" // Hidden on UI, visible in PDF
                        >
                          {value > 0 ? value : ""}
                        </text>
                      );
                    }}
                  />
                </Area>
              </AreaChart>
            )}
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
