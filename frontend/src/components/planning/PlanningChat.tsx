"use client";

import { useEffect, useRef, useState } from "react";
import { PlanningWebSocket } from "@/lib/ws";
import type { PlanningSession } from "@/types/planning";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Props {
  session: PlanningSession;
  token: string;
  onComplete: (sessionId: string) => void;
  onExtractedUpdate: (data: PlanningSession["extracted_data"]) => void;
}

export function PlanningChat({ session, token, onComplete, onExtractedUpdate }: Props) {
  const [messages, setMessages] = useState<Message[]>(
    session.conversation_history as Message[]
  );
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const wsRef = useRef<PlanningWebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ws = new PlanningWebSocket(
      session.id,
      token,
      (msg) => {
        if (msg.type === "message") {
          setMessages((prev) => [...prev, { role: "assistant", content: msg.content }]);
          onExtractedUpdate(msg.extracted as PlanningSession["extracted_data"]);
          if (msg.is_complete) setIsComplete(true);
          setIsLoading(false);
        }
      },
      () => setIsLoading(false)
    );
    ws.connect();
    wsRef.current = ws;
    return () => ws.disconnect();
  }, [session.id, token]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function sendMessage() {
    if (!input.trim() || isLoading) return;
    const msg = input.trim();
    setInput("");
    setIsLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    wsRef.current?.send(msg);
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-lg p-3 text-sm ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-foreground"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg p-3 text-sm text-muted-foreground">
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t p-4 space-y-2">
        {isComplete && (
          <button
            onClick={() => onComplete(session.id)}
            className="w-full py-2 bg-green-600 text-white rounded-md text-sm font-medium"
          >
            Create Idea
          </button>
        )}
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
            placeholder="Describe your idea..."
            disabled={isLoading}
            className="flex-1 px-3 py-2 border rounded-md text-sm bg-background disabled:opacity-50"
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
