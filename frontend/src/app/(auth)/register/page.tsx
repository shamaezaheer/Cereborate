"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { signIn } from "next-auth/react";

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const formData = new FormData(e.currentTarget);
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    try {
      await apiFetch("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          display_name: formData.get("display_name"),
          tenant_name: formData.get("tenant_name"),
          tenant_slug: formData.get("tenant_slug"),
        }),
      });

      // Auto sign in after registration
      await signIn("credentials", { email, password, redirect: false });
      router.push("/plan");
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-8 space-y-6 border rounded-lg shadow-sm">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Create your workspace</h1>
          <p className="text-muted-foreground mt-1">Set up Cereborate for your team</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="display_name" className="block text-sm font-medium mb-1">
              Your name
            </label>
            <input
              id="display_name"
              name="display_name"
              type="text"
              required
              className="w-full px-3 py-2 border rounded-md bg-background text-foreground"
              placeholder="Jane Smith"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              className="w-full px-3 py-2 border rounded-md bg-background text-foreground"
              placeholder="jane@company.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-1">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              minLength={8}
              className="w-full px-3 py-2 border rounded-md bg-background text-foreground"
              placeholder="••••••••"
            />
          </div>

          <div className="border-t pt-4">
            <p className="text-sm font-medium mb-3">Workspace details</p>
            <div className="space-y-3">
              <div>
                <label htmlFor="tenant_name" className="block text-sm font-medium mb-1">
                  Workspace name
                </label>
                <input
                  id="tenant_name"
                  name="tenant_name"
                  type="text"
                  required
                  className="w-full px-3 py-2 border rounded-md bg-background text-foreground"
                  placeholder="Acme Corp"
                />
              </div>
              <div>
                <label htmlFor="tenant_slug" className="block text-sm font-medium mb-1">
                  Workspace URL
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground text-sm">cereborate.io/</span>
                  <input
                    id="tenant_slug"
                    name="tenant_slug"
                    type="text"
                    required
                    pattern="[a-z0-9-]+"
                    className="flex-1 px-3 py-2 border rounded-md bg-background text-foreground"
                    placeholder="acme-corp"
                  />
                </div>
              </div>
            </div>
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 bg-primary text-primary-foreground rounded-md font-medium disabled:opacity-50"
          >
            {loading ? "Creating workspace..." : "Create workspace"}
          </button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
