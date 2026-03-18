"use client";

import type { DependencyGraph as DependencyGraphType } from "@/types/dependency";

interface Props {
  graph: DependencyGraphType;
}

const statusColors: Record<string, string> = {
  proposed: "bg-gray-100 text-gray-700",
  approved: "bg-blue-100 text-blue-700",
  in_progress: "bg-yellow-100 text-yellow-700",
  done: "bg-green-100 text-green-700",
};

const depTypeLabels: Record<string, string> = {
  blocks: "BLOCKS",
  requires_output: "NEEDS OUTPUT",
  shares_resource: "SHARES",
  extends: "EXTENDS",
  informed_by: "INFORMS",
};

export function DependencyGraph({ graph }: Props) {
  const { nodes, edges } = graph;

  const nodeMap = Object.fromEntries(nodes.map((n) => [n.id, n]));

  if (nodes.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground text-sm">
        No dependencies yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-2">
        {nodes.map((node) => (
          <div key={node.id} className="border rounded-lg p-3">
            <div className="flex items-center justify-between">
              <span className="font-medium text-sm">{node.name}</span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${statusColors[node.status] || "bg-muted"}`}
              >
                {node.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      {edges.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2 text-muted-foreground">Dependencies</h4>
          <div className="space-y-2">
            {edges.map((edge) => (
              <div
                key={edge.id}
                className={`flex items-center gap-2 text-sm p-2 rounded border ${
                  edge.is_cross_idea ? "border-pink-200 bg-pink-50" : "border-gray-100"
                } ${!edge.confirmed && edge.is_cross_idea ? "opacity-60" : ""}`}
              >
                <span className="font-medium">{nodeMap[edge.source]?.name ?? "?"}</span>
                <span className="text-xs px-1.5 py-0.5 bg-muted rounded font-mono">
                  {depTypeLabels[edge.type] ?? edge.type}
                </span>
                <span className="font-medium">{nodeMap[edge.target]?.name ?? "?"}</span>
                {edge.is_cross_idea && (
                  <span className="text-xs text-pink-600 ml-auto">cross-idea</span>
                )}
                {!edge.confirmed && (
                  <span className="text-xs text-muted-foreground ml-auto">unconfirmed</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
