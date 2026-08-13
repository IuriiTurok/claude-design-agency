---
name: refine
description: Orchestrate the full diagnose→fix→polish pipeline on a UI — runs audit → layout → typeset → colorize → harden → polish in order, with a confirmation gate between every stage. Use when the user wants a full polish pass, says "diagnose then fix then polish", "tighten this UI end to end", "run the whole refinement chain", or hands you a page/component that needs more than one kind of work. Skip for a single targeted fix (just the palette, just the spacing) — invoke the specific micro-skill (/colorize, /layout, …) directly instead.
version: 1.1.0
user-invocable: true
argument-hint: "[target (feature, page, component...)]"
---

Run the canonical **diagnose → fix → polish** pipeline against one target, gating between stages so the user stays in control. `/refine` is the design-side analogue of the session lifecycle chain (`prime → work → wrap → ship`): where each micro-skill is a single point transform, `/refine` is the orchestrator that sequences them.

This skill **dispatches the existing micro-skills — it does not reimplement them.** Each stage is a real `Skill`/`Agent` invocation of the corresponding command; their logic, references, and reports stay the source of truth.

## MANDATORY PREPARATION

Read `${CLAUDE_PLUGIN_ROOT}/skills/impeccable/context-protocol.md` and follow the Context Gathering Protocol once, up front. If no design context exists, run `/impeccable teach` first. The gathered context is passed through to every child stage so they don't each re-prompt.

---

## Inputs

- **`target`** (required) — the feature/page/component path or selector to refine. Passed verbatim as the `[target]` arg to every child skill.
- **`context`** (optional) — design-context already in hand; otherwise the preparation step above supplies it.
- **`scope`** (optional) — a subset of the chain: `--from typeset` (start mid-pipeline), `--only audit,polish`, or skip stages the audit scored as already-good.

## Outputs

- The refined deliverable — each child stage edits the source files in place.
- A **consolidated refine report**: the `audit` scored report (P0–P3) up front, then a short **per-stage change log** (one block per stage: what it changed, what it skipped), ending with the `polish` checklist result.
- A `lessons.md` append for any child stage that hit a gotcha (see Self-learning).

## Pipeline (fixed order)

```
audit → layout → typeset → colorize → harden → polish
```

Measure first (`audit`), fix structure (`layout`), then type (`typeset`), then color (`colorize`), then real-world robustness (`harden`), then the final micro-pass (`polish`). This honors the standing convention that **`/polish` is always the last step** — already encoded in both `audit` and `critique`.

`/refine` is seeded naturally by a diagnostic: both `/audit` and `/critique` point here ("Next: `/refine`"). If you arrive from `/audit`, reuse its scored report instead of re-running stage 1.

## Dispatch & gates

1. **Run `audit` first.** Surface its P0–P3 report and Audit Health Score. **Gate 1:** confirm scope with the user — they may drop any stage whose dimension audit scored as already-good (e.g. skip `colorize` if Theming scored 4).
2. **For each remaining stage in order, dispatch the corresponding micro-skill** (`/layout`, `/typeset`, `/colorize`, `/harden`, `/polish`), passing `target` + `context`. Do not inline the transform — call the skill.
3. **Confirmation gate between every stage** (default). After a stage finishes, show its diff/summary and ask before proceeding. The user may **approve**, **skip** the next stage, or **stop** the run. A `--yolo` flag chains all stages without gates for trusted runs.
4. **Motion & Feedback gate (after `polish`).** The mechanical chain fixes structure/type/color but never adds motion, so a refined page can be pixel-perfect yet completely static. If `audit` scored the **Feedback & Motion** dimension low (or flagged missing feedback / jarring transitions / no entrance choreography), surface ONE optional gate: *"This page has little/no motion — run `/animate` to add feedback + transitions (clamped to the project motion budget)? [run / skip]."* Consistent with the directional-skill rule this is **offered, never auto-applied** — but it makes motion visible at the end of every run instead of permanently opt-in. If approved, dispatch `/animate` with `target` + `context`, then re-run `/polish` on the result.
5. After `polish` and the motion gate, emit the consolidated report and **suggest `/critique`** for a subjective second opinion — the one dimension `/refine` deliberately does *not* auto-run, since it is judgment-heavy and gated differently.

## Picking the right tone skill

The fixed chain is the **mechanical fix pipeline only**. It deliberately excludes the **directional** skills — a human must choose a direction, not have one applied by default. When the audit or the user signals a tonal need, suggest the right one rather than folding it in:

- *Everything feels safe / timid* → `/bolder`. *Specifically the palette is dull* → `/colorize` (already in-chain).
- *Too loud / over-intense* → `/quieter`. *Too much stuff / cluttered* → `/distill` (run distill before quieter if both).
- *Wants personality / fun* → `/delight`. *Wants functional motion* → `/animate`.

Also excluded: `shape` (pre-code planning), `adapt` / `optimize` (run on demand for cross-device / perf), `overdrive` (an explicit ambition choice).

## Boundaries

`/refine` is the **fix** pipeline; `/critique` is the **judge**. They compose: diagnose with `/audit` or `/critique` → fix with `/refine` → re-`/critique` to verify. `/refine` never makes directional taste calls itself (see above) and never auto-runs `/critique`.

**NEVER**:
- Reimplement a child skill's logic inline — always dispatch the actual command.
- Chain stages without gates unless `--yolo` was passed.
- Run a stage the user skipped at Gate 1, or continue after the user says stop.
- Fold in a directional skill (`bolder`/`quieter`/`distill`/`delight`/`animate`/`overdrive`) automatically — suggest, don't apply.
- Re-run `audit` from scratch when arriving from a fresh `/audit` report — reuse it.

After the run, tell the user:

> Each stage ran in order with a checkpoint between them. Re-run `/audit` to see the score improve, or `/critique` for a subjective gut-check before ship.

## Self-learning

This skill learns across runs via a lessons file. Resolve its path once, first hit wins:
1. `<project>/.claude/lessons/refine.md`  (preferred when inside a project)
2. `{AGENCY_STATE}/lessons/refine.md`  (fallback when there is no project context)

**At run START (read-only, fail-open):**
- Read the lessons file(s) that exist (load both if both do). If none exist, continue silently.
- Read only the last ~20 lines; treat each `- YYYY-MM-DD …` line as a standing constraint for this run.
- Never block on a missing file; absence just means "no lessons yet".

**At run END (append, only when warranted):**
- Append a lesson **only if** this run produced a *correction* (the user fixed/redirected your output), a *gotcha* (a non-obvious failure you had to work around — e.g. a stage that should have been skipped, a bad dispatch order), or a *durable insight* worth reusing. Routine successful runs append nothing — keep the file high-signal.
- One physical line, exact format:
  `- YYYY-MM-DD <imperative fix or invariant> [ctx: refine/<project-or-->]`
- Create the file (and parent dir) on first append; otherwise append. Never rewrite existing lines.
- De-dupe: if an equivalent rule already exists in the last ~20 lines, skip the append.

Optional deterministic append (when a shell is available), instead of hand-writing the line:
`python3 "${SIL_KERNEL:-$HOME/.claude/lib/self-improving-loop}"/sil/cli.py lessons-append \
  --file "<resolved-path>" --date "YYYY-MM-DD" --window "run" --note "<imperative rule>" --tweak "refine/<project>"`

Per-stage gotchas belong to the child skill's own lessons file, not here — `/refine` only logs orchestration-level lessons (sequencing, gating, scope decisions). Durable AI-slop tells go to the canonical ban list (`${CLAUDE_PLUGIN_ROOT}/skills/impeccable/reference/ai-slop-bans.md`), not here.

Next: `/critique` — subjective second opinion once the mechanical fix chain is done.
