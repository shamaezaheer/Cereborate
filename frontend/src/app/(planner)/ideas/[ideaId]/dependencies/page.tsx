"use client";

import useSWR from "swr";
import { useSession } from "next-auth/react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { DependencyGraph } from "@/components/brain/DependencyGraph";
import type { DependencyGraph as DependencyGraphType } from "@/types/dependency";

export default function IdeaDependenciesPage() {
  const { data: authSession } = useSession();
  const params = useParams();
  const ideaId = params.ideaId as string;

  const { data: graph, isLoading } = useSWR<DependencyGraphType>(
    authSession ? `/api/v1/ideas/${ideaId}/dependency-graph` : null,
    (url) => apiFetch(url, { token: (authSession as any)?.accessToken })
  );

  return (
    <div className="max-w-3xl mx-auto p-8">
      <div className="mb-6">
        <Link
          href={`/ideas/${ideaId}`}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          ← Back to idea
        </Link>
      </div>

      <h1 className="text-2xl font-bold mb-6">Dependency Graph</h1>

      {isLoading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : graph ? (
        <DependencyGraph graph={graph} />
      ) : null}
    </div>
  );
}
