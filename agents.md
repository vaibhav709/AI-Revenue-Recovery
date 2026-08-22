# AGENTS.md

## Security

- NEVER read, print, expose, modify, or commit `.env` files.
- NEVER access or expose API keys, passwords, tokens, database credentials,
  private keys, or other secrets.
- You may inspect code that references environment variables, but never
  inspect their actual values.
- Never place secrets in source code, logs, tests, documentation, or commits.
- Never weaken `.gitignore` protections for secrets.

## Architecture

Maintain this separation:

ML Model
→ failure probability / predicted failure / risk level

Deterministic Python Rules
→ priority / strategy / communication channel / follow-up / escalation

CrewAI Agents
→ explanation / analysis / customer communication

Python + Pydantic Validation
→ final validation

The LLM must NOT override ML predictions or deterministic business rules.

## Financial Safety

Never invent:

- balances
- due dates
- fees
- penalties
- discounts
- payment arrangements
- financial amounts
- unsupported payment relationships

Do not calculate outstanding balance unless explicitly provided.

If information is unavailable, say:
"This information must be confirmed."

## Coding Rules

- Inspect the existing architecture before changing it.
- Reuse existing code where appropriate.
- Avoid unnecessary rewrites.
- Do not modify unrelated files.
- Do not add unnecessary dependencies.
- Do not implement future phases unless explicitly asked.

## Testing

After changes:

1. Run relevant tests.
2. Fix failures caused by the changes.
3. Re-run tests.
4. Never claim tests passed if they were not run.
5. Report failures honestly.

## Phase Discipline

For each requested phase:

1. Analyze current implementation.
2. Identify what's complete.
3. Identify what's missing.
4. Implement only the requested phase.
5. Test it.
6. Report changed files, tests, remaining issues, and phase status.

Do not automatically move to another phase.

## First Repository Analysis

When asked to analyze the repository for the first time:

- Do not modify files.
- Analyze the architecture.
- Identify completed and missing functionality.
- Identify affected files.
- Provide an implementation plan.
- Wait for explicit implementation instructions.