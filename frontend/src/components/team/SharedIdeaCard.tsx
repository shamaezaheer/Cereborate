"use client";

import Link from "next/link";
import { ShareabilityMeter } from "@/components/brain/ShareabilityMeter";
import { SharedDepsBadge } from "@/components/brain/SharedDepsBadge";
import type { SharedIdea } from "@/types/team";

interface SharedIdeaCardProps {
  idea: SharedIdea;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  active: "bg-green-100 text-green-700",
  archived: "bg-red-100 text-red-700",
};

export function SharedIdeaCard({ idea }: SharedIdeaCardProps) {
  return (
    <div className="rounded-lg border bg-card p-5 space-y-3 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <Link
          href={`/shared/${idea.id}`}
          className="font-semibold text-lg hover:underline"
        >
          {idea.title}
        </Link>
        <div className="flex items-center gap-2 shrink-0">
          <span
            className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[idea.status] ?? "bg-gray-100 text-gray-700"}`}
          >
            {idea.status}
          </span>
          <SharedDepsBadge count={idea.shared_dep_count} />
        </div>
      </div>

      <p className="text-sm text-muted-foreground line-clamp-2">
        {idea.description}
      </p>

      <ShareabilityMeter index={idea.shareability_index} label="Shareability" />

      <div className="flex gap-3 pt-1 text-sm">
        <Link
          href={`/shared/${idea.id}`}
          className="text-primary hover:underline"
        >
          View idea →
        </Link>
        {idea.shared_dep_count > 0 && (
          <Link
            href={`/shared/${idea.id}/dependencies`}
            className="text-muted-foreground hover:text-foreground hover:underline"
          >
            Shared deps
          </Link>
        )}
      </div>
    </div>
  );
}
