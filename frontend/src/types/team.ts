export interface Question {
  id: string;
  idea_id: string;
  component_id: string | null;
  asked_by: string | null;
  question_text: string;
  status: "open" | "answered" | "closed";
  created_at: string;
  answers?: Answer[];
}

export interface Answer {
  id: string;
  question_id: string;
  answered_by: string | null;
  answer_text: string;
  is_ai_generated: boolean;
  approved: boolean;
  created_at: string;
}

export interface Notification {
  id: string;
  event_type: string;
  idea_id: string | null;
  component_id: string | null;
  message: string;
  read: boolean;
  created_at: string;
}

export interface SharedIdea {
  id: string;
  title: string;
  description: string;
  status: string;
  shareability_index: number;
  shared_dep_count: number;
  creator_id: string | null;
}

export interface SharedIdeaDetail {
  id: string;
  title: string;
  description: string;
  status: string;
  deadline: string | null;
  components: SharedComponent[];
  shareability_index: number;
}

export interface SharedComponent {
  id: string;
  name: string;
  description: string;
  status: string;
  priority: string;
  deadline: string | null;
}
