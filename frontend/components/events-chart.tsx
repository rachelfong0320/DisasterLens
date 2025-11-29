"use client"

import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

interface EventsChartProps {
  title: string
  type: "bar" | "line" | "pie"
}

const data = {
  bar: [
    { name: "Jan", events: 45 },
    { name: "Feb", events: 52 },
    { name: "Mar", events: 38 },
    { name: "Apr", events: 61 },
    { name: "May", events: 55 },
    { name: "Jun", events: 67 },
  ],
  pie: [
    { name: "Flood", value: 120 },
    { name: "Landslide", value: 85 },
    { name: "Fire", value: 25 },
    { name: "Haze", value: 15 },
    { name: "Storm", value: 5 },
  ],
  line: [
    { month: "Week 1", events: 20 },
    { month: "Week 2", events: 35 },
    { month: "Week 3", events: 28 },
    { month: "Week 4", events: 45 },
  ],
}

const COLORS = ["#3366cc", "#33cccc", "#cccc33", "#cc6633", "#cc3333"]

export default function EventsChart({ title, type }: EventsChartProps) {
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h3 className="text-lg font-semibold text-foreground mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        {type === "bar" && (
          <BarChart data={data.bar}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis stroke="var(--muted-foreground)" />
            <YAxis stroke="var(--muted-foreground)" />
            <Tooltip contentStyle={{ backgroundColor: "var(--card)", border: "1px solid var(--border)" }} />
            <Bar dataKey="events" fill="var(--chart-1)" />
          </BarChart>
        )}
        {type === "line" && (
          <LineChart data={data.line}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis stroke="var(--muted-foreground)" />
            <YAxis stroke="var(--muted-foreground)" />
            <Tooltip contentStyle={{ backgroundColor: "var(--card)", border: "1px solid var(--border)" }} />
            <Line type="monotone" dataKey="events" stroke="var(--chart-2)" strokeWidth={2} />
          </LineChart>
        )}
        {type === "pie" && (
          <PieChart>
            <Pie
              data={data.pie}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value }) => `${name}: ${value}`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data.pie.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        )}
      </ResponsiveContainer>
    </div>
  )
}
