export interface ComponentDependency {
  id: string;
  source_component_id: string;
  target_component_id: string;
  dependency_type: "blocks" | "requires_output" | "shares_resource" | "extends" | "informed_by";
  is_cross_idea: boolean;
  llm_detected: boolean;
  confirmed: boolean;
  llm_rationale: string | null;
  created_at: string;
}

export interface DependencyGraph {
  nodes: Array<{
    id: string;
    name: string;
    status: string;
    priority: string;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    type: string;
    is_cross_idea: boolean;
    confirmed: boolean;
  }>;
}

export interface SharedDependency {
  dependency_id: string;
  dependency_type: string;
  source: {
    id: string;
    name: string;
    description: string;
    status: string;
    deadline: string | null;
    idea_id: string;
  };
  target: {
    id: string;
    name: string;
    description: string;
    status: string;
    deadline: string | null;
    idea_id: string;
  };
}
