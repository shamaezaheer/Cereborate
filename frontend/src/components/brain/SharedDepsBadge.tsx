"use client";

interface SharedDepsBadgeProps {
  count: number;
}

export function SharedDepsBadge({ count }: SharedDepsBadgeProps) {
  if (count === 0) return null;

  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800 dark:bg-purple-900 dark:text-purple-200">
      {count} shared dep{count !== 1 ? "s" : ""}
    </span>
  );
}
