export interface PlanningSession {
  id: string;
  status: "active" | "completed" | "abandoned";
  mode: "chat" | "form" | "hybrid";
  conversation_history: Array<{ role: "user" | "assistant"; content: string }>;
  extracted_data: ExtractedIdeaData;
  idea_id: string | null;
  created_at: string;
}

export interface ExtractedIdeaData {
  title: string;
  description: string;
  deadline: string | null;
  total_budget: number | null;
  budget_currency: string;
  components: ExtractedComponent[];
  follow_up_question: string | null;
  is_complete: boolean;
}

export interface ExtractedComponent {
  name: string;
  description: string;
  priority: string;
  estimated_cost: number | null;
}
