# Cereborate — User Guide

> **Think together. Share smart.**
> Cereborate is a structured ideation platform with an AI backbone. This guide walks through everything you can do as a user.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Planning an Idea](#planning-an-idea)
3. [Managing Your Ideas](#managing-your-ideas)
4. [Components](#components)
5. [Dependencies](#dependencies)
6. [Shareability](#shareability)
7. [Team Collaboration](#team-collaboration)
8. [Questions & Answers](#questions--answers)
9. [Notifications](#notifications)
10. [Exporting Ideas](#exporting-ideas)
11. [Using the CLI](#using-the-cli)
12. [Account & Workspace Settings](#account--workspace-settings)

---

## Getting Started

### Creating an account

1. Open Cereborate in your browser and click **Get Started Free**
2. Fill in your name, email, password, and a workspace name
   - The workspace name becomes your **tenant** — a private space for your team
3. You're logged in automatically and land on the **Planning** page

### Inviting team members

As the workspace owner you can invite others:

1. Go to **Admin → Members** in the sidebar
2. Click **Invite member**
3. Enter their email, choose a **role**, and set an **access tier** (1–10)

> **Roles:** `owner` > `admin` > `member` > `viewer`
> **Access tiers** control which idea components each person can see (see [Shareability](#shareability)).

---

## Planning an Idea

Cereborate has two ways to create an idea: **chat** (conversational) and **form** (structured). Both produce the same result.

### Chat mode

1. Click **Plan** in the sidebar, then **Start new plan**
2. Describe your idea in plain language — as much or as little as you have
3. The AI asks follow-up questions to draw out:
   - Components and sub-tasks
   - Budget and cost estimates
   - Deadlines
   - Priorities (must-have, should-have, nice-to-have)
4. When you have enough detail, click **Create Idea**

The extracted structure appears in a panel on the right as you chat, updating in real time.

### Form mode

If you prefer to type directly into fields:

1. On the planning page, toggle to **Form** mode
2. Fill in title, description, deadline, and budget
3. Add components manually using the **+ Add Component** button

### Tips for better AI planning

- Be specific about **who** the idea is for and **why** it matters
- Mention constraints upfront: "budget is $20k", "must launch by June"
- Name the key pieces of work, even roughly — the AI will refine them
- If a follow-up question doesn't apply, say "skip" or "not applicable"

---

## Managing Your Ideas

### Ideas list

The **Ideas** page shows all your active ideas. Each card shows:
- Title and status (draft / active / archived)
- Number of components
- Deadline and budget (if set)
- Version number

Click any idea to open its detail view.

### Idea detail

The idea detail page has several sections:

| Section | What it shows |
|---------|--------------|
| Header | Title, status, version, export button |
| Description | Full idea description and metadata |
| Components | All components with priority, status, cost |
| Navigation links | Dependencies · Shareability · Links (cross-idea) |

### Editing an idea

On the idea detail page, fields are editable inline. Every save increments the **version number** and stores a snapshot in the version history — so you can always see how the idea evolved.

### Archiving an idea

Click the **⋯** menu on an idea card or the delete button on the detail page. Archived ideas are hidden from your list but not permanently deleted.

---

## Components

Components are the building blocks of an idea — the individual pieces of work, features, or deliverables.

### Adding a component

1. Open an idea, scroll to **Components**
2. Click **Manage** → **Add Component**
3. Fill in:
   - **Name** — short, descriptive label
   - **Description** — what this component involves
   - **Priority** — must-have / should-have / nice-to-have
   - **Status** — proposed / approved / in progress / done
   - **Estimated cost** (optional)
   - **Deadline** (optional)

### Component statuses

| Status | Meaning |
|--------|---------|
| `proposed` | Not yet reviewed |
| `approved` | Accepted into the plan |
| `in_progress` | Actively being worked on |
| `done` | Completed |

When a `blocks` dependency's target component is marked **done**, the source component's owner receives a notification that the blocker has cleared.

### Shareability score

Each component gets an AI-computed **shareability score** (0–1) that reflects how sensitive the information is. This feeds into the idea's overall shareability index. You can override it manually — see [Shareability](#shareability).

---

## Dependencies

Components can depend on each other, both within one idea and across ideas. Cereborate models these as a **directed acyclic graph (DAG)**.

### Dependency types

| Type | Meaning |
|------|---------|
| `blocks` | This component cannot start until the target is done |
| `requires_output` | This component needs an artifact or deliverable from the target |
| `shares_resource` | Both components use the same resource, budget, or person |
| `extends` | This component builds on top of the target |
| `informed_by` | Soft link — the target's outcome influences this component |

### Adding a dependency

1. Open an idea and click **Dependencies** in the navigation
2. Click **+ Add Dependency**
3. Select source component, target component, and type

Cereborate automatically checks for **cycles** — if adding a dependency would create a circular chain, you'll see a consistency flag (advisory, not a hard block).

### Cross-idea dependencies

The AI scans your components against components in other ideas (using semantic similarity). When it finds a potential cross-idea dependency it:

1. Adds it with `confirmed = false` — it appears for review but has no effect yet
2. You review and **confirm** or **reject** it
3. Once confirmed, both teams get limited visibility into each other's relevant component (see [Shareability — Cross-idea exposure](#cross-idea-exposure))

### Visualizing the graph

The **Dependencies** page shows the full DAG for your idea — nodes are components, edges show dependency type. Cross-idea edges are highlighted.

---

## Shareability

Shareability controls what your team members can see. It operates at two levels: the **idea** and the **component**.

### Access tiers

Cereborate uses a 1–10 tier scale:

| Tier | Classification | Who can see it |
|------|---------------|----------------|
| 1–2 | Public | All workspace members |
| 3–4 | Internal | Members with tier ≥ 3 |
| 5–6 | Confidential | Members with tier ≥ 5 |
| 7–8 | Restricted | Admins and explicit grants only |
| 9–10 | Top Secret | Idea owner + workspace owner only |

Each team member has a single access tier set by the workspace admin (see [Inviting team members](#inviting-team-members)).

### How components get classified

When you add or update a component, Cereborate automatically runs it through the AI classifier (`qwen3:1.7b`) to suggest a shareability tier. The classification considers:

- The component's name and description
- The idea's context
- Sensitivity signals (budget figures, personal data, competitive information, etc.)

Auto-classified rules show an **(auto)** badge. You can override any classification manually.

### Overriding shareability

1. Go to **Ideas → [your idea] → Shareability**
2. See the overall **Shareability Index** (weighted average of all components)
3. Click on any component row to change its tier and classification
4. Click **Recompute All** to re-run the AI classifier across all components

### Cross-idea exposure

When a confirmed cross-idea dependency exists between two components, Cereborate automatically lowers the effective visibility tier to the **less restrictive** of the two — so both teams can see the shared surface.

What the other team's members see (read-only):
- Component name and description
- Status and deadline
- Dependency type

What they **never** see:
- Budget figures
- Internal notes or shareability rationale

You can **reject** this auto-exposure per dependency on the Shareability page. Once rejected, the cross-idea component reverts to its original tier.

---

## Team Collaboration

Team members browse ideas that have been shared with them (based on their access tier) through the **Shared** section.

### Browsing shared ideas

1. Click **Shared** in the sidebar
2. You see all ideas in the workspace where your tier meets or exceeds the idea's minimum tier
3. Each card shows:
   - Title and description
   - Shareability meter
   - Count of shared cross-idea dependencies

### Viewing a shared idea

Click any shared idea card to open its detail view. You see:
- Full title and description
- Deadline (if set)
- Components visible at your access tier — **budget figures are always hidden**
- The idea's shareability index

### Shared dependencies

The **Dependencies** page (team view) shows all cross-idea dependencies where any of your ideas are involved — giving you a unified picture of shared work surface across the whole workspace.

You can also view shared dependencies for a specific idea at **Shared → [idea] → Shared Deps**.

---

## Questions & Answers

Team members can ask questions on any shared idea they can access.

### Asking a question

1. Open a shared idea
2. Scroll to **Questions**
3. Type your question and click **Ask Question**

You can optionally target a specific component (useful if your question is about implementation details of one piece).

### Answering a question

Anyone in the workspace can answer questions on ideas they can see.

1. Open the shared idea (or go to **Questions** in the sidebar for a global feed)
2. Find the question
3. Type your answer in the text box and click **Answer**

Human answers are published immediately.

### AI-assisted answers

The workspace owner or idea owner can request an AI-generated answer:

1. Click **Ask AI** on any open question
2. The AI (`qwen3:8b`) reads the full idea context — components, statuses, deadlines — and drafts an answer
3. The AI answer appears with a **Pending approval** badge
4. The idea owner reviews and clicks **Approve** to publish it

> AI answers are never shown to other team members until an owner approves them.

### Question statuses

| Status | Meaning |
|--------|---------|
| `open` | No answer yet |
| `answered` | At least one approved answer exists |
| `closed` | Marked resolved by the owner |

---

## Notifications

Cereborate sends you notifications when things relevant to your ideas change.

### Notification types

| Event | When you get it |
|-------|----------------|
| **Linked idea updated** | A cross-idea link is detected and one of the linked ideas is yours |
| **Dependency cleared** | A `blocks` dependency targeting one of your components is marked done |
| **Cross-idea dependency detected** | The AI finds a new potential dependency involving your component |
| **Question answered** | An answer is posted on a question you asked |
| **Shareability changed** | A component's auto-classification changes |

### Managing notifications

1. Click **Notifications** in the sidebar
2. Unread notifications are highlighted in blue
3. Click **Mark read** on individual items, or **Mark all read** at the top

---

## Exporting Ideas

You can export any idea you own in three formats.

### How to export

1. Open an idea you own
2. Click the **Export ▾** button in the top-right of the header
3. Choose a format:

| Format | Contents | Best for |
|--------|----------|---------|
| **JSON** | Full structured data — all fields, components, dependencies, links | API integration, data archival |
| **CSV** | Tabular — idea header, components table, dependencies table | Spreadsheet analysis |
| **Markdown** | Formatted document — title, description, components table, dependency list, links | Documentation, sharing outside the platform |

The file downloads automatically with a filename derived from the idea title.

### What's included in an export

- Idea metadata (title, description, status, version, deadline, budget)
- All components (name, priority, status, cost, deadline, shareability score)
- All **confirmed** dependencies (source → target, type, cross-idea flag)
- All **confirmed** cross-idea links (linked idea ID, type, similarity score, AI rationale)

---

## Using the CLI

The Cereborate CLI provides the same capabilities as the web UI from your terminal.

### Installation

```bash
# From the repo root
cd backend && uv sync
uv run cereborate --help
```

Or if installed as a package:
```bash
cereborate --help
```

### Configuration

```bash
# Point the CLI at your Cereborate instance
cereborate config set-url http://localhost:8000

# Set the default LLM model for planning
cereborate config set-model planning qwen3:8b

# View current config
cereborate config show
```

### Planning a new idea

```bash
cereborate plan
```

This opens an interactive REPL in your terminal with the same AI follow-up flow as the web chat. Responses stream in real time with markdown rendering.

### Managing ideas

```bash
# List your ideas
cereborate ideas list

# Show a specific idea (with components)
cereborate ideas show <idea-id>

# Export an idea
cereborate ideas export <idea-id> --format json
cereborate ideas export <idea-id> --format csv
cereborate ideas export <idea-id> --format markdown
```

### Team management

```bash
# List all workspace members
cereborate team list

# Invite a new member
cereborate team invite user@example.com --role member --tier 3
```

### Tips

- The CLI uses the same backend API as the web UI — any idea created via CLI appears instantly in the web app
- Use `cereborate ideas export` in scripts or CI pipelines to archive idea snapshots automatically
- The `--format markdown` export is useful for pasting ideas into Confluence, Notion, or GitHub wikis

---

## Account & Workspace Settings

### Changing your profile

Currently managed via the API (`PATCH /api/v1/auth/me`) or directly in the database. A profile settings page is on the roadmap.

### Member roles and what they can do

| Action | Viewer | Member | Admin | Owner |
|--------|--------|--------|-------|-------|
| Browse shared ideas | ✓ | ✓ | ✓ | ✓ |
| Ask questions | ✓ | ✓ | ✓ | ✓ |
| Create ideas | | ✓ | ✓ | ✓ |
| Invite members | | | ✓ | ✓ |
| Change member tiers | | | ✓ | ✓ |
| Approve AI answers | (on their own ideas) | ✓ | ✓ | ✓ |
| Override shareability | (on their own ideas) | ✓ | ✓ | ✓ |

### Access tier guidelines (suggested)

| Tier | Example role |
|------|-------------|
| 1–2 | External contractors, broad team members |
| 3–4 | Full-time team members |
| 5–6 | Senior team members, tech leads |
| 7–8 | Managers, project leads |
| 9–10 | Executives, owners only |

Tiers are set per-member and apply across all ideas in the workspace. A higher tier gives broader visibility.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Submit message in planning chat |
| `Shift + Enter` | New line in planning chat |
| `Esc` | Close dropdowns and modals |

---

## Getting Help

- Check the **Consistency flags** on your idea — they explain detected issues and suggest fixes
- Review the **Dependency graph** to visualize blockers
- Ask a question on a shared idea — the AI or a colleague can answer
- For technical setup issues, see the [Implementation Guide](./IMPLEMENTATION_GUIDE.md)
