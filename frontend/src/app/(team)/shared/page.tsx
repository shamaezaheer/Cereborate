"use client";

import useSWR from "swr";
import { useSession } from "next-auth/react";
import { apiFetch } from "@/lib/api";
import { SharedIdeaCard } from "@/components/team/SharedIdeaCard";
import type { SharedIdea } from "@/types/team";

export default function SharedIdeasPage() {
  const { data: session } = useSession();

  const { data: ideas, isLoading } = useSWR<SharedIdea[]>(
    session ? "/api/v1/shared/ideas" : null,
    (url) => apiFetch(url, { token: (session as any)?.accessToken })
  );

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Shared Ideas</h1>
      <p className="text-muted-foreground mb-8">
        Ideas shared with your team, filtered to your access tier.
      </p>

      {isLoading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : !ideas || ideas.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-lg">No shared ideas yet.</p>
          <p className="text-sm mt-2">
            Ideas become visible here once their owners configure shareability.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {ideas.map((idea) => (
            <SharedIdeaCard key={idea.id} idea={idea} />
          ))}
        </div>
      )}
    </div>
  );
}
