"use client";

import useSWR from "swr";
import { useSession } from "next-auth/react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import type { Idea, IdeaComponent } from "@/types/idea";

interface IdeaDetail extends Idea {
  components: IdeaComponent[];
}

export default function IdeaDetailPage() {
  const { data: authSession } = useSession();
  const params = useParams();
  const ideaId = params.ideaId as string;

  const { data: idea, isLoading } = useSWR(
    authSession ? `/api/v1/ideas/${ideaId}` : null,
    (url) => apiFetch<IdeaDetail>(url, { token: (authSession as any)?.accessToken })
  );

  if (isLoading) {
    return <div className="p-8 text-muted-foreground">Loading...</div>;
  }

  if (!idea) return null;

  const priorityColors: Record<string, string> = {
    must_have: "bg-red-100 text-red-700",
    should_have: "bg-yellow-100 text-yellow-700",
    nice_to_have: "bg-green-100 text-green-700",
  };

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="mb-6">
        <Link href="/ideas" className="text-sm text-muted-foreground hover:text-foreground">
          ← Back to ideas
        </Link>
      </div>

      <div className="mb-8">
        <div className="flex items-start justify-between">
          <h1 className="text-3xl font-bold">{idea.title}</h1>
          <span className="text-xs px-2 py-1 rounded-full bg-muted text-muted-foreground">
            {idea.status} · v{idea.version}
          </span>
        </div>
        {idea.description && (
          <p className="text-muted-foreground mt-3">{idea.description}</p>
        )}
        <div className="flex gap-4 mt-4 text-sm text-muted-foreground">
          {idea.deadline && (
            <span>Deadline: {new Date(idea.deadline).toLocaleDateString()}</span>
          )}
          {idea.total_budget && (
            <span>
              Budget: {Number(idea.total_budget).toLocaleString()} {idea.budget_currency}
            </span>
          )}
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Components</h2>
          <Link
            href={`/ideas/${ideaId}/components`}
            className="text-sm text-primary hover:underline"
          >
            Manage
          </Link>
        </div>

        {idea.components.length === 0 ? (
          <p className="text-muted-foreground text-sm">No components yet.</p>
        ) : (
          <div className="space-y-3">
            {idea.components.map((c) => (
              <div key={c.id} className="border rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <h3 className="font-medium">{c.name}</h3>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${priorityColors[c.priority] || "bg-muted"}`}
                  >
                    {c.priority.replace("_", " ")}
                  </span>
                </div>
                {c.description && (
                  <p className="text-sm text-muted-foreground mt-1">{c.description}</p>
                )}
                <div className="flex gap-3 mt-2 text-xs text-muted-foreground">
                  <span>Status: {c.status}</span>
                  {c.estimated_cost && (
                    <span>Cost: {Number(c.estimated_cost).toLocaleString()}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
