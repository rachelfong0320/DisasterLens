interface MetricsCardProps {
  label: string
  value: string
  change: string
  trend: "up" | "down"
  icon: string
}

export default function MetricsCard({ label, value, change, trend, icon }: MetricsCardProps) {
  const TrendIcon = trend === "up" ? "↑" : "↓"
  const trendColor = trend === "up" ? "text-chart-1" : "text-chart-4"

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-sm text-muted-foreground mb-1">{label}</p>
          <p className="text-2xl font-bold text-foreground">{value}</p>
        </div>
        <span className="text-2xl">{icon}</span>
      </div>
      <div className="flex items-center gap-1 text-sm">
        <span className={`text-lg ${trendColor}`}>{TrendIcon}</span>
        <span className={trend === "up" ? "text-chart-1" : "text-chart-4"}>{change}</span>
        <span className="text-muted-foreground">vs last month</span>
      </div>
    </div>
  )
}
