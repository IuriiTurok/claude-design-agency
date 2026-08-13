# Changelog

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
so it loaded with *all* metadata silently dropped and could never trigger. Now quoted;
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
