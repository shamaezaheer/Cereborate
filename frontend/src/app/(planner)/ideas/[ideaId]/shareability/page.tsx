"use client";

import useSWR from "swr";
import { useSession } from "next-auth/react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { ShareabilityMeter } from "@/components/brain/ShareabilityMeter";
import { classificationColor } from "@/lib/shareability";
import type { IdeaShareability } from "@/types/shareability";

export default function IdeaShareabilityPage() {
  const { data: authSession } = useSession();
  const params = useParams();
  const ideaId = params.ideaId as string;

  const { data, isLoading, mutate } = useSWR<IdeaShareability>(
    authSession ? `/api/v1/ideas/${ideaId}/shareability` : null,
    (url) => apiFetch(url, { token: (authSession as any)?.accessToken })
  );

  const handleRecompute = async () => {
    await apiFetch(`/api/v1/ideas/${ideaId}/shareability/recompute`, {
      method: "POST",
      token: (authSession as any)?.accessToken,
    });
    mutate();
  };

  return (
    <div className="max-w-3xl mx-auto p-8">
      <div className="mb-6">
        <Link
          href={`/ideas/${ideaId}`}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          &larr; Back to idea
        </Link>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Shareability</h1>
        <button
          onClick={handleRecompute}
          className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          Recompute All
        </button>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : data ? (
        <div className="space-y-8">
          <div className="rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">Overall Index</h2>
            <ShareabilityMeter
              index={data.shareability_index}
              label="Idea Shareability"
            />
          </div>

          <div className="rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">Component Scores</h2>
            {data.component_scores.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                No components yet.
              </p>
            ) : (
              <div className="space-y-4">
                {data.component_scores.map((cs) => (
                  <div
                    key={cs.component_id}
                    className="flex items-center justify-between border-b pb-3 last:border-0"
                  >
                    <div className="space-y-1">
                      <p className="font-medium">{cs.name}</p>
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full ${classificationColor(cs.classification as any)}`}
                        >
                          {cs.classification}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          Tier {cs.min_access_tier}
                        </span>
                        {cs.auto_classified && (
                          <span className="text-xs text-muted-foreground italic">
                            (auto)
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="w-32">
                      <ShareabilityMeter index={cs.shareability_score} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
