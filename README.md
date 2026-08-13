# design-agency

A 23-role virtual design agency for Claude Code, with hard QA gates.

Most design help from an LLM stops at "here is a landing page." This plugin models the
part that actually produces quality: a **workflow with gates**. It detects design intent
in your prompt, classifies the engagement, dispatches the right role, and then refuses to
call a deliverable done until a mechanical style enforcer reports zero violations and a
visual QA pass grades it ≥3/5 on coherence, originality, craft, and functionality.

The gates are the point. A check that exists only in the conversation transcript did not
happen — every QA agent writes its report to disk.

---

## Install

```
/plugin marketplace add IuriiTurok/claude-design-agency
/plugin install design-agency@design-agency-mp
```

Restart Claude Code. Hooks activate automatically from `hooks/hooks.json`.

Only `python3` (stdlib) is required. Everything else is optional — see
[Optional dependencies](#optional-dependencies).

## What you get

| Component        | Count | What it does                                                                                                                                                                                             |
| ---------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Skills**       | 23    | 3 agency skills (orchestrator, routing, taste) + 2 design-intelligence skills + the 18 Impeccable design skills (`design-agency:layout`, `:typeset`, `:colorize`, `:animate`, `:critique`, `:polish`, …) |
| **QA subagents** | 5     | `style-enforcer` and `visual-qa` (hard gates) · `taste-guardian`, `polish-inspector`, `motion-designer` (advisory)                                                                                       |
| **Roles**        | 23    | Creative director, logo designer, brandbook designer, copywriter, researcher, prototype lead, character designer, project manager, …                                                                     |
| **Hooks**        | 2     | Design-intent detection on every prompt · a post-edit gate on `ui/*.html`                                                                                                                                |

## How it works

1. **`design-intent.py`** (UserPromptSubmit) scores each prompt for design signals. Above
   threshold it injects a `<design-agency-decision>` block classifying the engagement —
   new brand project, deliverable iteration, one-off asset, prototype, character work.

2. **`design-agency-routing`** consumes that block and asks whether to engage, or
   auto-engages in repos that opt in.

3. **`design-agency`** orchestrates phases: discovery → strategy → concept → execution →
   **QA** → handoff, dispatching roles from `roles/`.

4. **`ui-edit-gate.py`** (PostToolUse) fires after any edit to a `ui/*.html` file and
   demands `style-enforcer` before the edit counts as complete — so iteration cannot
   quietly bypass compliance.

## Configuration

### Brand config

The agency ships **brand-neutral**. To have it protect your own brand's tokens from
bleeding into client work, declare them in `~/.claude/design-agency/config.json`:

```json
{
  "brand": {
    "agency_name": "Your Studio",
    "agency_tagline": "Your tagline",
    "own_brand_folders": ["your-studio/"],
    "reserved_tokens": {
      "fonts": ["Your Display Font"],
      "colors": ["#FF6B35"]
    },
    "carve_outs": { "some-project": ["Inter"] }
  }
}
```

- `own_brand_folders` — the only dirs where your reserved tokens are allowed.
- `reserved_tokens` — fonts and colors that belong to your brand. Used anywhere else,
  they are a violation.
- `carve_outs` — documented per-project exceptions.

Resolution merges **plugin defaults ← global config ← `<repo>/.claude/design-agency.json`**
(`brand` key), later tiers winning key by key. Inspect the result with:

```
python3 "${CLAUDE_PLUGIN_ROOT}/execution/state_paths.py" --brand
```

Leave `reserved_tokens` empty and bleed-through checks are skipped entirely — the agency
never invents a reserved list.

### Routing config

Per-repo, in `<repo>/.claude/design-agency.json`:

```json
{
  "disabled": false,
  "ask_threshold": 0.55,
  "extra_signals": ["brand", "palette", "mockup"]
}
```

`#noagency` / `#nodesign` in a prompt suppresses the hook for that turn; `#agency` forces
engagement. `DESIGN_AGENCY_DISABLE=1` turns both hooks off entirely.

Tune `ask_threshold` by reviewing `~/.claude/cache/design-agency/audit.jsonl` — a high
`not_design` rate means the threshold is too low.

## Adopting in a new project

**None of this is required.** With no configuration at all the plugin still works: the
hook classifies prompts by keyword heuristics, and state lands in
`~/.claude/design-agency/`. The three levers below buy you progressively stronger routing,
and matter most in a repo where design work is the norm rather than the exception.

The failure they prevent is real and specific. An audit of 58 sessions in an
agency-operated repo found the workflow was bypassed in nearly every one — not because
the skills were wrong, but because nothing routed sessions into them. Keyword heuristics
alone lose to a prompt like *"fix the spacing on the pricing card"*.

**1. Tune the classifier** — `<repo>/.claude/design-agency.json`

Lower `ask_threshold` in a design-heavy repo, and add vocabulary the heuristics miss:

```json
{ "ask_threshold": 0.45, "extra_signals": ["brand", "palette", "mockup"] }
```

**2. Route every session** — a stanza in `<repo>/AGENTS.md`

This is the lever that fixes the bypass problem, because it acts on sessions the hook
never scores. Declare the bootstrap and the engagement classes:

```markdown
## Mandatory Context Bootstrap

Before any work in this repo (read-only actions only until complete):

1. Invoke the `design-agency` skill — orchestrator, workflow, gates, state resolution.
2. Classify the session with the Engagement Router below, then follow that protocol.

## Engagement Router (classify EVERY session before acting)

Role files live at `{AGENCY_ROOT}/roles/` — the `design-agency` skill resolves
`{AGENCY_ROOT}`; never hardcode a path to the plugin.

| Engagement type | Signals | Protocol |
|---|---|---|
| New brand project | new client, brand identity, logo, brand book from scratch | Full Phases 1–6 |
| Deliverable iteration | editing an existing `<project>/ui/*.html` | Maintenance & Iteration Mode |
| Product prototype | app replication, multi-screen prototype | `roles/prototype_lead.md` |
| One-off asset | favicon, avatar, social image | `roles/asset_designer.md` |
| Ops / release / git | release notes, commit/deploy, file moves | no design gates |
```

**3. Force auto-engage** — an optional `DesignAgencyAgent/` marker

`hooks/design-intent.py` walks up from the working directory looking for
`DesignAgencyAgent/master_agent.md`. If it finds one, the session engages the agency
unconditionally (`source: repo_agents_md`) regardless of what the prompt says. **Only the
file's existence is checked — its contents are never read**, so an empty file is a valid
marker:

```bash
mkdir -p DesignAgencyAgent && touch DesignAgencyAgent/master_agent.md
```

Creating that directory also switches the state chain to repo-local: `style_library.md`
and `logo_feedback_log.json` then live in the repo instead of `~/.claude/design-agency/`
(see the State table below), which is what you want when the agency's memory should be
versioned with the project rather than with the machine.

### State

The plugin directory is **read-only at runtime**. Everything writable resolves through
`execution/state_paths.py`:

| File                      | Chain (first that exists wins)                                                                                 |
| ------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `style_library.md`        | `<repo>/DesignAgencyAgent/style_library.md` → `~/.claude/design-agency/style_library.md`                       |
| `lessons_learned.md`      | `<repo>/lessons_learned.md` → `~/.claude/design-agency/lessons_learned.md`                                     |
| `logo_feedback_log.json`  | `<repo>/DesignAgencyAgent/execution/logo_feedback_log.json` → `~/.claude/design-agency/logo_feedback_log.json` |
| `config.json`, `lessons/` | `~/.claude/design-agency/`                                                                                     |

`DESIGN_AGENCY_STATE_DIR` overrides the whole chain. Deliverables and QA reports go to
the project repo; agency memory goes to state; nothing is ever written back into the
plugin.

## What it reads and writes

Stated plainly, because a UserPromptSubmit hook deserves it:

- **It reads every prompt you type.** It has to, to classify design intent. Classification
  is pure local Python stdlib — pattern matching and a scoring heuristic. **No network
  calls, no model calls, no telemetry.**
- **It writes a local audit log** at `~/.claude/cache/design-agency/audit.jsonl` and
  `overrides.jsonl`, so you can tune the threshold. Local only, never transmitted.
- **It ships executable hooks** — two Python scripts, both invoked via
  `${CLAUDE_PLUGIN_ROOT}`, both wrapped so a failure can never block your prompt.

## Optional dependencies

| Dependency                               | Purpose                           | Without it                                   |
| ---------------------------------------- | --------------------------------- | -------------------------------------------- |
| `GEMINI_API_KEY` + `google-generativeai` | Logo generation                   | Logo roles produce SVG by hand               |
| vision venv (`.venv-vision`)             | Saliency heatmaps, visual diffing | Heatmap analyst is skipped (advisory anyway) |
| `node` + `npx`                           | marp decks, svgo, sharp           | Presentation/asset roles degrade to HTML     |
| chrome-devtools MCP                      | visual-qa full-page screenshots   | visual-qa grades from source only            |
| `~/.claude/lib/self-improving-loop`      | Self-improving rubric loops       | Loops print a notice and exit cleanly        |

## Development

Work against a local checkout instead of the published marketplace:

```
git clone https://github.com/IuriiTurok/claude-design-agency
/plugin marketplace add ./design-agency
/plugin install design-agency@design-agency-mp
```

Seed the writable state dir and check optional deps (optional — paths are
created lazily on first write):

```
bash "${CLAUDE_PLUGIN_ROOT}/bin/setup-state.sh"
```

Run the suites:

```
bash tests/run.sh                                  # hook classifier + ui-edit gate
python3 skills/design-agency/sil/test_measure.py   # sil measure()
claude plugin validate . --strict
claude plugin validate .claude-plugin/plugin.json --strict
```

## License

MIT — see [`LICENSE`](LICENSE).

The 18 bundled Impeccable design skills are Apache-2.0, derived from Anthropic's
`frontend-design` skill. See [`NOTICE.md`](NOTICE.md) for attribution and the list of
modifications.
