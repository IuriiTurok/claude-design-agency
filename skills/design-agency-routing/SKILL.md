---
name: design-agency-routing
description: "Routes design-intent prompts to the design agency. Use whenever a <design-agency-decision> block is present in injected context (emitted by the design-agency UserPromptSubmit hook), AND as a discovery fallback when the user mentions brand identity, brand book, rebrand, logo, landing page, design system, style guide, mascot, or UI prototype work but no decision block has appeared yet. Asks the user whether to engage the agency when design intent is detected, with 'Use design agency' as the recommended default. Mandatory before doing design work inline when the band is engage or ask. Skip for trivial one-line CSS/copy tweaks the user explicitly wants inline."
---

# design-agency-routing

You are running as a **router parent**. The design-agency hook has
classified the user's prompt and emitted a `<design-agency-decision>` block
in your injected context. Honour it before doing any design work.

## Contents

- [Configuration](#configuration)
- [Decision schema](#decision-schema)
- [Procedure](#procedure)
- [Step 1 — SUBAGENT GUARD](#step-1--subagent-guard)
- [Step 2 — PLAN-MODE CHECK](#step-2--plan-mode-check-parent-authoritative)
- [Step 3 — ROUTER RECONCILIATION](#step-3--router-reconciliation)
- [Step 4 — `band == "engage"`](#step-4--band--engage)
- [Step 5 — `band == "ask"`](#step-5--band--ask)
- [Step 6 — `band == "none"` or no decision block](#step-6--band--none-or-no-decision-block)
- [Failure modes to avoid](#failure-modes-to-avoid)
- [Inputs / Outputs / Dependencies](#inputs--outputs--dependencies)
- [Recommended next step](#recommended-next-step)
- [Self-learning](#self-learning)

---

## Configuration

Named cache paths used by this skill. Override via the matching env var if needed.

| Constant           | Default path                                    | Env var                       |
| ------------------ | ----------------------------------------------- | ----------------------------- |
| `OVERRIDES_LOG`    | `~/.claude/cache/design-agency/overrides.jsonl` | `DESIGN_AGENCY_OVERRIDES_LOG` |
| `ROUTER_AUDIT_LOG` | `~/.claude/cache/router/audit.jsonl`            | `ROUTER_AUDIT_LOG`            |

---

## Decision schema

```json
{
  "band": "engage" | "ask" | "none",
  "confidence": 0.0-1.0,
  "engagement_type": "brand_project" | "deliverable_iteration" | "prototype" | "character_3d" | "asset" | "ops" | "unknown",
  "matched_signals": ["..."],
  "reason": "one-sentence justification",
  "source": "heuristic" | "repo_agents_md" | "override" | "project_config",
  "decision_id": "da_xxxxxxxxxx",
  "thresholds": {"ask": 0.55},
  "plan_mode": false
}
```

`band == "engage"` — the classifier is confident enough to invoke the agency without asking.
`band == "ask"` — design intent detected but confidence is below the engage threshold; prompt the user.
`band == "none"` — no design intent; proceed normally.

`plan_mode` is **best-effort and usually `false`** — the hook can't see plan mode reliably. Trust your own context over this field (see Step 2).

`source == "repo_agents_md"` — the current repo's `AGENTS.md` mandates the design agency (e.g. the brandbook repo). The bootstrap already loaded the correct skill set; do not re-read the plugin roster on top of it. **Inverse case:** when NO `AGENTS.md` is present (the root cause of the 2026-06 audit finding where 58 sessions bypassed the agency), the keyword-fallback in this skill's `description` is the only thing that fires the agency — this is why secondary keyword triggers are declared there.

---

## Procedure

```
SUBAGENT GUARD  → dispatched subagent? ignore block entirely — FIRST CHECK
PLAN-MODE CHECK → in plan mode? fold agency into plan, never AskUserQuestion — SECOND CHECK
ROUTER RECONCIL → resolve design-agency question before honouring router decision
band == "engage" → invoke design-agency skill with engagement_type
band == "ask"    → AskUserQuestion (one question), then log choice
band == "none"   → proceed normally
```

---

### Step 1 — SUBAGENT GUARD

If you are running as a dispatched subagent (your system prompt identifies
you as a `router-*` worker, or the parent dispatched you via the `Agent`
tool), **ignore the `<design-agency-decision>` block entirely** and proceed
with the assigned task. Agency orchestration is the parent's responsibility;
a bare worker model re-engaging the agency would strip context and double-gate
the workflow.

---

### Step 2 — PLAN-MODE CHECK (parent-authoritative)

If a system reminder in your context says plan mode is active, fold the
design-agency workflow into the plan itself — do NOT call `AskUserQuestion`
about engagement. The user approves the agency by reviewing the plan.
The `plan_mode` field in the decision block is best-effort and is almost always
`false` even when you ARE in plan mode; trust your own context, not that field.

---

### Step 3 — ROUTER RECONCILIATION

The auto-model-router's `UserPromptSubmit` hook also fires on every prompt,
so a `<router-decision>` block may be present alongside the
`<design-agency-decision>` block. Resolve the design-agency question FIRST.

- **If the agency is engaged** (band `engage`, or the user chose "Use design
  agency" on an `ask` band): treat the router band as `none` and log outcome
  `continuity_inline` to `ROUTER_AUDIT_LOG` by running:

  ```bash
  scripts/log_router_continuity.sh "<router_decision_id>" "<model>"
  ```

  Rationale: delegating design work to a bare `router-sonnet` worker strips
  the agency context (Emil, Impeccable, Taste roles) that the engagement
  carries. The agency runs inline on the current session model.
  **Bridge note:** the `continuity_inline` rows this skill writes to `audit.jsonl`
  are consumed by `auto-model-routing`'s `router_loop.py` sil. Do not
  double-count them in the overrides harvest — they are already owned by the router loop.

- **If the user declines the agency** (chose "Quick inline design" or "Not
  design work"): honour the `<router-decision>` block normally per the
  auto-model-routing skill.

---

### Step 4 — `band == "engage"`

Invoke the `design-agency` skill, passing the `engagement_type` from the
decision block.

**Special case — `source == "repo_agents_md"`:** The current repo's
`AGENTS.md` already mandates the agency and has run the bootstrap. Defer
entirely to that bootstrap — do NOT re-read the plugin roster on top of it.
Double-loading the roster overwrites role assignments and corrupts the
context the bootstrap already established.

---

### Step 5 — `band == "ask"`

1. Call `AskUserQuestion` with ONE question:
   - **header**: `Design agency`
   - **question**: "Design intent detected (`<engagement_type>`, confidence
     `<confidence>`). Engage the design agency workflow?"
   - **options**:
     - `Use design agency (Recommended)` — invoke the `design-agency` skill.
     - `Quick inline design (no agency gates)` — proceed inline; the full agency
       QA gates are skipped, but for a component/page/UI build still reach for the
       `ui-ux-pro-max` skill (ground palette/type/layout in its database) then
       `impeccable` (`craft` mode) before writing the code yourself — see Step 6.
     - `Not design work` — proceed normally.

2. Wait for the answer, then execute the chosen branch.

3. **Log the user's choice** before doing the work — run:

   ```bash
   python3 scripts/log_override.py "<DECISION_ID>" "<ENGAGEMENT_TYPE>" <CONFIDENCE> "<USER_CHOICE>"
   ```

   Substitute the `decision_id`, `engagement_type`, and `confidence` from the
   `<design-agency-decision>` block. Use one of `engaged`, `inline`, or
   `not_design` for `user_choice`. Never block on this — the script exits non-zero
   but non-fatally on a write failure; proceed with the work regardless.

   `not_design` rows are false-positive training data for tuning the hook's
   heuristics. Every row matters; never skip the log step.

---

### Step 6 — `band == "none"` or no decision block

Proceed normally on the current session model. **Exception — inline UI/design
build:** if the work is building or restyling a component, page, screen, or app
(not a trivial one-line CSS/copy tweak), first reach for the `ui-ux-pro-max`
skill to ground design-system / palette / typography / layout choices, then
`impeccable` (`craft` mode) to write distinctive, anti-slop frontend, before
writing the code yourself. These skills ARE the top-level tool on this inline
branch — the "do not invoke directly" rule in Failure modes applies only when the
agency is engaged, not here.

---

## Failure modes to avoid

- **Don't re-ask after the user has already answered once this session.**
  The hook's engaged-marker should prevent re-prompts on follow-up turns.
  If a stale `<design-agency-decision>` block appears on a subsequent turn
  after the user already answered, honour the previous answer and skip the
  question.

- **Don't engage the agency for trivial one-line CSS tweaks the user
  explicitly wants inline.** A micro-edit the user described as "just change
  the colour to red" is not a design engagement. Reserve agency invocation for
  deliverables, brand-level decisions, and multi-step design workflows.

- **Don't let passive skill matching substitute for the agency when the user
  chose "Use design agency".** The skills `impeccable`, `ui-ux-pro-max`, and
  `taste-skill` may match on their own through normal skill routing. When the
  user has engaged the agency, those vocabularies are orchestrated through the
  agency's own roles (Emil as motion designer, Impeccable as polish inspector,
  Taste as taste guardian). Let the agency own that orchestration — do not
  invoke those skills directly in parallel.

---

## Inputs / Outputs / Dependencies

**Inputs:**

- A `<design-agency-decision>` JSON block injected by the design-agency `UserPromptSubmit` hook (schema above). Required to operate; if absent, fall through to Step 6.
- Optionally a co-present `<router-decision>` block from the auto-model-router hook.

**Outputs:**

- Invocation of the `design-agency` skill (band `engage`, or user chose agency).
- Inline design work (band `none` or user declined).
- One JSON line appended to `OVERRIDES_LOG` (`~/.claude/cache/design-agency/overrides.jsonl`) — user choice record (Step 5).
- One JSON line appended to `ROUTER_AUDIT_LOG` (`~/.claude/cache/router/audit.jsonl`) — `continuity_inline` outcome (Step 3, when agency is engaged).

**Upstream:**

- design-agency `UserPromptSubmit` hook (classifier that emits the decision block).
- auto-model-router `UserPromptSubmit` hook (emits co-present `<router-decision>` block).

**Downstream:**

- `design-agency` skill (invoked on `engage` or user-accept) → Design Phase-5 QA gates (motion-designer / polish-inspector / style-enforcer → taste-guardian → visual-qa).
- `auto-model-routing` skill (deferred to on user-decline, per the co-present `<router-decision>` block).
- `overrides.jsonl` (false-positive training log; not_design rows flag over-triggers by `engagement_type`/`confidence` band).
- `audit.jsonl` (router outcome log; `continuity_inline` rows consumed by `router_loop.py` sil).

---

## Recommended next step

| Outcome                                                   | Next action                                                                 |
| --------------------------------------------------------- | --------------------------------------------------------------------------- |
| `engage` / user accepted agency                           | Invoke `design-agency` with the `engagement_type` from the decision block.  |
| User declined ("Quick inline design" / "Not design work") | Defer to `auto-model-routing` per the co-present `<router-decision>` block. |
| `none` / no decision block                                | Proceed inline; no next skill.                                              |

---

## Self-learning

This skill learns across runs via a lessons file. Resolve its path once, first hit wins:

1. `<project>/.claude/lessons/design-agency-routing.md` (preferred when inside a project)
2. `<this-skill-dir>/LESSONS.md` (fallback when there is no project context)

**At run START (read-only, fail-open):**

- Read the lessons file(s) that exist (load both if both do). If none exist, continue silently.
- Read only the last ~20 lines; treat each `- YYYY-MM-DD …` line as a standing constraint for this run.
- Never block on a missing file; absence just means "no lessons yet".

**At run END (append, only when warranted):**

- Append a lesson **only if** this run produced a _correction_ (the user fixed/redirected your output),
  a _gotcha_ (a non-obvious failure you had to work around), or a _durable insight_ worth reusing.
  Routine successful runs append nothing — keep the file high-signal.
- One physical line, exact format:
  `- YYYY-MM-DD <imperative fix or invariant> [ctx: design-agency-routing/<project-or-->]`
- Create the file (and parent dir) on first append; otherwise append. Never rewrite existing lines.
- De-dupe: if an equivalent rule already exists in the last ~20 lines, skip the append.

**Periodic harvest (non-autonomous):**

- A read-only sweep of `~/.claude/cache/design-agency/overrides.jsonl` can surface routing quality:
  tally `not_design` rows (hook false positives) and `inline` rows (engage-band over-triggers the user
  declined), grouped by `engagement_type` and `confidence` band.
- Accumulated patterns inform threshold tuning (`thresholds.ask`, currently 0.55) and the hook's
  `matched_signals`; append the finding as a lesson bullet so it informs future runs.
- Trigger: manual `/refine` invocation or the nightly Phase-5 lessons-harvest sweep.
- **Bridge note:** `continuity_inline` rows in `audit.jsonl` are already owned by `auto-model-routing`'s
  `router_loop.py` sil. Harvest `overrides.jsonl` only; do not re-aggregate rows the router loop
  already processes.
- `engagement_type` values in scope (harvest by all): `brand_project`, `deliverable_iteration`,
  `prototype`, `character_3d`, `asset`, `ops`, `unknown`.

Optional deterministic append (when a shell is available), instead of hand-writing the line:
`python3 ~/.claude/lib/self-improving-loop/sil/cli.py lessons-append \
  --file "<resolved-path>" --date "YYYY-MM-DD" --window "run" --note "<imperative rule>" --tweak "design-agency-routing/<project>"`
