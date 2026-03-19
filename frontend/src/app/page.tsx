import Link from "next/link";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";

export default async function HomePage() {
  const session = await getServerSession(authOptions);

  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <header className="border-b">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="font-bold text-xl tracking-tight">Cereborate</span>
          <nav className="flex items-center gap-4">
            {session ? (
              <Link
                href="/plan"
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90"
              >
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-sm text-muted-foreground hover:text-foreground"
                >
                  Sign in
                </Link>
                <Link
                  href="/register"
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90"
                >
                  Get Started Free
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 pt-24 pb-16 text-center">
        <h1 className="text-5xl font-bold tracking-tight mb-6">
          Think together.{" "}
          <span className="text-primary">Share smart.</span>
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
          Cereborate turns raw ideas into structured, shareable knowledge.
          AI-powered planning, an intelligent dependency graph, and tier-based
          shareability — all in one platform.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {session ? (
            <Link
              href="/plan"
              className="px-8 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90"
            >
              Go to Dashboard
            </Link>
          ) : (
            <>
              <Link
                href="/register"
                className="px-8 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90"
              >
                Start for free
              </Link>
              <Link
                href="/login"
                className="px-8 py-3 border rounded-lg font-medium hover:bg-muted"
              >
                Sign in
              </Link>
            </>
          )}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 pb-24">
        <div className="grid md:grid-cols-3 gap-8">
          <FeatureCard
            icon="🤖"
            title="AI-Powered Planning"
            description="Chat your ideas into existence. The LLM backbone extracts structure from natural conversation — components, budgets, deadlines — and turns them into a working plan."
          />
          <FeatureCard
            icon="🕸️"
            title="Knowledge Graph"
            description="Ideas don't exist in isolation. Cereborate detects semantic links between ideas, builds a component dependency DAG, and surfaces cross-team shared surface area automatically."
          />
          <FeatureCard
            icon="🔒"
            title="Smart Shareability"
            description="Every component gets an LLM-scored shareability index. Tier-based access control means each team member sees exactly what they need — nothing more, nothing less."
          />
        </div>
      </section>

      {/* How it works */}
      <section className="bg-muted/40 py-20">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">How it works</h2>
          <div className="space-y-8">
            {[
              {
                step: "1",
                title: "Capture your idea",
                desc: "Chat with the AI or fill in a structured form. The planning engine asks follow-up questions to extract every detail.",
              },
              {
                step: "2",
                title: "The Brain takes over",
                desc: "Embeddings link your idea to related work. Dependencies are detected across your team's components. Consistency flags surface conflicts early.",
              },
              {
                step: "3",
                title: "Share on your terms",
                desc: "Set shareability tiers per component. Cross-idea dependencies auto-expose the right surface area. Teams collaborate without oversharing.",
              },
            ].map(({ step, title, desc }) => (
              <div key={step} className="flex gap-6 items-start">
                <div className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg shrink-0">
                  {step}
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-1">{title}</h3>
                  <p className="text-muted-foreground">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      {!session && (
        <section className="max-w-2xl mx-auto px-6 py-24 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to think together?</h2>
          <p className="text-muted-foreground mb-8">
            Free to start. No credit card required.
          </p>
          <Link
            href="/register"
            className="px-10 py-4 bg-primary text-primary-foreground rounded-lg font-semibold text-lg hover:bg-primary/90"
          >
            Create your workspace
          </Link>
        </section>
      )}

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between text-sm text-muted-foreground">
          <span>© 2026 Cereborate. All rights reserved.</span>
          <span>Think together. Share smart.</span>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border bg-card p-6 space-y-3">
      <div className="text-3xl">{icon}</div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
    </div>
  );
}
