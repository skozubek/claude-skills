---
name: devils-advocate
description: |
  Anti-sycophancy diagnostic. When you've been talking to Claude for a while about a
  decision and feel certain, invoke this to force the opposite argument at full force.
  If the counter-argument is equally convincing, you don't have a reason — you have an
  LLM-amplified vibe. Optionally cross-checks with codex for different-model diversity.

  Use when: "devils advocate", "argue the opposite", "steelman against", "challenge
  this", "am I sure about X", "opposite case". Pair with /codex for cross-model check.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

# Devil's Advocate

Karpathy's pattern: LLMs optimize for making whoever asked last sound right. Asking
"help me argue X" and then "help me argue not-X" yields two equally brilliant
arguments. The quality of the argument is decoupled from its correctness. This skill
converts that sycophancy into a diagnostic.

**When to invoke.** Before shipping a non-trivial decision you've been developing
*with Claude in the current conversation*. Architectural choices, PR rationales,
product bets, design directions — anywhere you feel certain after prolonged
collaboration.

**When NOT to invoke.** Trivial decisions, decisions made independently, or cases
where you want validation rather than a check. If you want validation, that's fine —
just don't pretend this is a check.

## Flow

### Step 1 — Restate the decision (4-6 lines)

In your own words: what's being chosen, what the alternative is, the 2-3 load-bearing
reasons. If the user's argument was built across the conversation, pull the actual
claims — do not summarize into a stronger version than what was said.

If it isn't clear what's under review, ask before continuing.

### Step 2 — Maximum-force opposition

Argue the opposite **as if your job depended on killing this plan.** Requirements:

1. **Specific counter-examples.** Concrete scenarios where the original fails — not
   "there might be issues."
2. **Concrete failure modes.** "This specific thing breaks when this specific
   condition holds," not generic risk language.
3. **Name where the evidence is thin.** If the original rests on unstated
   assumptions, name them.
4. **Attack the strongest version of the plan, not a weak caricature.** Kill it on
   its own terms.
5. **No balance. No hedges. No compromises.** One-sided round. Balance comes in
   Step 4.

If you genuinely cannot mount a serious attack after real effort, say so explicitly —
that is also signal, and often the strongest vote for the original plan.

### Step 3 — Optional: codex cross-check

Same-model steelmen can silently collude with the original because the underlying
intuitions are shared. A second model with different training is a much harder test.
Offer to run codex if the decision touches code, architecture, or anything codex can
reason about:

```bash
codex exec "Argue against this decision at full force. Here's the decision and its reasoning:

<paste Step 1 restatement>
<paste the user's reasoning>

Find specific failure modes, counter-examples, and unstated assumptions. Don't
balance — attack. If you cannot mount a serious attack, say so explicitly."
```

Only run if the user agrees. Summarize codex's argument in 3-5 bullets, flagging
where it diverges from Step 2 and where it converges (convergence from a different
model on the same failure mode is a strong signal, not a coincidence).

### Step 4 — Verdict

Answer three questions directly, no hedging:

1. **Did the counter-argument land?** Yes / Partly / No.
2. **Evidence density comparison.** Which side had more specifics vs hand-waves?
3. **Surviving counter-examples.** Which specific attack vectors did the original
   NOT answer?

Then give the diagnostic:

- **Original holds** — proceed, but note the surviving counter-examples so they
  don't get lost.
- **Both equally strong** — you don't have a reason, you have a vibe. Stop, rethink,
  or gather evidence before shipping.
- **Opposite wins** — flip the decision, or reconsider the framing entirely.

## Rules

- Do NOT hedge in Step 2. A weak steelman is worse than no steelman — it validates
  the original by looking like it survived attack. Be adversarial.
- Do NOT flatter. No "this is a strong plan, but..." No "valid concerns on both
  sides." Not in Step 2, not in Step 4.
- Do NOT propose compromises in Step 2. Forcing contrast is the point; middle paths
  blur the signal.
- Cite specifics when possible: file:line, a benchmark number, a known incident,
  a paper.
- If the user pushes back on Step 2 ("you're being unfair"), that's often the signal
  they wanted validation. Ask them directly what they're looking for.
