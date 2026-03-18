"use client";

interface ShareabilityMeterProps {
  index: number;
  label?: string;
}

function getTierLabel(index: number): string {
  if (index <= 0.2) return "Public";
  if (index <= 0.4) return "Internal";
  if (index <= 0.6) return "Moderate";
  if (index <= 0.8) return "Confidential";
  return "Restricted";
}

function getMeterColor(index: number): string {
  if (index <= 0.2) return "bg-green-500";
  if (index <= 0.4) return "bg-blue-500";
  if (index <= 0.6) return "bg-yellow-500";
  if (index <= 0.8) return "bg-orange-500";
  return "bg-red-500";
}

export function ShareabilityMeter({ index, label }: ShareabilityMeterProps) {
  const pct = Math.round(index * 100);
  const tierLabel = getTierLabel(index);
  const color = getMeterColor(index);

  return (
    <div className="space-y-1">
      {label && (
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">{label}</span>
          <span className="font-medium">
            {tierLabel} ({pct}%)
          </span>
        </div>
      )}
      <div className="w-full bg-muted rounded-full h-2.5">
        <div
          className={`h-2.5 rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
