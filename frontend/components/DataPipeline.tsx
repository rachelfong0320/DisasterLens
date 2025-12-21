const steps = [
  "RapidAPI & Public Sources",
  "Validation",
  "Cleaning",
  "Normalization",
  "Database Storage",
];

export default function DataPipeline() {
  return (
    <div className="my-10">
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
        {steps.map((step, i) => (
          <div
            key={step}
            className="relative rounded-lg border border-border bg-card p-4 text-center text-sm font-medium"
          >
            <span className="block text-muted-foreground text-xs mb-1">
              Step {i + 1}
            </span>
            {step}
          </div>
        ))}
      </div>
    </div>
  );
}
