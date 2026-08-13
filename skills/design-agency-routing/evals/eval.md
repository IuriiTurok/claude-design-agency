# design-agency-routing — eval cases

Rubric criterion 9: pass/fail signal for the router's band-dispatch logic.
Each case lists: **input** (injected context), **assertion** (observable output),
and **PASS / FAIL** criterion.

---

## Case 1 — band "engage" triggers agency invocation

**Input:** The injected context contains a `<design-agency-decision>` block with
`"band": "engage"` and `"engagement_type": "brand_project"`. The session is NOT
running as a dispatched subagent. Plan mode is NOT active.

**Expected behaviour:** The skill invokes the `design-agency` skill with
`engagement_type = "brand_project"`. It does NOT call `AskUserQuestion`.
It writes one `continuity_inline` entry to `ROUTER_AUDIT_LOG` if a co-present
`<router-decision>` block is also in context.

**PASS:** `design-agency` skill is invoked; no clarifying question is emitted.  
**FAIL:** `AskUserQuestion` is called before invoking the agency (gate inserted
on a confident engage), OR inline design work is done without invoking the agency.

---

## Case 2 — band "ask" surfaces the three-option prompt, logs choice

**Input:** The injected context contains a `<design-agency-decision>` block with
`"band": "ask"`, `"confidence": 0.6`, `"engagement_type": "prototype"`,
`"decision_id": "da_test0001"`. The session is NOT a subagent. Plan mode is
NOT active.

**Expected behaviour:** The skill calls `AskUserQuestion` once with exactly
three options ("Use design agency (Recommended)", "Quick inline design (no
agency gates)", "Not design work"). After the user chooses any option, it runs
`scripts/log_override.py "da_test0001" "prototype" 0.6 "<mapped_choice>"` before
doing any work.

**PASS:** Exactly one `AskUserQuestion` is issued; `log_override.py` is called
with the correct positional args immediately after the choice is made.  
**FAIL:** No question is asked (skip straight to design work), more than one
question is asked, or `log_override.py` is never invoked.

---

## Case 3 — subagent guard suppresses all routing

**Input:** The injected context contains a `<design-agency-decision>` block with
`"band": "engage"`. The system prompt identifies the session as a dispatched
subagent (e.g. `router-sonnet` worker or Agent-tool invocation).

**Expected behaviour:** The decision block is ignored entirely. The skill
proceeds directly with the assigned task and does NOT invoke `design-agency`,
does NOT call `AskUserQuestion`, and does NOT write to any audit log.

**PASS:** No agency invocation, no question, no log write; assigned task proceeds
inline.  
**FAIL:** The agency is engaged, or `AskUserQuestion` is called — subagent
double-gating the workflow.
