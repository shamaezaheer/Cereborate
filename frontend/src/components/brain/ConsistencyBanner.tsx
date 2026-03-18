"use client";

import { useState } from "react";
import useSWR from "swr";
import { useSession } from "next-auth/react";
import { apiFetch } from "@/lib/api";

interface ConsistencyFlag {
  id: string;
  severity: "info" | "warning" | "critical";
  flag_type: string;
  description: string;
  resolved: boolean;
}

interface Props {
  ideaId: string;
}

const severityStyles = {
  info: "bg-blue-50 border-blue-200 text-blue-800",
  warning: "bg-yellow-50 border-yellow-200 text-yellow-800",
  critical: "bg-red-50 border-red-200 text-red-800",
};

export function ConsistencyBanner({ ideaId }: Props) {
  const { data: authSession } = useSession();
  const [expanded, setExpanded] = useState(false);

  const { data: flags, mutate } = useSWR<ConsistencyFlag[]>(
    authSession ? `/api/v1/ideas/${ideaId}/consistency` : null,
    (url) => apiFetch(url, { token: (authSession as any)?.accessToken })
  );

  const unresolvedFlags = flags?.filter((f) => !f.resolved) ?? [];

  if (unresolvedFlags.length === 0) return null;

  const worstSeverity = unresolvedFlags.some((f) => f.severity === "critical")
    ? "critical"
    : unresolvedFlags.some((f) => f.severity === "warning")
    ? "warning"
    : "info";

  async function resolve(flagId: string) {
    await apiFetch(`/api/v1/consistency/${flagId}/resolve`, {
      method: "PATCH",
      token: (authSession as any)?.accessToken,
      body: JSON.stringify({ resolved: true }),
    });
    mutate();
  }

  return (
    <div className={`border rounded-lg p-3 mb-4 ${severityStyles[worstSeverity]}`}>
      <button
        className="flex items-center justify-between w-full"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="font-medium text-sm">
          {unresolvedFlags.length} advisory flag{unresolvedFlags.length !== 1 ? "s" : ""}
        </span>
        <span className="text-xs">{expanded ? "▲ Hide" : "▼ Show"}</span>
      </button>

      {expanded && (
        <ul className="mt-3 space-y-2">
          {unresolvedFlags.map((flag) => (
            <li key={flag.id} className="flex items-start justify-between gap-2">
              <div>
                <span className="text-xs font-mono opacity-70">{flag.flag_type}</span>
                <p className="text-sm mt-0.5">{flag.description}</p>
              </div>
              <button
                onClick={() => resolve(flag.id)}
                className="text-xs underline shrink-0 opacity-70 hover:opacity-100"
              >
                Resolve
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
