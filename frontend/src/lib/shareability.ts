/**
 * Client-side helpers for shareability tier checks.
 */

export type Classification = "public" | "internal" | "confidential" | "restricted";

export const TIER_LABELS: Record<string, string> = {
  "1": "Public",
  "2": "Public",
  "3": "Internal",
  "4": "Internal",
  "5": "Confidential",
  "6": "Confidential",
  "7": "Restricted",
  "8": "Restricted",
  "9": "Top Secret",
  "10": "Top Secret",
};

export function canAccess(userTier: number, requiredTier: number): boolean {
  return userTier >= requiredTier;
}

export function classificationColor(classification: Classification): string {
  switch (classification) {
    case "public":
      return "text-green-600 bg-green-50";
    case "internal":
      return "text-blue-600 bg-blue-50";
    case "confidential":
      return "text-orange-600 bg-orange-50";
    case "restricted":
      return "text-red-600 bg-red-50";
    default:
      return "text-gray-600 bg-gray-50";
  }
}

export function tierToClassification(tier: number): Classification {
  if (tier <= 2) return "public";
  if (tier <= 4) return "internal";
  if (tier <= 6) return "confidential";
  return "restricted";
}
