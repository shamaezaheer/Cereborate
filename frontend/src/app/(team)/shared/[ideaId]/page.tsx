"use client";

import useSWR from "swr";
import { useSession } from "next-auth/react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { ShareabilityMeter } from "@/components/brain/ShareabilityMeter";
import { QuestionThread } from "@/components/team/QuestionThread";
import type { Answer, Question, SharedIdeaDetail } from "@/types/team";
import { useState } from "react";

const PRIORITY_COLORS: Record<string, string> = {
  must_have: "text-red-600 bg-red-50",
  should_have: "text-yellow-600 bg-yellow-50",
  nice_to_have: "text-green-600 bg-green-50",
};

const STATUS_COLORS: Record<string, string> = {
  proposed: "bg-gray-100 text-gray-700",
  approved: "bg-blue-100 text-blue-700",
  in_progress: "bg-yellow-100 text-yellow-700",
  done: "bg-green-100 text-green-700",
};

export default function SharedIdeaDetailPage() {
  const { data: session } = useSession();
  const params = useParams();
  const ideaId = params.ideaId as string;
  const token = (session as any)?.accessToken as string;

  const [questionText, setQuestionText] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { data: idea, isLoading } = useSWR<SharedIdeaDetail>(
    session ? `/api/v1/shared/ideas/${ideaId}` : null,
    (url) => apiFetch(url, { token })
  );

  const { data: questions, mutate: mutateQ } = useSWR<Question[]>(
    session ? `/api/v1/shared/ideas/${ideaId}/questions` : null,
    (url) => apiFetch(url, { token })
  );

  const { data: allAnswers, mutate: mutateA } = useSWR<Record<string, Answer[]>>(
    questions ? `answers-${ideaId}` : null,
    async () => {
      const map: Record<string, Answer[]> = {};
      for (const q of questions ?? []) {
        map[q.id] = await apiFetch(`/api/v1/questions/${q.id}/answers`, { token });
      }
      return map;
    }
  );

  const handleAskQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!questionText.trim()) return;
    setSubmitting(true);
    try {
      await apiFetch(`/api/v1/shared/ideas/${ideaId}/questions`, {
        method: "POST",
        token,
        body: JSON.stringify({ question_text: questionText }),
      });
      setQuestionText("");
      mutateQ();
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading) return <div className="p-8 text-muted-foreground">Loading...</div>;
  if (!idea) return <div className="p-8 text-muted-foreground">Idea not found.</div>;

  return (
    <div className="max-w-3xl mx-auto p-8 space-y-8">
      <div>
        <Link href="/shared" className="text-sm text-muted-foreground hover:text-foreground">
          &larr; All shared ideas
        </Link>
      </div>

      <div className="space-y-3">
        <div className="flex items-start justify-between">
          <h1 className="text-2xl font-bold">{idea.title}</h1>
          <span className={`text-xs px-2 py-1 rounded-full ${STATUS_COLORS[idea.status] ?? ""}`}>
            {idea.status}
          </span>
        </div>
        <p className="text-muted-foreground">{idea.description}</p>
        {idea.deadline && (
          <p className="text-sm text-muted-foreground">
            Deadline: {new Date(idea.deadline).toLocaleDateString()}
          </p>
        )}
        <ShareabilityMeter index={idea.shareability_index} label="Shareability" />
      </div>

      {/* Components */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Components</h2>
        {idea.components.length === 0 ? (
          <p className="text-sm text-muted-foreground">No components visible at your access tier.</p>
        ) : (
          <div className="space-y-3">
            {idea.components.map((comp) => (
              <div key={comp.id} className="border rounded-lg p-4 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{comp.name}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${PRIORITY_COLORS[comp.priority] ?? ""}`}>
                    {comp.priority.replace("_", " ")}
                  </span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${STATUS_COLORS[comp.status] ?? ""}`}>
                    {comp.status.replace("_", " ")}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">{comp.description}</p>
                {comp.deadline && (
                  <p className="text-xs text-muted-foreground">
                    Due: {new Date(comp.deadline).toLocaleDateString()}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Q&A */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Questions</h2>

        <form onSubmit={handleAskQuestion} className="mb-6 space-y-2">
          <textarea
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
            placeholder="Ask a question about this idea..."
            rows={2}
            className="w-full px-3 py-2 border rounded-md text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button
            type="submit"
            disabled={submitting || !questionText.trim()}
            className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            Ask Question
          </button>
        </form>

        {!questions || questions.length === 0 ? (
          <p className="text-sm text-muted-foreground">No questions yet.</p>
        ) : (
          <div className="space-y-4">
            {questions.map((q) => (
              <QuestionThread
                key={q.id}
                question={q}
                answers={allAnswers?.[q.id] ?? []}
                token={token}
                onUpdate={() => { mutateQ(); mutateA(); }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
