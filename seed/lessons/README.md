# Agent lesson logs

Copied once to `{AGENCY_STATE}/lessons/`. Each QA agent appends here when a review turns
up a rule worth carrying into the next engagement:

| File | Written by |
|---|---|
| `style-enforcer.md` | style-enforcer — detection rules that caught (or missed) a real violation |
| `visual-qa.md` | visual-qa — grading calls worth calibrating against |
| `taste-guardian.md` | taste-guardian — originality/craft judgments and collisions found |
| `polish-inspector.md` | polish-inspector — Impeccable suggestions that were right, and ones clamped away |
| `motion-designer.md` | motion-designer — easing/duration choices that survived review |
| `emil-design-eng.md` | emil-design-eng — design-engineering calls made without project context |

These live in `{AGENCY_STATE}`, never in the plugin. **The plugin directory is read-only
at runtime** — an agent that appends into its own install directory loses everything on
the next update and cannot be distributed. If a lesson is durable enough to belong to the
agency rather than one engagement, promote it into `lessons_learned.md`.

Append-only. One entry per lesson, dated, stating the rule — not the anecdote.
