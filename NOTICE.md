# NOTICE

This distribution combines original work under the MIT License (see `LICENSE`) with
third-party work under the Apache License, Version 2.0, and third-party work under the
MIT License.

## Provenance (every vendored component)

| Component | Upstream | Version | Commit |
|---|---|---|---|
| 18 Impeccable skills (`skills/adapt` … `skills/typeset`) | https://github.com/pbakaus/impeccable | v2.1.1 (`impeccable` SKILL 2.2.0) | not recorded at fork time |
| `skills/impeccable/reference/{craft-floor,operate,mode-operate,mode-persuade,mode-read}.md` | https://github.com/pbakaus/impeccable (`.claude/skills/impeccable/reference/`) | skill-v4.7.0 | `aeeb3d8c30b5f95aeeb3e893b0f1a308af8fdb8f` |
| `skills/taste-skill/` body (`SKILL.md` §0/§1/§9/§13/§14 + `references/` except below) | https://github.com/Leonxlnx/taste-skill | v2 (upstream now "v2 experimental", kept in taste-skill-classics) | `ce26fc25c0e5` |
| `skills/taste-skill/references/app-screens.md`, `app-styles.md` | https://github.com/Leonxlnx/taste-skill | v2.1.3 | `63aba5f43b5056758b15bbe7d683da8c86a7a7ad` |
| `skills/emil-design-eng/` (+ `references/animation-performance.md`, `review-animations.md`) | https://github.com/emilkowalski/skills | `main` (no tags) | `2d228630ba1446365f614a108cb8252f1feda202` |
| `skills/ui-ux-pro-max/` (`data/`, `scripts/`) | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill (`src/ui-ux-pro-max/`) | v2.15.0 | `a38d04c3d5c298c851dbe5e6ee1965ee3de42cb5` |
| `execution/enforce.py` rule set | ported from the author's own `brandbook/tworocks/tools/audit.sh` (MIT, same author) | — | — |

## Apache-2.0 components

The 18 Impeccable design skills bundled here are a fork:

```
skills/adapt/      skills/animate/    skills/audit/      skills/bolder/
skills/clarify/    skills/colorize/   skills/critique/   skills/delight/
skills/distill/    skills/harden/     skills/impeccable/ skills/layout/
skills/optimize/   skills/overdrive/  skills/polish/     skills/quieter/
skills/shape/      skills/typeset/
```

**Impeccable** is itself derived from Anthropic's `frontend-design` skill and is
distributed under the Apache License, Version 2.0.

You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under
the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. See the License for the specific language governing
permissions and limitations under the License.

### Modifications

Per Apache-2.0 §4(b), the following changes were made to the original files:

- `skills/impeccable/SKILL.md` — an agency binding preamble was prepended, replacing
  Impeccable's default context-resolution order with the agency's
  (`style_directive.md` first, then `visual_philosophy.md`, then `research_context.md`,
  falling back to Impeccable's `.impeccable.md` / `teach` flow only when those are absent).
  Reserved-token enforcement was made config-driven rather than hardcoded.
- All 18 skills were relocated from a standalone skills directory into this plugin's
  `skills/` tree, so they resolve as `design-agency:<name>`.
- Path references were rewritten to `${CLAUDE_PLUGIN_ROOT}` for portability.

No changes were made to the substance of the design guidance in the remaining 17 skills.

The v0.5.0 additions under `skills/impeccable/reference/` (`craft-floor.md`, `operate.md`,
`mode-operate.md`, `mode-persuade.md`, `mode-read.md`) are copied unmodified from
skill-v4.7.0 apart from a three-line HTML attribution comment at the top of each file.

## MIT components

`skills/taste-skill/` (`SKILL.md` + `references/` + `references/modes/`) is taste-skill v2,
vendored from:

```
skills/taste-skill/SKILL.md
skills/taste-skill/references/
skills/taste-skill/references/modes/
```

Copyright leonxlnx. Source: https://github.com/Leonxlnx/taste-skill @ `ce26fc25c0e5`,
distributed under the MIT License — compatible with this plugin's own MIT license; see
`LICENSE` for the MIT text.

### Modifications

- An agency binding preamble was prepended to `SKILL.md` (`<design-agency-binding>`),
  subordinating upstream defaults to `style_directive.md` / `visual_philosophy.md` and
  routing the three dials plus `TASTE_MODE` through the Creative Director.
- Upstream sections were relocated verbatim into `references/`:
  `references/engineering.md` — upstream §3 Architecture & Conventions through §8 Dark
  Mode Protocol; `references/design-systems.md` — upstream §2 Brief → Design System Map
  plus Appendices A-C; `references/vocabulary.md` — upstream §10 Reference Vocabulary;
  `references/redesign.md` — upstream §11 Redesign Protocol plus the upstream
  `skills/redesign-skill/SKILL.md` body; `references/block-library.md` — upstream §12
  Block Library contract; `references/modes/soft.md`, `references/modes/minimalist.md`,
  `references/modes/brutalist.md` — the upstream `skills/soft-skill`,
  `skills/minimalist-skill`, and `skills/brutalist-skill` bodies.
- Frontmatter `name` was kept as `taste-skill` so the skill resolves as
  `design-agency:taste-skill`; `description` was rewritten for this plugin's routing.
- A one-line pointer to the relocated content was added under the §0, §9, §13, and §14
  headings kept in `SKILL.md`.
- The v1 Self-learning block was retained, with its lessons path moved outside the
  plugin directory to `{AGENCY_STATE}/lessons/taste-skill.md`.
- The sibling upstream skills `soft-skill`, `minimalist-skill`, and `brutalist-skill`
  are bundled as reference modes under `references/modes/` with their frontmatter
  stripped.
- v0.5.0: `references/app-screens.md` is upstream v2.1.3 verbatim (attribution comment
  prepended); `references/app-styles.md` is a markdown digest of upstream
  `library/app.json`. The binding preamble now forks page vs app screen on
  `SURFACE_MODE`, and an agency note above §13 records that upstream 2.1.0 brought
  dashboards into scope. The upstream 2.1 scripts and assets (`draw.mjs`, `lint.mjs`,
  `inspect.mjs`, `app.css`, `charts.js`) are not bundled.

`skills/emil-design-eng/` is from https://github.com/emilkowalski/skills (MIT, copyright
Emil Kowalski). Modifications: agency frontmatter, Self-learning and Recommended-next-step
sections; v0.5.0 synced the body to `2d22863` and added the upstream
`animation-performance` and `review-animations` skills as `references/` (frontmatter
stripped; `review-animations.md` joins its SKILL.md and STANDARDS.md).

`skills/ui-ux-pro-max/` is from https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
(MIT). Modifications: agency binding preamble, I/O contract, Self-learning and `sil/`
sections in `SKILL.md`; the body's stack and domain lists follow v2.15.0. v0.5.0 removed
`data/design.csv`, `data/draft.csv` and `data/_sync_all.py` (deleted upstream in
`3da52ff1`, 2026-07-10: unused by the scripts and carrying prompt-shaped text) and the
stacks renamed upstream (`shadcn-ui` → `shadcn`, `tailwindcss` → `html-tailwind`).

## External tools (not bundled)

`img2threejs` (Apache-2.0, https://github.com/img2threejs/img2threejs) is invoked from
a host install at `~/.claude/skills/img2threejs` and is not distributed with this
plugin.
