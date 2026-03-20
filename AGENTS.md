# AGENTS.md

## Purpose

This file defines the collaboration boundary between the human and the agent.

It is intentionally project-independent. Project rules, architecture, and implementation guidance belong in the project documentation, not here.

## Collaboration Protocol

- Before substantial edits, state which layers and files are affected.
- Keep diffs scoped to the active task.
- Do not perform speculative refactors outside the requested scope.
- Treat the project's active documentation as the source of truth for project-specific guidance.
- Use project documentation as working context and read the relevant documents on demand for the task at hand.
- Do not treat external, historical, or reference-only material as active instruction unless the project documentation says so.

## Conflict Handling

- If documented guidance conflicts with implementation, describe the conflict clearly.
- Point to the exact doc and code locations involved.
- Suggest plausible resolution paths when a conflict is found.
- Stop and ask before changing behavior that depends on ambiguous intent.
- Do not silently reconcile business-logic conflicts.

## Human-Agent Boundary

- The human sets goals, constraints, and acceptance criteria.
- The agent executes within that scope, surfaces tradeoffs, and reports meaningful risks.
- The agent should prefer making progress over blocking on minor uncertainty, but must stop when a decision would change intended behavior or policy.
- The agent should preserve user work and avoid reverting changes it did not make unless explicitly instructed.

## Communication

- Be explicit about assumptions when they matter.
- Surface blockers, conflicts, and irreversible actions before taking them.
- Summaries should focus on what changed, what remains risky, and what was not verified.
- When a change updates meta-rules, shared conventions, or documentation structure, check the affected docs for follow-on updates and call out any remaining gaps explicitly.

## Verification

- After making code changes, run the relevant formatter, linter, and tests for the affected area.
- At minimum, run unit tests when the codebase has them and they are relevant to the change.
- If relevant tests do not exist, explicitly call out the coverage gap and suggest adding unit tests.
- If verification cannot be completed, state what was not run and why.
