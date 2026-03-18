export interface Idea {
  id: string;
  tenant_id: string;
  creator_id: string;
  title: string;
  description: string;
  status: "draft" | "active" | "archived";
  deadline: string | null;
  total_budget: number | null;
  budget_currency: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface IdeaComponent {
  id: string;
  idea_id: string;
  name: string;
  description: string;
  estimated_cost: number | null;
  priority: "must_have" | "should_have" | "nice_to_have";
  status: "proposed" | "approved" | "in_progress" | "done";
  deadline: string | null;
  shareability_score: number;
  created_at: string;
}

export interface Budget {
  id: string;
  idea_id: string;
  total_amount: number;
  currency: string;
  line_items: BudgetLineItem[];
}

export interface BudgetLineItem {
  id: string;
  budget_id: string;
  description: string;
  amount: number;
  component_id: string | null;
}
