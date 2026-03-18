"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut } from "next-auth/react";

const navItems = [
  { href: "/plan", label: "New Plan" },
  { href: "/ideas", label: "My Ideas" },
  { href: "/shared", label: "Shared Ideas" },
  { href: "/dependencies", label: "Dependencies" },
  { href: "/questions", label: "Q&A" },
  { href: "/notifications", label: "Notifications" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 h-screen bg-card border-r flex flex-col">
      <div className="p-4 border-b">
        <h1 className="font-bold text-lg text-primary">Cereborate</h1>
        <p className="text-xs text-muted-foreground">Think together. Share smart.</p>
      </div>

      <nav className="flex-1 p-2 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`block px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              pathname.startsWith(item.href)
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="p-2 border-t">
        <button
          onClick={() => signOut({ callbackUrl: "/login" })}
          className="w-full px-3 py-2 text-sm text-muted-foreground hover:text-foreground rounded-md hover:bg-muted text-left"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
