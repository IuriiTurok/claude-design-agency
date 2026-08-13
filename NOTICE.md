# NOTICE

This distribution combines original work under the MIT License (see `LICENSE`) with
third-party work under the Apache License, Version 2.0.

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
