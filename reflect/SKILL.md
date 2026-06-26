---
name: reflect
description: Reflect on a mistake that keeps repeating. Abstract the learning and persist it.
disable-model-invocation: true
argument-hint: "[description of the mistake or context]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
---

# Reflect on a Recurring Mistake

The user flagged a repeated mistake. Your job: abstract the lesson and persist it so it never happens again.

## Input

`$ARGUMENTS` — the user's description of the mistake, or empty (infer from recent conversation).

## Steps

1. **Identify the pattern.** What did you do wrong? What was the root cause — not the surface symptom?

2. **Abstract and generalize.** Don't write "don't do X in file Y." Write a principle that covers this class of mistake. Ask: "What other situations would this apply to?"

3. **Check for existing rules.** Read the project `CLAUDE.md` and memory files — is this already covered? If so, the rule isn't working. Strengthen it or reword it instead of duplicating.

4. **Decide where to persist:**
   - **CLAUDE.md** (project root) — if it's a project-specific coding convention, architectural rule, or workflow constraint. These are authoritative and always loaded.
   - **Memory file** (`~/.claude/projects/.../memory/`) — if it's a personal working style correction, user preference, or cross-project lesson.

5. **Read the META section.** If writing to CLAUDE.md, read `## META — How to Maintain This File` first. Follow its formatting rules and anti-bloat constraints.

6. **Write the rule.** Format per META:
   - Start with NEVER or ALWAYS
   - Lead with why, then solution (max 1-3 bullets)
   - Be concrete — include real code/commands
   - One code block max per rule

7. **Update the Rules Summary.** If writing to CLAUDE.md, add a one-line entry to the corresponding summary section at the top and update the rule count.

8. **Report back.** Tell the user:
   - What pattern you identified
   - Where you persisted it
   - The exact rule you wrote
