"use client";

import useSWR from "swr";
import { useSession } from "next-auth/react";
import { apiFetch } from "@/lib/api";
import type { SharedDependency } from "@/types/dependency";
import Link from "next/link";

const DEP_COLORS: Record<string, string> = {
  blocks: "bg-red-50 text-red-700 border-red-200",
  requires_output: "bg-orange-50 text-orange-700 border-orange-200",
  shares_resource: "bg-yellow-50 text-yellow-700 border-yellow-200",
  extends: "bg-blue-50 text-blue-700 border-blue-200",
  informed_by: "bg-gray-50 text-gray-700 border-gray-200",
};

export default function SharedDependenciesPage() {
  const { data: session } = useSession();
  const token = (session as any)?.accessToken as string;

  const { data: deps, isLoading } = useSWR<SharedDependency[]>(
    session ? "/api/v1/shared/dependencies" : null,
    (url) => apiFetch(url, { token })
  );

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-2">Shared Dependencies</h1>
      <p className="text-muted-foreground mb-8 text-sm">
        All cross-idea dependencies where your ideas are involved.
      </p>

      {isLoading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : !deps || deps.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-lg">No shared dependencies yet.</p>
          <p className="text-sm mt-2">
            Cross-idea dependencies appear here when the Brain detects or you create them.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {deps.map((dep) => (
            <div
              key={dep.dependency_id}
              className={`border rounded-lg p-4 space-y-3 ${DEP_COLORS[dep.dependency_type]?.split(" ").slice(2).join(" ") ?? ""}`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium border ${DEP_COLORS[dep.dependency_type] ?? "bg-gray-50 text-gray-700"}`}
                >
                  {dep.dependency_type.replace(/_/g, " ")}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: "Source", comp: dep.source },
                  { label: "Target", comp: dep.target },
                ].map(({ label, comp }) => (
                  <div key={comp.id} className="bg-white rounded-md p-3 border">
                    <p className="text-xs text-muted-foreground mb-1">{label}</p>
                    <p className="font-medium text-sm">{comp.name}</p>
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {comp.description}
                    </p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      <span className="text-xs bg-muted px-1.5 py-0.5 rounded">
                        {comp.status}
                      </span>
                      {comp.deadline && (
                        <span className="text-xs text-muted-foreground">
                          Due {new Date(comp.deadline).toLocaleDateString()}
                        </span>
                      )}
                      <Link
                        href={`/shared/${comp.idea_id}`}
                        className="text-xs text-primary hover:underline"
                      >
                        View idea →
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
