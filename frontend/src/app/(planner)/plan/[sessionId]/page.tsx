"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter, useParams } from "next/navigation";
import { PlanningChat } from "@/components/planning/PlanningChat";
import { apiFetch } from "@/lib/api";
import type { PlanningSession } from "@/types/planning";

export default function ActiveSessionPage() {
  const { data: authSession } = useSession();
  const router = useRouter();
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [session, setSession] = useState<PlanningSession | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authSession) return;

    apiFetch<PlanningSession>(`/api/v1/plan/${sessionId}`, {
      token: (authSession as any).accessToken,
    })
      .then(setSession)
      .catch(() => router.push("/plan"))
      .finally(() => setLoading(false));
  }, [authSession, sessionId]);

  async function handleComplete(sid: string) {
    const result = await apiFetch<{ idea: { id: string } }>(
      `/api/v1/plan/${sid}/complete`,
      {
        method: "POST",
        token: (authSession as any)?.accessToken,
      }
    );
    router.push(`/ideas/${result.idea.id}`);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-muted-foreground">Loading session...</p>
      </div>
    );
  }

  if (!session || !authSession) return null;

  return (
    <div className="flex h-screen">
      {/* Chat panel */}
      <div className="flex-1 flex flex-col border-r">
        <div className="p-4 border-b">
          <h2 className="font-semibold">Planning Session</h2>
        </div>
        <div className="flex-1 overflow-hidden">
          <PlanningChat
            session={session}
            token={(authSession as any).accessToken}
            onComplete={handleComplete}
            onExtractedUpdate={(data) =>
              setSession((prev) => prev ? { ...prev, extracted_data: data } : prev)
            }
          />
        </div>
      </div>

      {/* Extracted data panel */}
      <div className="w-80 p-4 overflow-y-auto">
        <h3 className="font-semibold mb-4">Extracted Data</h3>
        {session.extracted_data.title && (
          <div className="mb-3">
            <p className="text-xs text-muted-foreground uppercase font-medium">Title</p>
            <p className="text-sm mt-1">{session.extracted_data.title}</p>
          </div>
        )}
        {session.extracted_data.description && (
          <div className="mb-3">
            <p className="text-xs text-muted-foreground uppercase font-medium">Description</p>
            <p className="text-sm mt-1">{session.extracted_data.description}</p>
          </div>
        )}
        {session.extracted_data.components.length > 0 && (
          <div className="mb-3">
            <p className="text-xs text-muted-foreground uppercase font-medium">Components</p>
            <ul className="mt-1 space-y-1">
              {session.extracted_data.components.map((c, i) => (
                <li key={i} className="text-sm flex items-start gap-1">
                  <span className="text-primary">•</span>
                  <span>{c.name}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {session.extracted_data.deadline && (
          <div className="mb-3">
            <p className="text-xs text-muted-foreground uppercase font-medium">Deadline</p>
            <p className="text-sm mt-1">{session.extracted_data.deadline}</p>
          </div>
        )}
        {session.extracted_data.total_budget && (
          <div className="mb-3">
            <p className="text-xs text-muted-foreground uppercase font-medium">Budget</p>
            <p className="text-sm mt-1">
              {session.extracted_data.total_budget.toLocaleString()}{" "}
              {session.extracted_data.budget_currency}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
