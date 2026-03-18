export interface ShareabilityRule {
  id: string;
  idea_id: string | null;
  component_id: string | null;
  min_access_tier: number;
  classification: "public" | "internal" | "confidential" | "restricted";
  auto_classified: boolean;
  overridden_by: string | null;
}

export interface ComponentShareabilityInfo {
  component_id: string;
  name: string;
  shareability_score: number;
  classification: string;
  min_access_tier: number;
  auto_classified: boolean;
}

export interface IdeaShareability {
  idea_id: string;
  shareability_index: number;
  rules: ShareabilityRule[];
  component_scores: ComponentShareabilityInfo[];
}
