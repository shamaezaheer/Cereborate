# CLAUDE.md — Cereborate

> **Cereborate** is a structured ideation-to-collaboration platform with an LLM backbone.
> It captures ideas through conversational AI or GUI, stores and links them in an intelligent
> knowledge graph, enforces shareability controls, and exposes a team collaboration interface.

---

## PROJECT IDENTITY

- **Name:** Cereborate
- **Tagline:** "Think together. Share smart."
- **Type:** Multi-tenant SaaS platform
- **License:** Proprietary (all rights reserved)

---

## HIGH-LEVEL ARCHITECTURE

Cereborate has three distinct layers:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     LAYER 1: PLANNING INTERFACE                     │
│                                                                     │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│   │   Web GUI     │    │   CLI (REPL)  │    │  API (headless)     │  │
│   │  React + Next │    │  Rich/Typer   │    │  REST/WebSocket     │  │
│   └──────┬───────┘    └──────┬───────┘    └──────────┬───────────┘  │
│          │                   │                       │              │
│          └───────────┬───────┴───────────────────────┘              │
│                      ▼                                              │
│          ┌───────────────────────┐                                  │
│          │  Planning Service     │                                  │
│          │  (FastAPI)            │                                  │
│          │  - Idea intake        │                                  │
│          │  - Follow-up engine   │                                  │
│          │  - Budget/deadline    │                                  │
│          │  - Component breakdown│                                  │
│          └───────────┬───────────┘                                  │
│                      │                                              │
├──────────────────────┼──────────────────────────────────────────────┤
│                      ▼                                              │
│                 LAYER 2: THE BRAIN                                  │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  Knowledge Engine (FastAPI service)                          │  │
│   │                                                              │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │  │
│   │  │ PostgreSQL   │  │ pgvector    │  │ Redis               │  │  │
│   │  │ (structured  │  │ (embeddings │  │ (sessions, cache,   │  │  │
│   │  │  idea data)  │  │  & linking) │  │  job queue)         │  │  │
│   │  └─────────────┘  └─────────────┘  └─────────────────────┘  │  │
│   │                                                              │  │
│   │  Core Capabilities:                                          │  │
│   │  - Idea storage & versioning                                 │  │
│   │  - Cross-idea linking (semantic similarity via embeddings)   │  │
│   │  - Component dependency graph (DAG, within + across ideas)   │  │
│   │  - Auto-exposure of shared dependencies to relevant teams    │  │
│   │  - Consistency checking (advisory, LLM-powered)              │  │
│   │  - Shareability index computation                            │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                      │                                              │
├──────────────────────┼──────────────────────────────────────────────┤
│                      ▼                                              │
│               LAYER 3: TEAM INTERFACE                               │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  Collaboration Portal (React + Next.js)                      │  │
│   │                                                              │  │
│   │  - Browse shared ideas (filtered by access level)            │  │
│   │  - View shared dependencies across ideas                     │  │
│   │  - Ask questions on idea components                          │  │
│   │  - View shareability-gated detail levels                     │  │
│   │  - Comment threads & discussion                              │  │
│   │  - Notification system for linked idea updates               │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│                    LLM BACKBONE (SHARED)                            │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  Ollama (local) / vLLM (cloud)                               │  │
│   │  Models:                                                     │  │
│   │  - Qwen3-8B: conversational planning, consistency checks     │  │
│   │  - Qwen3-1.7B: classification (shareability scoring)         │  │
│   │  - nomic-embed-text: embedding generation for linking        │  │
│   └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## TECH STACK

| Component               | Technology                        | Rationale                                         |
|--------------------------|-----------------------------------|----------------------------------------------------|
| Backend API              | Python 3.12 + FastAPI             | Async-native, great LLM ecosystem, type-safe       |
| Frontend (GUI + Portal)  | Next.js 14 (App Router) + React   | SSR, shared component library, one framework       |
| CLI                      | Python (Typer + Rich)             | Beautiful terminal UI, shares backend logic         |
| Database                 | PostgreSQL 16 + pgvector          | Production-grade, native vector search, JSONB       |
| Cache / Queue            | Redis 7                           | Session store, Celery broker, real-time pubsub      |
| Task Queue               | Celery                            | Async LLM jobs, consistency checks, reindexing      |
| LLM Runtime (local)      | Ollama                            | Simple local model management, good Mac support     |
| LLM Runtime (cloud)      | vLLM                              | Swap in for production — same OpenAI-compat API     |
| Embeddings               | nomic-embed-text (via Ollama)     | High quality, runs locally, 768-dim vectors         |
| Auth                     | NextAuth.js + JWT                 | Multi-tenant SaaS auth with role-based access       |
| Container                | Docker Compose (local + cloud)    | Reproducible dev/prod environments                  |
| Migrations               | Alembic                           | SQLAlchemy-based, version-controlled schema         |

---

## DIRECTORY STRUCTURE

```
cereborate/
├── CLAUDE.md                          # This file
├── docker-compose.yml                 # Full stack orchestration
├── docker-compose.dev.yml             # Dev overrides (hot reload, debug)
├── .env.example                       # Environment template
├── Makefile                           # Common commands
│
├── backend/                           # Python FastAPI monorepo
│   ├── pyproject.toml                 # Poetry/uv project config
│   ├── alembic/                       # Database migrations
│   │   ├── alembic.ini
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app factory
│   │   ├── config.py                  # Pydantic Settings (env-driven)
│   │   ├── deps.py                    # Dependency injection (db, llm, auth)
│   │   │
│   │   ├── models/                    # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Base model with tenant_id, timestamps
│   │   │   ├── user.py               # User, Role, TenantMembership
│   │   │   ├── idea.py               # Idea, IdeaVersion, IdeaComponent
│   │   │   ├── budget.py             # Budget, BudgetLineItem
│   │   │   ├── shareability.py       # ShareabilityRule, AccessGrant
│   │   │   ├── link.py               # IdeaLink (cross-idea relationships)
│   │   │   ├── consistency.py        # ConsistencyFlag (advisory warnings)
│   │   │   ├── dependency.py        # ComponentDependency, cross-idea deps
│   │   │   └── discussion.py         # Question, Answer, Comment
│   │   │
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── idea.py
│   │   │   ├── planning.py           # Planning session schemas
│   │   │   ├── dependency.py         # Dependency + shared view schemas
│   │   │   ├── shareability.py
│   │   │   ├── team.py
│   │   │   └── auth.py
│   │   │
│   │   ├── api/                       # Route handlers
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py          # Aggregated v1 router
│   │   │   │   ├── planning.py        # POST /plan/start, /plan/respond
│   │   │   │   ├── ideas.py           # CRUD for ideas
│   │   │   │   ├── components.py      # Idea component management
│   │   │   │   ├── dependencies.py   # Component dependency CRUD + graph
│   │   │   │   ├── budget.py          # Budget endpoints
│   │   │   │   ├── shareability.py    # Shareability config endpoints
│   │   │   │   ├── team.py            # Team member views, Q&A
│   │   │   │   ├── links.py           # Cross-idea link management
│   │   │   │   ├── consistency.py     # Consistency flag review
│   │   │   │   └── auth.py            # Login, register, tenant mgmt
│   │   │   └── ws/
│   │   │       └── planning.py        # WebSocket for real-time planning chat
│   │   │
│   │   ├── services/                  # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── planning_service.py    # Orchestrates idea intake flow
│   │   │   ├── llm_service.py         # Ollama/vLLM abstraction layer
│   │   │   ├── embedding_service.py   # Vector generation & similarity
│   │   │   ├── linking_service.py     # Cross-idea link detection
│   │   │   ├── dependency_service.py # Component deps, DAG validation, auto-exposure
│   │   │   ├── consistency_service.py # Advisory consistency checker
│   │   │   ├── shareability_service.py# Shareability index computation
│   │   │   ├── question_service.py    # Team Q&A with access filtering
│   │   │   └── notification_service.py# Alerts for linked idea changes
│   │   │
│   │   ├── llm/                       # LLM integration layer
│   │   │   ├── __init__.py
│   │   │   ├── client.py             # Unified client (Ollama local / vLLM cloud)
│   │   │   ├── prompts/              # Jinja2 prompt templates
│   │   │   │   ├── planning_intake.j2
│   │   │   │   ├── follow_up.j2
│   │   │   │   ├── consistency_check.j2
│   │   │   │   ├── shareability_score.j2
│   │   │   │   ├── link_detection.j2
│   │   │   │   ├── dependency_detection.j2
│   │   │   │   └── question_answer.j2
│   │   │   └── schemas.py            # Structured output schemas for LLM
│   │   │
│   │   └── tasks/                     # Celery async tasks
│   │       ├── __init__.py
│   │       ├── celery_app.py
│   │       ├── consistency_tasks.py   # Background consistency sweeps
│   │       ├── linking_tasks.py       # Re-index embeddings, find new links
│   │       ├── dependency_tasks.py    # Cross-idea dep discovery, DAG validation
│   │       └── notification_tasks.py
│   │
│   ├── cli/                           # CLI application
│   │   ├── __init__.py
│   │   ├── main.py                    # Typer app entry point
│   │   ├── plan_cmd.py               # `cereborate plan` — interactive planning
│   │   ├── ideas_cmd.py              # `cereborate ideas list/show/delete`
│   │   ├── team_cmd.py               # `cereborate team invite/list`
│   │   └── config_cmd.py             # `cereborate config set-model/set-url`
│   │
│   └── tests/
│       ├── conftest.py               # Fixtures: test DB, mock LLM
│       ├── test_planning.py
│       ├── test_consistency.py
│       ├── test_shareability.py
│       └── test_linking.py
│
├── frontend/                          # Next.js 14 monorepo
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   │
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx             # Root layout with auth provider
│   │   │   ├── page.tsx               # Landing / dashboard
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   ├── (planner)/             # Layer 1: Planning Interface
│   │   │   │   ├── plan/
│   │   │   │   │   ├── page.tsx       # Start new plan
│   │   │   │   │   └── [sessionId]/
│   │   │   │   │       └── page.tsx   # Active planning session (chat + form)
│   │   │   │   └── ideas/
│   │   │   │       ├── page.tsx       # My ideas list
│   │   │   │       └── [ideaId]/
│   │   │   │           ├── page.tsx   # Idea detail (owner view, full access)
│   │   │   │           ├── components/page.tsx
│   │   │   │           ├── budget/page.tsx
│   │   │   │           ├── links/page.tsx
│   │   │   │           ├── dependencies/page.tsx   # Component dependency graph
│   │   │   │           └── shareability/page.tsx
│   │   │   ├── (team)/                # Layer 3: Team Interface
│   │   │   │   ├── shared/
│   │   │   │   │   ├── page.tsx       # Browse shared ideas (filtered)
│   │   │   │   │   └── [ideaId]/
│   │   │   │   │       ├── page.tsx   # Shared idea view (access-gated)
│   │   │   │   │       └── dependencies/page.tsx  # Cross-idea shared deps
│   │   │   │   ├── dependencies/
│   │   │   │   │   └── page.tsx       # All shared dependencies affecting my ideas
│   │   │   │   ├── questions/
│   │   │   │   │   └── page.tsx       # Q&A feed
│   │   │   │   └── notifications/
│   │   │   │       └── page.tsx
│   │   │   └── (admin)/
│   │   │       ├── tenant/page.tsx    # Tenant settings
│   │   │       └── members/page.tsx   # Member + access management
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui base components
│   │   │   ├── planning/
│   │   │   │   ├── PlanningChat.tsx   # Chat-based idea intake
│   │   │   │   ├── IdeaForm.tsx       # Structured form (toggle from chat)
│   │   │   │   ├── ComponentBuilder.tsx
│   │   │   │   ├── BudgetTable.tsx
│   │   │   │   └── DeadlinePicker.tsx
│   │   │   ├── brain/
│   │   │   │   ├── ConsistencyBanner.tsx  # Advisory warning banner
│   │   │   │   ├── LinkGraph.tsx          # D3/Force graph of linked ideas
│   │   │   │   ├── DependencyGraph.tsx    # DAG visualization of component deps
│   │   │   │   ├── SharedDepsBadge.tsx    # Badge showing cross-idea dep count
│   │   │   │   └── ShareabilityMeter.tsx  # Visual index display
│   │   │   ├── team/
│   │   │   │   ├── SharedIdeaCard.tsx
│   │   │   │   ├── QuestionThread.tsx
│   │   │   │   └── AccessBadge.tsx
│   │   │   └── layout/
│   │   │       ├── Sidebar.tsx
│   │   │       ├── TopBar.tsx
│   │   │       └── ModeToggle.tsx     # GUI ↔ Chat toggle
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts                 # Fetch wrapper for backend
│   │   │   ├── ws.ts                  # WebSocket client for planning
│   │   │   ├── auth.ts                # NextAuth config
│   │   │   └── shareability.ts        # Client-side access helpers
│   │   │
│   │   └── types/
│   │       ├── idea.ts
│   │       ├── dependency.ts          # ComponentDependency, SharedDepView
│   │       ├── planning.ts
│   │       ├── team.ts
│   │       └── shareability.ts
│   │
│   └── public/
│       └── assets/
│
└── infra/
    ├── ollama/
    │   └── modelfile                  # Pre-pull script for required models
    ├── postgres/
    │   └── init.sql                   # Enable pgvector extension
    └── nginx/
        └── nginx.conf                 # Reverse proxy (production)
```

---

## DATA MODELS (Core Schema)

### Tenant & Auth

```
Tenant
  id: UUID (PK)
  name: str
  slug: str (unique)
  plan: enum(free, pro, enterprise)
  created_at: datetime

User
  id: UUID (PK)
  email: str (unique)
  password_hash: str
  display_name: str
  created_at: datetime

TenantMembership
  id: UUID (PK)
  tenant_id: FK(Tenant)
  user_id: FK(User)
  role: enum(owner, admin, member, viewer)
  access_tier: int (1-10, controls shareability access)
  invited_at: datetime
```

### Ideas (Layer 1 + Layer 2)

```
Idea
  id: UUID (PK)
  tenant_id: FK(Tenant)
  creator_id: FK(User)
  title: str
  description: text
  status: enum(draft, active, archived)
  deadline: datetime (nullable)
  total_budget: decimal (nullable)
  budget_currency: str (default "USD")
  embedding: vector(768)              -- pgvector, for cross-idea linking
  version: int (auto-increment)
  created_at: datetime
  updated_at: datetime

IdeaVersion
  id: UUID (PK)
  idea_id: FK(Idea)
  version: int
  snapshot: jsonb                      -- full idea state at this version
  changed_by: FK(User)
  created_at: datetime

IdeaComponent
  id: UUID (PK)
  idea_id: FK(Idea)
  name: str
  description: text
  estimated_cost: decimal (nullable)
  priority: enum(must_have, should_have, nice_to_have)
  status: enum(proposed, approved, in_progress, done)
  deadline: datetime (nullable)
  embedding: vector(768)
  shareability_score: float (0.0-1.0)  -- computed by LLM
  shareability_reason: text
  created_at: datetime
```

### Component Dependencies (Layer 2)

Dependencies are directional edges between components — within the same idea
or across ideas. When a dependency crosses idea boundaries, the shared
components on both sides are automatically exposed to team members involved
in either idea (subject to the higher of the two shareability tiers).

```
ComponentDependency
  id: UUID (PK)
  tenant_id: FK(Tenant)
  source_component_id: FK(IdeaComponent)  -- the component that depends
  target_component_id: FK(IdeaComponent)  -- the component depended upon
  dependency_type: enum(
    blocks,             -- source cannot start until target is done
    requires_output,    -- source needs an artifact/deliverable from target
    shares_resource,    -- both components use the same resource/budget/person
    extends,            -- source builds on top of target
    informed_by         -- soft dependency — target's outcome influences source
  )
  is_cross_idea: bool                     -- computed: source.idea_id != target.idea_id
  llm_detected: bool (default false)      -- true if auto-discovered by LLM
  confirmed: bool (default false)         -- user confirmed/rejected
  llm_rationale: text (nullable)          -- why the LLM thinks this dependency exists
  created_at: datetime

-- CROSS-IDEA DEPENDENCY AUTO-EXPOSURE RULES:
-- When is_cross_idea = true, both the source and target components gain
-- a "shared dependency" flag. The Brain automatically:
--   1. Lowers the effective shareability tier of BOTH components to the
--      LESS restrictive of the two (so both teams can see the shared surface)
--   2. Creates a SharedDependencyView (read-only) for team members of
--      either idea, showing: component name, description, status, deadline,
--      and dependency_type — but NOT budget figures or internal notes
--   3. Notifies owners of both ideas when a cross-idea dependency is detected
--   4. Owner can reject the auto-exposure or manually tighten it back

SharedDependencyView   -- materialized/computed, not a stored table
  dependency_id: FK(ComponentDependency)
  viewer_idea_id: FK(Idea)               -- which idea's team is viewing
  visible_component_id: FK(IdeaComponent) -- the OTHER idea's component
  visible_fields: [name, description, status, deadline, dependency_type]
  excluded_fields: [estimated_cost, internal_notes, shareability_reason]
```

### Dependency Graph Behavior

The dependency graph is a DAG (directed acyclic graph) within and across ideas.
The Brain enforces and validates:

1. **No cycles**: Adding a dependency that creates a circular chain is flagged
   as a critical consistency error (advisory — not blocked, but loud)
2. **Deadline propagation**: If component A blocks component B, and A's deadline
   is after B's deadline, a consistency flag is raised
3. **Cross-idea discovery**: When the LLM detects a new IdeaLink, it also scans
   the components of both ideas for potential dependencies using embedding
   similarity + structured reasoning. Discovered dependencies are added with
   `llm_detected=true, confirmed=false` and surfaced for owner review
4. **Cascade status**: If a blocking dependency's target is marked "done",
   the source component's owner is notified that the blocker is cleared
5. **Shared resource detection**: If two components (same or different ideas)
   reference similar resources (via embedding similarity on description),
   they get a `shares_resource` dependency suggestion

### Shareability (Layer 2)

```
ShareabilityRule
  id: UUID (PK)
  tenant_id: FK(Tenant)
  idea_id: FK(Idea) (nullable — tenant-wide if null)
  component_id: FK(IdeaComponent) (nullable)
  min_access_tier: int (1-10)          -- minimum tier to see this
  classification: enum(public, internal, confidential, restricted)
  auto_classified: bool                -- true if LLM-assigned
  overridden_by: FK(User) (nullable)   -- if manually changed
  created_at: datetime

-- Shareability Index is computed as:
-- shareability_index = weighted_avg(component.shareability_score)
-- weighted by component priority and budget allocation
-- Exposed as a read-only computed field on the Idea
```

### Cross-Idea Links (Layer 2)

```
IdeaLink
  id: UUID (PK)
  tenant_id: FK(Tenant)
  source_idea_id: FK(Idea)
  target_idea_id: FK(Idea)
  link_type: enum(related, depends_on, conflicts_with, extends)
  similarity_score: float              -- cosine similarity from embeddings
  llm_rationale: text                  -- why the LLM thinks they're linked
  confirmed: bool (default false)      -- user confirmed/rejected
  created_at: datetime
```

### Consistency (Layer 2)

```
ConsistencyFlag
  id: UUID (PK)
  tenant_id: FK(Tenant)
  idea_id: FK(Idea)
  related_idea_id: FK(Idea) (nullable) -- if cross-idea inconsistency
  component_id: FK(IdeaComponent) (nullable)
  severity: enum(info, warning, critical)
  flag_type: enum(
    budget_exceeds_total,
    deadline_conflict,
    component_overlap,
    cross_idea_contradiction,
    missing_dependency,
    dependency_cycle,
    dependency_deadline_conflict,
    shared_resource_conflict
  )
  description: text                    -- LLM-generated explanation
  resolved: bool (default false)
  resolved_by: FK(User) (nullable)
  created_at: datetime
```

### Team Collaboration (Layer 3)

```
Question
  id: UUID (PK)
  tenant_id: FK(Tenant)
  idea_id: FK(Idea)
  component_id: FK(IdeaComponent) (nullable)
  asked_by: FK(User)
  question_text: text
  status: enum(open, answered, closed)
  created_at: datetime

Answer
  id: UUID (PK)
  question_id: FK(Question)
  answered_by: FK(User)
  answer_text: text
  is_ai_generated: bool                -- true if LLM drafted it
  approved: bool (default false)       -- owner approved AI answer
  created_at: datetime
```

### Planning Session (Layer 1)

```
PlanningSession
  id: UUID (PK)
  tenant_id: FK(Tenant)
  user_id: FK(User)
  idea_id: FK(Idea) (nullable — created mid-session)
  mode: enum(chat, form, hybrid)
  status: enum(active, completed, abandoned)
  conversation_history: jsonb          -- full message log
  extracted_data: jsonb                -- structured fields extracted so far
  created_at: datetime
  completed_at: datetime (nullable)
```

---

## LLM INTEGRATION DESIGN

### Unified Client (`app/llm/client.py`)

```python
# Abstract interface — same API for Ollama (local) and vLLM (cloud)
# Both expose OpenAI-compatible /v1/chat/completions

class LLMClient:
    async def chat(model, messages, temperature, response_format) -> str
    async def embed(model, text) -> list[float]
    async def classify(model, text, categories) -> dict

# Config switches via environment:
# LLM_BACKEND=ollama | vllm
# LLM_BASE_URL=http://localhost:11434/v1  (ollama)
# LLM_BASE_URL=http://vllm-host:8000/v1  (vllm)
```

### Model Assignment

| Task                      | Model           | Why                                    |
|---------------------------|-----------------|----------------------------------------|
| Planning conversation     | qwen3-8b        | Best at structured multi-turn dialogue |
| Consistency checking      | qwen3-8b        | Needs reasoning over complex state     |
| Shareability scoring      | qwen3-1.7b      | Simple classification, fast            |
| Link detection rationale  | qwen3-8b        | Needs to explain connections           |
| Dependency detection      | qwen3-8b        | Cross-idea component reasoning         |
| Question answering        | qwen3-8b        | Context-heavy reasoning                |
| Embeddings                | nomic-embed-text | 768-dim, high quality, local           |

### Prompt Engineering Approach

All prompts live in `app/llm/prompts/` as Jinja2 templates. Each prompt:
1. Has a system message defining the role and output format
2. Uses structured output (JSON mode) for all extraction tasks
3. Includes few-shot examples inline
4. Is version-controlled and testable independently

---

## SHAREABILITY INDEX — DETAILED DESIGN

The shareability system is the core differentiator. It works as follows:

### Levels

```
Tier 1-2:  PUBLIC       — visible to all tenant members
Tier 3-4:  INTERNAL     — visible to members with access_tier >= 3
Tier 5-6:  CONFIDENTIAL — visible to members with access_tier >= 5
Tier 7-8:  RESTRICTED   — visible to admins and explicitly granted users
Tier 9-10: TOP SECRET   — visible only to idea owner and tenant owner
```

### Auto-Classification Flow

1. When a component is created/updated, Celery triggers `classify_shareability` task
2. LLM (qwen3-1.7b) receives component name + description + idea context
3. LLM outputs: `{ classification, score (0.0-1.0), rationale }`
4. Score maps to a tier suggestion; stored in `ShareabilityRule`
5. Owner receives notification to confirm/override
6. Until confirmed, auto-classified rules are marked and can be bulk-reviewed

### Access Filtering

Every query to the team interface passes through a shareability middleware:
```python
def filter_by_access(query, user_membership):
    user_tier = user_membership.access_tier
    return query.filter(
        or_(
            ShareabilityRule.min_access_tier <= user_tier,
            ShareabilityRule.idea_id == None  # no rule = default public
        )
    )
```

Team members see:
- **Idea titles and high-level descriptions** (always, if shared at all)
- **Component details** gated by their access tier
- **Budget figures** only if their tier meets the component's shareability
- **Questions and answers** filtered to components they can see
- **Shared dependencies** — when a cross-idea dependency exists, team members
  on either side see the other idea's component (name, description, status,
  deadline, dependency type) regardless of normal shareability tier, BUT
  budget figures and internal notes remain hidden. Owners can reject or
  tighten this auto-exposure per dependency.

---

## CONSISTENCY CHECKER — DETAILED DESIGN

Advisory mode: flags issues but never blocks saves.

### Check Types

1. **Budget Consistency**: Sum of component costs vs. idea total budget
2. **Deadline Feasibility**: Component deadlines after idea deadline
3. **Component Overlap**: Two components in same idea describe similar work (embedding similarity > 0.85)
4. **Cross-Idea Contradiction**: Linked ideas with conflicting assumptions (LLM-detected)
5. **Missing Dependencies**: Component references capability not in any component
6. **Dependency Cycle**: Adding a dependency would create a circular chain in the DAG
7. **Dependency Deadline Conflict**: A blocking dependency's target has a deadline after the source's deadline
8. **Shared Resource Conflict**: Two components with `shares_resource` dependency have overlapping timelines and incompatible resource needs

### Trigger Points

- On idea save → synchronous lightweight checks (budget math, deadline logic)
- On idea save → async Celery task for LLM-powered checks (contradiction, overlap)
- Nightly sweep → full cross-idea consistency scan across tenant

### UI Treatment

- Yellow banner on idea detail page: "2 advisory flags"
- Expandable list showing each flag with severity, description, and "Resolve" button
- Resolved flags are hidden but kept in history

---

## CLI DESIGN

```bash
# Interactive planning session (mirrors the GUI chat)
cereborate plan
# > What's your idea? ...
# > (follow-up questions driven by same LLM prompts as GUI)

# Direct idea management
cereborate ideas list
cereborate ideas show <idea-id>
cereborate ideas export <idea-id> --format json|csv|md

# Team management
cereborate team invite user@example.com --role member --tier 3
cereborate team list

# Configuration
cereborate config set-model planning qwen3-8b
cereborate config set-url http://localhost:11434
cereborate config toggle-mode gui|cli   # sets default interface preference
```

The CLI uses the same FastAPI backend via HTTP — it is a thin client, not a separate app.
The `cereborate plan` command opens a Rich-powered interactive REPL that streams
LLM responses with proper formatting (markdown rendering, progress spinners).

---

## API ROUTES (v1)

### Planning
```
POST   /api/v1/plan/start              — Start a new planning session
POST   /api/v1/plan/{session_id}/respond — Send user response, get follow-up
POST   /api/v1/plan/{session_id}/complete — Finalize and create idea
GET    /api/v1/plan/{session_id}        — Get session state
WS     /api/v1/ws/plan/{session_id}     — Real-time planning chat
```

### Ideas
```
GET    /api/v1/ideas                    — List ideas (owner's view)
POST   /api/v1/ideas                    — Create idea directly (skip planning)
GET    /api/v1/ideas/{id}               — Get idea detail
PATCH  /api/v1/ideas/{id}               — Update idea
DELETE /api/v1/ideas/{id}               — Archive idea
GET    /api/v1/ideas/{id}/versions      — Version history
GET    /api/v1/ideas/{id}/components    — List components
POST   /api/v1/ideas/{id}/components    — Add component
GET    /api/v1/ideas/{id}/links         — Get cross-idea links
GET    /api/v1/ideas/{id}/consistency   — Get consistency flags
```

### Dependencies
```
GET    /api/v1/ideas/{id}/dependencies          — List all deps for idea's components
POST   /api/v1/components/{id}/dependencies     — Add a dependency from this component
DELETE /api/v1/dependencies/{id}                — Remove a dependency
PATCH  /api/v1/dependencies/{id}/confirm        — Confirm/reject LLM-detected dep
GET    /api/v1/ideas/{id}/dependency-graph      — Full DAG for idea (incl. cross-idea)
GET    /api/v1/shared/dependencies              — All cross-idea shared deps visible to me
GET    /api/v1/shared/ideas/{id}/dependencies   — Shared deps for a specific shared idea
```

### Shareability
```
GET    /api/v1/ideas/{id}/shareability          — Get shareability config
PATCH  /api/v1/ideas/{id}/shareability          — Update idea-level rules
PATCH  /api/v1/components/{id}/shareability     — Override component classification
POST   /api/v1/ideas/{id}/shareability/recompute — Trigger re-classification
```

### Team (Layer 3)
```
GET    /api/v1/shared/ideas             — Browse shared ideas (access-filtered)
GET    /api/v1/shared/ideas/{id}        — View shared idea (access-gated)
POST   /api/v1/shared/ideas/{id}/questions — Ask a question
GET    /api/v1/shared/ideas/{id}/questions — List questions (access-filtered)
POST   /api/v1/questions/{id}/answers   — Answer a question
```

### Auth & Admin
```
POST   /api/v1/auth/register            — Create account + tenant
POST   /api/v1/auth/login               — Get JWT tokens
POST   /api/v1/auth/refresh             — Refresh token
GET    /api/v1/tenant/members            — List members
POST   /api/v1/tenant/members/invite     — Invite member with role + tier
PATCH  /api/v1/tenant/members/{id}       — Update role/tier
```

---

## ENVIRONMENT VARIABLES

```bash
# Database
DATABASE_URL=postgresql+asyncpg://cereborate:password@localhost:5432/cereborate

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM
LLM_BACKEND=ollama                    # ollama | vllm
LLM_BASE_URL=http://localhost:11434/v1
LLM_PLANNING_MODEL=qwen3-8b
LLM_CLASSIFIER_MODEL=qwen3-1.7b
LLM_EMBEDDING_MODEL=nomic-embed-text

# Auth
JWT_SECRET=<generate-random-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=60

# App
APP_ENV=development                    # development | production
APP_URL=http://localhost:3000
API_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000
```

---

## BUILD ORDER (Implementation Phases)

### Phase 1: Foundation (Week 1-2)
1. Docker Compose with PostgreSQL + pgvector + Redis + Ollama
2. FastAPI app skeleton with config, deps, health check
3. Alembic migrations for User, Tenant, TenantMembership
4. Auth endpoints (register, login, JWT)
5. Basic Next.js app with NextAuth integration

### Phase 2: Planning Engine (Week 3-4)
6. Idea + IdeaComponent + PlanningSession models + migrations
7. LLM client abstraction (Ollama backend)
8. Planning prompts (intake, follow-up)
9. Planning API endpoints (start, respond, complete)
10. Planning GUI: chat interface + structured form + toggle
11. CLI: `cereborate plan` command

### Phase 3: The Brain — Links & Dependencies (Week 5-7)
12. Embedding service (nomic-embed-text via Ollama)
13. IdeaLink model + linking service
14. ComponentDependency model + dependency service
15. DAG validation (cycle detection, deadline propagation)
16. Cross-idea dependency auto-detection (LLM + embedding similarity)
17. ConsistencyFlag model + consistency service (incl. dependency checks)
18. Celery setup + async tasks for linking, dependencies, and consistency
19. Budget model + budget consistency checks
20. DependencyGraph component (D3 DAG visualization)

### Phase 4: Shareability + Dependency Exposure (Week 8-9)
21. ShareabilityRule model + migrations
22. Shareability scoring prompt + classification service
23. Access filtering middleware
24. Cross-idea dependency auto-exposure logic (SharedDependencyView)
25. Shareability management UI (owner config, incl. dep override)
26. ShareabilityMeter + SharedDepsBadge components

### Phase 5: Team Interface (Week 10-11)
27. Question/Answer models
28. Shared ideas browse page (access-filtered)
29. Shared dependencies page (cross-idea deps visible to me)
30. Q&A system with LLM-assisted answers
31. Notification service for linked idea updates + dependency status changes
32. Link graph + dependency graph visualizations in team view

### Phase 6: Polish & Deploy (Week 12-13)
33. Nightly consistency sweep task (incl. dependency re-scan)
34. Export (JSON, CSV, Markdown) — incl. dependency graph export
35. Nginx reverse proxy config
36. Production Docker Compose with vLLM swap
37. CI/CD pipeline
38. Landing page

---

## CODING CONVENTIONS

### Python (Backend + CLI)
- Python 3.12, type hints everywhere
- async/await for all I/O (database, LLM calls, HTTP)
- Pydantic v2 for all schemas and settings
- SQLAlchemy 2.0 style (mapped_column, declarative)
- 4-space indentation, Black formatter, Ruff linter
- Tests with pytest-asyncio, factory_boy for fixtures
- All services are dependency-injected via FastAPI `Depends()`

### TypeScript (Frontend)
- Strict TypeScript, no `any`
- Next.js App Router with server components by default
- Client components only where interactivity required (`"use client"`)
- Tailwind CSS for styling, shadcn/ui for base components
- SWR or TanStack Query for data fetching
- Zod for client-side form validation

### General
- Every API endpoint has OpenAPI docs (FastAPI auto-generates)
- Every model has `tenant_id` — ALL queries filter by tenant
- Never trust client-side access control; always re-check on server
- Secrets in `.env`, never committed
- Commit messages: conventional commits (`feat:`, `fix:`, `chore:`)

---

## KEY DESIGN DECISIONS & RATIONALE

1. **Ollama locally, vLLM in production**: Same OpenAI-compatible API. Zero code changes to swap. Ollama is simpler for dev on Mac; vLLM gives 3-5x throughput in production.

2. **PostgreSQL + pgvector over separate vector DB**: One database for everything. pgvector is production-ready for <1M vectors. Avoids operational complexity of ChromaDB/Pinecone.

3. **Advisory consistency (not blocking)**: Blocking kills creative flow. Users should be warned, not stopped. The LLM may be wrong — humans decide.

4. **Shareability as a first-class concept**: Not bolted on RBAC. Shareability is per-component, LLM-scored, and the index aggregates up. This makes it a meaningful metric, not just access control.

5. **CLI as thin HTTP client**: Shares all business logic with the GUI. No duplication. The CLI is just a different input/output mode for the same backend.

6. **Jinja2 prompt templates**: Versionable, testable, parameterizable. Better than hardcoded strings. Each prompt can be A/B tested.

7. **Multi-tenant from day one**: SaaS architecture. Every table has `tenant_id`. Queries always scope by tenant. This is hard to retrofit.

8. **Dependencies as a DAG, not a flat list**: Component dependencies form a directed acyclic graph. This enables deadline propagation, critical path analysis, and cycle detection. The graph spans idea boundaries — a component in Idea A can block a component in Idea B.

9. **Cross-idea dependency auto-exposure**: When the Brain detects (or a user creates) a dependency that crosses idea boundaries, both sides' teams automatically gain limited visibility into the other idea's relevant component. This is the key mechanism for organic collaboration — teams discover shared surface area through the dependency graph, not through manual sharing. The exposure is deliberately limited (no budgets, no internal notes) and owner-overridable.

10. **LLM-detected dependencies require confirmation**: Auto-discovered dependencies are surfaced with `confirmed=false`. They appear in the UI with a review prompt but don't affect shareability or team visibility until the owner confirms. This prevents false positives from leaking information.
