"use client";

import useSWR from "swr";
import { useSession } from "next-auth/react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import type { SharedDependency } from "@/types/dependency";

const DEP_COLORS: Record<string, string> = {
  blocks: "bg-red-50 text-red-700",
  requires_output: "bg-orange-50 text-orange-700",
  shares_resource: "bg-yellow-50 text-yellow-700",
  extends: "bg-blue-50 text-blue-700",
  informed_by: "bg-gray-50 text-gray-700",
};

export default function SharedIdeaDependenciesPage() {
  const { data: session } = useSession();
  const params = useParams();
  const ideaId = params.ideaId as string;
  const token = (session as any)?.accessToken as string;

  const { data: deps, isLoading } = useSWR<SharedDependency[]>(
    session ? `/api/v1/shared/ideas/${ideaId}/dependencies` : null,
    (url) => apiFetch(url, { token })
  );

  return (
    <div className="max-w-3xl mx-auto p-8">
      <div className="mb-6">
        <Link href={`/shared/${ideaId}`} className="text-sm text-muted-foreground hover:text-foreground">
          &larr; Back to idea
        </Link>
      </div>
      <h1 className="text-2xl font-bold mb-6">Shared Dependencies</h1>
      <p className="text-muted-foreground mb-8 text-sm">
        Components from this idea that have cross-idea dependencies with other teams.
      </p>

      {isLoading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : !deps || deps.length === 0 ? (
        <p className="text-muted-foreground">No shared dependencies for this idea.</p>
      ) : (
        <div className="space-y-4">
          {deps.map((dep) => (
            <div key={dep.dependency_id} className="border rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${DEP_COLORS[dep.dependency_type] ?? ""}`}>
                  {dep.dependency_type.replace("_", " ")}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                {[dep.source, dep.target].map((comp, i) => (
                  <div key={comp.id} className={`rounded-md p-3 ${i === 0 ? "bg-blue-50" : "bg-purple-50"}`}>
                    <p className="text-xs text-muted-foreground mb-1">
                      {i === 0 ? "Source" : "Target"}
                    </p>
                    <p className="font-medium text-sm">{comp.name}</p>
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{comp.description}</p>
                    <div className="flex gap-2 mt-2">
                      <span className="text-xs bg-white px-1.5 py-0.5 rounded border">{comp.status}</span>
                      {comp.deadline && (
                        <span className="text-xs text-muted-foreground">
                          Due {new Date(comp.deadline).toLocaleDateString()}
                        </span>
                      )}
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
