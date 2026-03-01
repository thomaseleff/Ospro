# Test Agent Guidance

## Testing Philosophy

1. Prioritize integration tests that exercise public interfaces as a user/consumer would.
2. Add unit tests only for domain-specific or high-complexity logic.
3. Do not test Rust language behavior or dependency internals.

## Practical Rules

- Use `tests/` integration tests for externally visible behavior.
- Keep fixtures minimal and representative of real runtime inputs.
- Prefer deterministic tests; avoid non-deterministic timing and external IO when possible.
- Assert contract outcomes and error semantics owned by Ospro.
