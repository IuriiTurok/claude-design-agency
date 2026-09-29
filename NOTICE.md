# NOTICE

This distribution combines original work under the MIT License (see `LICENSE`) with
third-party work under the Apache License, Version 2.0, and third-party work under the
MIT License.

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

## External tools (not bundled)

`img2threejs` (Apache-2.0, https://github.com/img2threejs/img2threejs) is invoked from
a host install at `~/.claude/skills/img2threejs` and is not distributed with this
plugin.
