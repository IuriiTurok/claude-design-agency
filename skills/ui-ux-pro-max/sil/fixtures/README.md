# sil fixtures — synthetic saved-project corpus

Tiny, deterministic stand-ins for persisted design systems (the Master +
Overrides pattern `scripts/design_system.py persist=True` writes). The sil
adapter (`../ui-ux-pro-max_loop.py`) scores a candidate reasoning-rule edit
against this corpus offline, so `--dry-run` can compute a **projected
override-rate** without touching any real persisted project.

Each `project_*.json` captures one saved project:

```json
{
  "project": "<name>",
  "rule_id": "<ui-reasoning.csv No>",     // the reasoning rule that generated the Master
  "fields": {                              // generated design-system field -> generated value
    "pattern": "...", "style": "...", "color_mood": "...",
    "typography_mood": "...", "key_effects": "..."
  },
  "overrides": {                           // field -> user-edited value (a kept field is absent)
    "style": "..."
  }
}
```

**Override-rate** for a project = `len(overrides) / len(fields)` (fraction of
generated fields the user edited rather than kept). Lower is better. The
corpus override-rate is the mean across projects. A reasoning rule whose
targeted field is overridden in >= the threshold fraction of its projects is a
`propose()` candidate: the candidate edits that field's default so the
projected override-rate drops.

These are NOT real persisted projects and never become one — they exist only so
the offline gate + projected metric are computable in-loop. Real override-rate
is realized later on projects persisted since a pending row's window (`measure`).
