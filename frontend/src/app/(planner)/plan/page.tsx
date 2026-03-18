"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type { PlanningSession } from "@/types/planning";

export default function NewPlanPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function startPlan() {
    if (!message.trim() || !session) return;
    setLoading(true);
    setError(null);

    try {
      const planSession = await apiFetch<PlanningSession>("/api/v1/plan/start", {
        method: "POST",
        token: (session as any).accessToken,
        body: JSON.stringify({ message }),
      });
      router.push(`/plan/${planSession.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to start planning session");
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto mt-16 px-4">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold">What&apos;s your idea?</h1>
        <p className="text-muted-foreground mt-2">
          Describe it briefly and I&apos;ll help you structure it into a full plan.
        </p>
      </div>

      <div className="space-y-4">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && e.metaKey && startPlan()}
          placeholder="e.g. I want to build a mobile app that helps people track their daily water intake..."
          rows={5}
          className="w-full px-4 py-3 border rounded-lg bg-background text-foreground resize-none"
          autoFocus
        />

        {error && <p className="text-sm text-destructive">{error}</p>}

        <button
          onClick={startPlan}
          disabled={loading || !message.trim()}
          className="w-full py-3 bg-primary text-primary-foreground rounded-lg font-medium disabled:opacity-50"
        >
          {loading ? "Starting..." : "Start Planning →"}
        </button>
      </div>

      <div className="mt-8 text-center">
        <a href="/ideas" className="text-sm text-muted-foreground hover:text-foreground">
          View existing ideas →
        </a>
      </div>
    </div>
  );
}
