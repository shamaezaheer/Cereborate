"use client";

import useSWR from "swr";
import { useSession } from "next-auth/react";
import { apiFetch } from "@/lib/api";
import type { Notification } from "@/types/team";

const EVENT_ICONS: Record<string, string> = {
  linked_idea_updated: "🔗",
  dependency_cleared: "✅",
  shareability_changed: "🔒",
  question_answered: "💬",
  cross_idea_dep_detected: "⚡",
};

export default function NotificationsPage() {
  const { data: session } = useSession();
  const token = (session as any)?.accessToken as string;

  const { data: notifications, mutate, isLoading } = useSWR<Notification[]>(
    session ? "/api/v1/notifications" : null,
    (url) => apiFetch(url, { token })
  );

  const handleMarkRead = async (id: string) => {
    await apiFetch(`/api/v1/notifications/${id}/read`, {
      method: "PATCH",
      token,
    });
    mutate();
  };

  const handleMarkAllRead = async () => {
    const unread = (notifications ?? []).filter((n) => !n.read);
    await Promise.all(
      unread.map((n) =>
        apiFetch(`/api/v1/notifications/${n.id}/read`, {
          method: "PATCH",
          token,
        })
      )
    );
    mutate();
  };

  const unreadCount = (notifications ?? []).filter((n) => !n.read).length;

  return (
    <div className="max-w-2xl mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Notifications</h1>
          {unreadCount > 0 && (
            <p className="text-sm text-muted-foreground mt-1">
              {unreadCount} unread
            </p>
          )}
        </div>
        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllRead}
            className="text-sm text-primary hover:underline"
          >
            Mark all read
          </button>
        )}
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : !notifications || notifications.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-lg">All caught up!</p>
          <p className="text-sm mt-2">
            Notifications appear here when linked ideas update or dependencies change.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((notif) => (
            <div
              key={notif.id}
              className={`flex items-start gap-3 rounded-lg border p-4 transition-colors ${
                !notif.read ? "bg-blue-50 border-blue-200" : "bg-background"
              }`}
            >
              <span className="text-xl shrink-0 mt-0.5">
                {EVENT_ICONS[notif.event_type] ?? "🔔"}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm">{notif.message}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {new Date(notif.created_at).toLocaleString()}
                </p>
              </div>
              {!notif.read && (
                <button
                  onClick={() => handleMarkRead(notif.id)}
                  className="text-xs text-muted-foreground hover:text-foreground shrink-0"
                >
                  Mark read
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
