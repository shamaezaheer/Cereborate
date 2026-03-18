"use client";

import { classificationColor, type Classification } from "@/lib/shareability";

interface AccessBadgeProps {
  classification: Classification;
  tier: number;
}

export function AccessBadge({ classification, tier }: AccessBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${classificationColor(classification)}`}
    >
      Tier {tier} · {classification}
    </span>
  );
}
