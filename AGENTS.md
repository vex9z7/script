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
- When explaining how something works, prefer pseudo code over lengthy prose. Keep it brief and focused on the core idea.

## Verification

- After making code changes, run the relevant formatter, linter, and tests for the affected area.
- At minimum, run unit tests when the codebase has them and they are relevant to the change.
- If relevant tests do not exist, explicitly call out the coverage gap and suggest adding unit tests.
- If verification cannot be completed, state what was not run and why.
- When fixing a bug or finding a flaw, add test cases that reproduce it to prevent regression.
- Use mocks to isolate tests from external dependencies (filesystem, time, etc.).
- Prefer pytest fixtures over ad-hoc setup.
- Do not make tests overly trivial - preserve meaningful behavioral assertions.
- Do not drop tests unless they are stale or redundant.
- Do not import modules that are out of the testing scope (e.g., `os`, `time`). Mock them or design tests that don't need them.

## Version Control

- ALWAYS show the user the changes (via `git diff` or summary) before committing.
- MUST NOT commit or push without explicit user approval.
- If the user asks to commit, present the diff and ask for confirmation before executing `git commit`.

## Testing

### Test-Driven Development (TDD)

Follow the **Red-Green-Refactor** cycle:
1. **Red** - Write a failing test
2. **Green** - Write minimum code to pass
3. **Refactor** - Clean up code

**Key principles:**
- **Test behavior, not implementation** - Tests survive refactoring when they verify "what" not "how"
- **Keep tests simple** - One behavior per test, minimal setup
- **Mock external dependencies** - Use `patch()` for filesystem, network, time
- **Don't skip refactoring** - The green phase is not the end
- **Focus coverage strategically** - 100% coverage is wasteful; prioritize critical logic
- **Keep tests fast** - Unit tests should run in seconds

### Unit Testing

Test **individual functions/methods in isolation** with mocks for external dependencies.

**Best practices:**
- Use **Arrange-Act-Assert** pattern
- Test behavior, not implementation
- One logical concept per test
- Use descriptive names: `should_X_when_Y`
- Test edge cases, not just happy path
- Minimize mocking - only mock external boundaries
- Use fixtures for test data
- Tests must be independent

```python
def test_should_return_true_when_path_is_mountpoint():
    # Arrange
    path = Path("/tmp/test")
    # Act
    result = is_mountpoint(path)
    # Assert
    assert result is True
```

### Integration Testing

Test **multiple components working together**. May use real dependencies.

**Best practices:**
- Isolate tests - each test independent, clean up after
- Use appropriate test doubles (mocks, stubs, fakes)
- Manage test data with fixtures/builders
- Test realistic scenarios including error paths
- Keep tests fast - use in-memory alternatives when possible

**Note:** Integration tests are slower and may be flaky. Keep them minimal and focus on critical paths.

### When to Use Each

| Scenario | Use |
|----------|-----|
| Algorithm/logic in isolation | Unit test |
| File operations | Unit test with mocks |
| Component interactions | Integration test |
| End-to-end workflows | Integration test |
