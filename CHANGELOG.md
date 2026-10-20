# Changelog

## 0.5.0 (2026-10-20)

**Product UI is a first-class track.** Most real engagements are iterations on product
apps (dashboards, tables, KPI rows in React/Vue/Svelte code), yet the agency modelled only
the four brand deliverables. New `roles/product_ui_lead.md` owns the Operate surface:
the directive comes from `directive_path` in `.claude/design-agency.json`, rules from
taste-skill 2.1 `references/app-screens.md` (vendored, MIT) and Impeccable's
`craft-floor.md` / Operate mode (vendored, Apache-2.0), gates are `enforce.py --surface
operate` → style-enforcer → visual-qa on an Operate rubric. Auth-gated apps are verified
on a throwaway harness page served by the app's own dev server, never by signing in.
The orchestrator, taste-skill and the routing skill all fork on `SURFACE_MODE`
(persuade | operate | read | experience); landing-page tells apply only to persuade.

**Gates dispatch by their registered names.** The edit-gate hook and the orchestrator
dispatched `style-enforcer`, but the agents are registered as
`design-agency:style-enforcer` (and so on), so dispatch failed or fell back to an inline
pass. Every dispatch site is fixed, a test asserts the hook's name matches an agent, and
the orchestrator now states that an inline pass is not the gate and that the final
enforcer and VQA runs are sequential. `ui-edit-gate.py` also gates product-UI files
(`*.tsx|jsx|vue|svelte|css|scss`) when the repo config declares `directive_path` or
`ui_globs`, or in an engaged session with a directive up the tree.

**visual-qa can see.** It gets the built-in browser and Claude in Chrome tools with a
capability ladder, serves pages over a local http server instead of `file://`, captures
1440px and 390px in light and dark, runs keyboard and console checks, and returns
`UNMEASURED` (never PASS) when no browser exists. Reports have standard names,
`<reports_dir>/<gate>_report_<name>.md` with a `Verdict:` line, and
`execution/check_reports.py` checks presence, freshness and verdict.

**A mechanical style enforcer.** `execution/enforce.py` ports the generic rules of the
brandbook repo's `audit.sh` into a stdlib, directive-driven linter (14 rules; palette and
font allowlists, token files and surface mode read from `style_directive.md`; `--json`,
`--report`, `--list-rules`). It also catches orphan classes applied from JS string
literals, which `audit.sh` missed. style-enforcer runs it first and reports its findings
verbatim; Impeccable's `detect` is an optional offline second detector.

**Brand Overrides and DESIGN.md.** `style_directive.md` gains a `## Brand Overrides`
section: one `allow <rule-id>` line per deliberate identity choice (mono figures,
near-black + one accent, DIN 5008 dashes), honoured by the script and by taste-guardian
and visual-qa. The Creative Director can also emit a Google-format `DESIGN.md`
(`assets/examples/DESIGN_example.md`) generated from the directive.

**Classifier false positives.** `hooks/design-intent.py` now matches phrases on word
boundaries ("poster" no longer matches "posterior"), strips path tokens before scoring
(the repo name "brandbook"), needs a creation verb for "brandbook"/"logo" and character
context for "3d model", stops "design system" double-counting the verb "design", and has
an engineering penalty (0.45) that can cancel a Tier-A hit, a veto at four distinct
engineering terms or on prompts about the plugin's own machinery, per-repo
`negative_signals`, bare-string `extra_signals`, and a `product_ui` engagement type. One
answered question now suppresses only that engagement type for the session; the session
goes silent only after "Use design agency" (logged by `log_override.py`, which the
routing skill calls by the absolute `plugin_root` the hook emits; the old relative path
left 75% of asks unlogged). In a repo with the brandbook marker, an ask is upgraded to
engage instead of engaging every prompt. Headless sessions take a logged default.
`DESIGN_AGENCY_CACHE_DIR` and hermetic test runners keep fixture runs out of the real
telemetry (they had been two thirds of `audit.jsonl`). 23 new fixtures.

**One spec per QA gate.** `agents/<gate>.md` is authoritative (role-only content merged);
`roles/<gate>.md` are pointers. Wrong "Model: opus" claims, unresolved `{AGENCY_ROOT}` and
relative paths in subagent prompts, and dead references (`agent-browser-verify`,
`chrome-devtools-mcp`, `a11y-debugging`, `figma:create-design-system-rules`, slash-named
official skills) are fixed; official Anthropic skills are optional with named fallbacks.
`tests/test_refs.py` keeps it that way and checks every skill and agent frontmatter.

**Vendored skills resynced, provenance recorded.** taste-skill app-screens/app-styles at
v2.1.3; Impeccable craft-floor, operate and mode files at skill-v4.7.0 (the 18 forked
skills are not restructured); emil-design-eng at `2d22863` plus its animation-performance
and review-animations skills as references; ui-ux-pro-max v2.5.0 → v2.15.0 data and
scripts (stack renames `shadcn-ui` → `shadcn`, `tailwindcss` → `html-tailwind`; the
unused, prompt-shaped `design.csv` / `draft.csv` / `_sync_all.py` removed as upstream did).
`NOTICE.md` has a provenance table with version and commit for every vendored component.

**Lessons promoted** from shipped work into the files that need them: harness pages,
browser serving, script-edits for large showcase files, CSS pitfalls
(`skills/impeccable/reference/css-pitfalls.md`), component/icon inventory before adding,
logo masters only, scoped greps and strictest readings, DACH font self-hosting and DIN
5008 overrides, bounded screenshot reads, and character rigging gotchas.
`hooks/hooks.json` quotes `${CLAUDE_PLUGIN_ROOT}` (strict validation).

## 0.4.1 (2026-10-14)

**The design-intent hook ignores harness events.** Background-task completions and
scheduled fires reach UserPromptSubmit as if they were prompts, and an agent report that
mentions a brand book or a landing page scored as design intent, so the session was told
to invoke `design-agency-routing` for text nobody typed. `hooks/design-intent.py` now
returns silently for prompts that open with `<task-notification`, `<scheduled-task` or
`[SYSTEM NOTIFICATION`. New fixture `task-notification-none` covers it.

## 0.4.0 (2026-09-29)

**Taste is applied at generation time, not only checked at QA.** The v1 anti-slop list
was easy to skim past because it only showed up as a checklist at the end. v2 adds a
Design Read before any code is written, hard bans with objective tells instead of
taste-based judgment calls, and a pre-flight the UI/UX Designer runs on itself before
handing off — so the agency now applies taste while generating, and QA re-verifies
rather than discovering problems for the first time.

**`skills/taste-skill/` is now taste-skill v2**, vendored from
https://github.com/Leonxlnx/taste-skill at `ce26fc25c0e5` (MIT, copyright leonxlnx; see
`NOTICE.md`). `SKILL.md` keeps the agency binding preamble plus upstream §0 Brief
Inference, §1 Three Dials, §9 AI Tells (including the em-dash ban), §13 Out of Scope,
and §14 Final Pre-Flight; the v1 Self-learning block is retained with its fallback path
moved to `{AGENCY_STATE}/lessons/taste-skill.md`. Everything else moves to
`references/`: `engineering.md` (§3-§8), `design-systems.md` (§2 + Appendices A-C),
`vocabulary.md` (§10), `redesign.md` (§11 plus the upstream redesign-skill body),
`block-library.md` (§12), and `references/modes/{soft,minimalist,brutalist}.md` (the
upstream soft/minimalist/brutalist skill bodies). The skill carries no dial baseline —
`DESIGN_VARIANCE`, `MOTION_INTENSITY`, `VISUAL_DENSITY`, and the new `TASTE_MODE`
(soft | minimalist | brutalist | none) are declared by the Creative Director in
`<project>/visual_philosophy.md`, and the UI/UX Designer writes a new
`<project>/taste_preflight_<deliverable>.md` artifact (the §14 result) before QA.

**Generation roles now read taste before generating, not after.**
`roles/creative_director.md` sets the three dials plus `TASTE_MODE` (v2 §1
inference/presets and modes) and records the §2 brief → design-system decision in a new
"Design System Foundation" section of `style_directive.md`. `roles/uiux_designer.md`
gains a Taste Pass before `/frontend-design` (a Design Read, plus a §13 scope check that
routes dashboards and product UI to `prototype_lead.md` and `ui-ux-pro-max`), v2 layout
rules that replace the old fixed 9-section list (at least 4 layout families, hero
discipline, nav capped at 80px, one accent, one radius, page theme lock), the §9.F/§9.G
items in its anti-slop checklist, and a pre-flight (§14) step immediately before QA.

**3D generation moves from prep-only to full ownership.** `roles/character_designer.md`
now owns image-to-3D via the external `img2threejs` skill
(https://github.com/img2threejs/img2threejs at `6e60b5e22419`, Apache-2.0, installed on
the host at `~/.claude/skills/img2threejs`, not bundled): code-only procedural
Three.js/TypeScript factories built from a reference image through gated passes, output
under `<project>/3d/<name>/`, with their own turntable and comparison gates running
before `visual-qa`. This replaces the previous "prep only, no 3D modeling" limitation.

**QA gates re-verify taste independently instead of re-deriving it.**
`agents/taste-guardian.md` and `roles/taste_guardian.md` replace the old 12-item
anti-slop list with the v2 §9.A-§9.G tells and Consistency Locks, add a §14 craft
checklist that independently re-verifies the pre-flight, read `TASTE_MODE`, and resolve
bleed-through tokens via `state_paths.py --brand` instead of hardcoded literals;
taste-guardian's tools gain `Bash` so it can run `state_paths.py`,
`archive_taste_report.py`, and `emit_candidate.py`. `agents/style-enforcer.md` and
`roles/style_enforcer.md` add a mechanical "Taste v2 objective tells" table (em-dash
count, `h-screen` hero, nav over 80px, divider overuse, scroll cues, version labels,
section-number eyebrows, multiple accents, multiple radius scales, mixed theme
sections). `agents/visual-qa.md` adds an AI-tells scan before grading, anchors
Originality on layout-family count, consumes the pre-flight file, and now caps Craft at
2 — an automatic fail — when an em-dash is found. `agents/motion-designer.md` and
`roles/motion_designer.md` add the v2 §5.D forbidden animation patterns, make reduced
motion mandatory above `MOTION_INTENSITY` 3, and check for "motion claimed, motion
shown".

**Routing and hooks catch up to the 3D track.** `skills/design-agency/SKILL.md` updates
its Binding Contract, Engagement Router (adding a 3D row for `character_designer` +
`img2threejs`), Phase 2/Phase 5 wording, and Layer 5 list; `roles/_official_skills.md`
gains "Bundled design-intelligence skills" (taste-skill v2) and "External skills
(installed on the host, not bundled)" (img2threejs); `hooks/design-intent.py` gains five
`character_3d` TIER_A signals ("3d model", "image to 3d", "image-to-3d", "three.js
model", "procedural model"); `tests/fixtures.jsonl` gains 2 fixtures (26 total, all
passing); `skills/impeccable/reference/ai-slop-bans.md` gets a one-line update pointing
the dials at `visual_philosophy.md`.

**Formatting note.** The maintainer's prettier pre-commit hook reformatted every touched
markdown file in this release (`*emphasis*` to `_emphasis_`, list spacing, table
alignment), which accounts for a large share of the diff beyond the content changes
above.

## 0.3.1 (2026-08-20)

**The state-dir override now actually moves all the state.** `DESIGN_AGENCY_STATE_DIR` is
the documented override — the README, `bin/setup-state.sh`, every `roles/*.md`, the main
`SKILL.md`, and the canonical resolver in `execution/state_paths.py` all agree on it. But
the two self-improving-loop scripts never went through the resolver: they read a
`DA_AGENCY_STATE` variable that appears nowhere else in the plugin and nowhere in the
shared kernel. Both defaulted to the same `~/.claude/design-agency`, so nothing looked
wrong — until you set the documented override, at which point the taste ledger and the
archived taste-reports kept writing to the default while everything else relocated.

`skills/design-agency/sil/design-agency_loop.py` and `sil/archive_taste_report.py` now
import `state_paths` and call `resolve("sil")`. Because `sil` is not a repo-relative name,
`resolve()` skips the repo-local tier and returns the historical path when no override is
set — so default behavior is byte-identical and `DA_AGENCY_STATE` is gone from the tree.

## 0.3.0 (2026-08-13)

**The pipeline orchestrator ships.** `refine` — the skill that sequences
`audit → layout → typeset → colorize → harden → polish` with a gate between every stage —
was referenced by nine bundled skills but never shipped with them; `audit` and `critique`
both ended with "Next: `/refine`" pointing at nothing. Installing the plugin from GitHub
got you nine dangling references. It is now `skills/refine/`, with its two host-machine
references (`~/.claude/skills/impeccable/context-protocol.md` and a private planning doc)
rewritten to `${CLAUDE_PLUGIN_ROOT}` and to inline prose.

**Adoption is documented.** A new README section covers the three levers for using the
agency in your own repo — classifier config, an `AGENTS.md` routing stanza, and the
optional `DesignAgencyAgent/master_agent.md` auto-engage marker. That marker is what
`hooks/design-intent.py` has always detected, and it had never been written down.

**Fixes.** `bin/setup-state.sh` pointed installers at the private source repo, which is a
404 for everyone but the author. `license` now reads `MIT AND Apache-2.0` in both
manifests, matching what `NOTICE.md` has always described.

## 0.2.0 (2026-08-13)

**Consolidation + first publishable release.**

The 18 Impeccable skills move from `vendor/impeccable/` to first-class plugin skills
under `skills/`, so one install now provides all 23 (`design-agency:layout`,
`:typeset`, `:polish`, …) instead of leaving them scattered across three locations —
`~/.claude/skills/`, the vendored fork, and a project-scoped copy that shadowed both.
`vendor/` is gone; the ban list (`ai-slop-bans.md`), context protocol, and sil tooling
that previously lived only in the loose global copy are now bundled.

**Brand enforcement is configuration, not hardcoded strings.** Own-brand folders,
reserved fonts/colors, per-project carve-outs, and the agency's own name/tagline move
into a `brand` block resolved by `execution/state_paths.py --brand`, merging plugin
defaults ← `{AGENCY_STATE}/config.json` ← `<repo>/.claude/design-agency.json`. The
plugin ships neutral: with no reserved tokens declared, bleed-through checks are skipped
rather than guessed at. Previously the enforcer, the anti-pattern canon, the Impeccable
binding preamble, and six role files each carried their own copy of the literals.

**Fixed: `harden` had unparseable YAML frontmatter** (an unquoted `production-ready:`),
so it loaded with _all_ metadata silently dropped and could never trigger. Now quoted;
all 23 skills verified to parse.

**Portability.** Removed the one hardcoded absolute home path. Replaced eight absolute
plugin self-references with `${CLAUDE_PLUGIN_ROOT}` —
these would all have broken under a marketplace install. The five `references/*-lessons.md`
append targets did not exist and violated the plugin's own read-only-root rule; agent
lesson logs now write to `{AGENCY_STATE}/lessons/`. The self-improving-loop kernel is now
an optional import that degrades with a message instead of an `ImportError` traceback,
overridable via `SIL_KERNEL`. The router continuity log no longer assumes `jq` is present.

**Licensing.** Added `LICENSE` (MIT) and the `NOTICE.md` that the Apache-2.0 Impeccable
frontmatter had referenced since 0.1.0 without it existing, including the §4(b) list of
modifications. All 18 bundled skills now carry `license:` frontmatter. `plugin.json`
gains `homepage`, `repository`, `license`, and `keywords`; both manifests pass
`claude plugin validate --strict`.

**Client data removed** from the distributed package: seeded style library, logo
generation history, and agency style directives are replaced with generic starters and a
worked example directive; provenance is recorded by engagement type rather than client
name. `.env` is now gitignored (`generate_logo.py` invites one at the plugin root).

Also adopted in this release: `emil-design-eng`, `taste-skill`, and `ui-ux-pro-max`
(previously loose global skills).

## 0.1.2 (2026-06-14)

Skill-quality pass: both SKILL.md descriptions optimized for triggering — design-agency-routing gains a keyword discovery-fallback (fires the agency in repos with no AGENTS.md, the original audit root cause), and both add explicit Skip clauses. Bodies restructured for progressive disclosure: inline logging one-liners extracted to scripts/ (log_override.py, log_router_continuity.sh), and the orchestrator's long tables moved to references/ (anti_patterns, completeness_matrix, role_roster). Test fix: the brandbook auto-engage fixture is now hermetic (temp marker repo) instead of depending on a real repo path that moved between sessions.

## 0.1.1 (2026-06-11)

Heuristic tuning from first live session: engineering-term suppression now uses word-boundary matching (bare substring checks misfired — "ci" matched "social", "test" matched "testimonial") and a broader term list (tests, endpoint, refactor, lint, schema, sdk, server, pull request, type-check). Fixes the known false positive where a lone design phrase inside an engineering prompt ("add api tests for the color palette endpoint") triggered the ask. 4 regression fixtures added.

## 0.1.0 (2026-06-11)

Initial port of the agency from its origin repo (24 roles, 5 QA-gate agents, 2 skills, 2 hooks, vendored Impeccable fork).
