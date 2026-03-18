"use client";

import useSWR from "swr";
import { useSession } from "next-auth/react";
import { apiFetch } from "@/lib/api";
import { QuestionThread } from "@/components/team/QuestionThread";
import type { Answer, Question, SharedIdea } from "@/types/team";

export default function QuestionsPage() {
  const { data: session } = useSession();
  const token = (session as any)?.accessToken as string;

  // Fetch all shared ideas first, then aggregate questions
  const { data: ideas } = useSWR<SharedIdea[]>(
    session ? "/api/v1/shared/ideas" : null,
    (url) => apiFetch(url, { token })
  );

  const { data: allQuestions, mutate } = useSWR<Question[]>(
    ideas ? `all-questions-${ideas.map((i) => i.id).join(",")}` : null,
    async () => {
      const results: Question[] = [];
      for (const idea of ideas ?? []) {
        const qs: Question[] = await apiFetch(
          `/api/v1/shared/ideas/${idea.id}/questions`,
          { token }
        );
        results.push(...qs);
      }
      return results;
    }
  );

  const { data: answerMap, mutate: mutateAnswers } = useSWR<Record<string, Answer[]>>(
    allQuestions ? `answers-all-${allQuestions.map((q) => q.id).join(",")}` : null,
    async () => {
      const map: Record<string, Answer[]> = {};
      for (const q of allQuestions ?? []) {
        map[q.id] = await apiFetch(`/api/v1/questions/${q.id}/answers`, { token });
      }
      return map;
    }
  );

  const handleUpdate = () => {
    mutate();
    mutateAnswers();
  };

  const openQuestions = allQuestions?.filter((q) => q.status === "open") ?? [];
  const answeredQuestions = allQuestions?.filter((q) => q.status !== "open") ?? [];

  return (
    <div className="max-w-3xl mx-auto p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold mb-2">Questions</h1>
        <p className="text-muted-foreground text-sm">
          All questions across shared ideas you have access to.
        </p>
      </div>

      {!allQuestions ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : allQuestions.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-lg">No questions yet.</p>
          <p className="text-sm mt-2">
            Visit a shared idea to ask the first question.
          </p>
        </div>
      ) : (
        <>
          {openQuestions.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold mb-3">
                Open ({openQuestions.length})
              </h2>
              <div className="space-y-4">
                {openQuestions.map((q) => (
                  <QuestionThread
                    key={q.id}
                    question={q}
                    answers={answerMap?.[q.id] ?? []}
                    token={token}
                    onUpdate={handleUpdate}
                  />
                ))}
              </div>
            </section>
          )}

          {answeredQuestions.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold mb-3">
                Answered ({answeredQuestions.length})
              </h2>
              <div className="space-y-4">
                {answeredQuestions.map((q) => (
                  <QuestionThread
                    key={q.id}
                    question={q}
                    answers={answerMap?.[q.id] ?? []}
                    token={token}
                    onUpdate={handleUpdate}
                  />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
