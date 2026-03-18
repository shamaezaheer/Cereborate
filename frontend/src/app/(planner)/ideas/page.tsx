"use client";

import useSWR from "swr";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import type { Idea } from "@/types/idea";

export default function IdeasPage() {
  const { data: authSession } = useSession();

  const { data: ideas, isLoading } = useSWR(
    authSession ? "/api/v1/ideas" : null,
    (url) =>
      apiFetch<Idea[]>(url, { token: (authSession as any)?.accessToken })
  );

  if (isLoading) {
    return (
      <div className="p-8">
        <p className="text-muted-foreground">Loading ideas...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">My Ideas</h1>
        <Link
          href="/plan"
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium"
        >
          + New Idea
        </Link>
      </div>

      {!ideas?.length ? (
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-lg">No ideas yet.</p>
          <Link href="/plan" className="text-primary hover:underline text-sm mt-2 inline-block">
            Start your first idea →
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {ideas.map((idea) => (
            <Link
              key={idea.id}
              href={`/ideas/${idea.id}`}
              className="block p-4 border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="font-semibold">{idea.title}</h2>
                  {idea.description && (
                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                      {idea.description}
                    </p>
                  )}
                </div>
                <span className="text-xs px-2 py-1 rounded-full bg-muted text-muted-foreground ml-4 shrink-0">
                  {idea.status}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                {new Date(idea.updated_at).toLocaleDateString()}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
