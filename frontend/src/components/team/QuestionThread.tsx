"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";
import type { Answer, Question } from "@/types/team";

interface QuestionThreadProps {
  question: Question;
  answers: Answer[];
  token: string;
  isOwner?: boolean;
  onUpdate?: () => void;
}

export function QuestionThread({
  question,
  answers,
  token,
  isOwner = false,
  onUpdate,
}: QuestionThreadProps) {
  const [replyText, setReplyText] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim()) return;
    setSubmitting(true);
    try {
      await apiFetch(`/api/v1/questions/${question.id}/answers`, {
        method: "POST",
        token,
        body: JSON.stringify({ answer_text: replyText }),
      });
      setReplyText("");
      onUpdate?.();
    } finally {
      setSubmitting(false);
    }
  };

  const handleRequestAI = async () => {
    setSubmitting(true);
    try {
      await apiFetch(`/api/v1/questions/${question.id}/answers/ai`, {
        method: "POST",
        token,
      });
      onUpdate?.();
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async (answerId: string) => {
    await apiFetch(`/api/v1/answers/${answerId}/approve`, {
      method: "PATCH",
      token,
    });
    onUpdate?.();
  };

  const statusColors: Record<string, string> = {
    open: "text-yellow-600",
    answered: "text-green-600",
    closed: "text-gray-500",
  };

  return (
    <div className="border rounded-lg p-4 space-y-4">
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <p className="font-medium">{question.question_text}</p>
          <span className={`text-xs font-medium ${statusColors[question.status]}`}>
            {question.status}
          </span>
        </div>
        <p className="text-xs text-muted-foreground">
          {new Date(question.created_at).toLocaleDateString()}
        </p>
      </div>

      {answers.length > 0 && (
        <div className="space-y-3 pl-4 border-l">
          {answers.map((answer) => (
            <div key={answer.id} className="space-y-1">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm">{answer.answer_text}</p>
                <div className="flex items-center gap-2 shrink-0">
                  {answer.is_ai_generated && (
                    <span className="text-xs bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">
                      AI
                    </span>
                  )}
                  {answer.is_ai_generated && !answer.approved && isOwner && (
                    <button
                      onClick={() => handleApprove(answer.id)}
                      className="text-xs text-green-600 hover:underline"
                    >
                      Approve
                    </button>
                  )}
                  {answer.is_ai_generated && !answer.approved && !isOwner && (
                    <span className="text-xs text-orange-500">Pending approval</span>
                  )}
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                {new Date(answer.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-2">
        <textarea
          value={replyText}
          onChange={(e) => setReplyText(e.target.value)}
          placeholder="Write an answer..."
          rows={2}
          className="w-full px-3 py-2 border rounded-md text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={submitting || !replyText.trim()}
            className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            Answer
          </button>
          <button
            type="button"
            onClick={handleRequestAI}
            disabled={submitting}
            className="px-3 py-1.5 text-sm border rounded-md hover:bg-muted disabled:opacity-50"
          >
            Ask AI
          </button>
        </div>
      </form>
    </div>
  );
}
