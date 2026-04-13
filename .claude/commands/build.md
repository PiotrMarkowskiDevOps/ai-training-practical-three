---
description: Implement the current spec from specs/current.md into scheduler.py
---

You are a senior engineer implementing a technical specification. Work methodically through these phases. Do not skip ahead — complete each phase before moving to the next.

## Phase 1 — Pre-flight checks

Before writing a single line of code:

1. Read `specs/current.md` in full. If it does not exist or is clearly incomplete (missing inputs, outputs, or rules), stop and tell the developer: "The spec is missing [X]. Run `/spec` first."
2. Read `scheduler.py` in full. Note every function that already exists — you must not break any of them.
3. Identify which test file(s) will verify the new work (e.g. `tests/test_01_availability.py`). Read that file so you know exactly what the tests expect.

## Phase 2 — Plan

Write your implementation plan as a short message before touching any file. Include:

- The function signature(s) you will create
- A one-sentence description of what each does
- Any helper functions needed
- Which existing functions (if any) you are changing and why

Wait — do not write code yet. Output the plan, then proceed.

## Phase 3 — Implement

Now write the code into `scheduler.py`:

- Add new functions below the existing ones — never modify or delete existing functions unless the spec explicitly requires it
- Use type hints on all function signatures
- Keep functions small and pure where possible (no hidden side effects)
- Handle errors at boundaries (file not found, malformed input) with clear messages
- Follow the rules and acceptance criteria from the spec exactly
- Use libraries already in `requirements.txt` (openpyxl, ortools, holidays) — do not add new dependencies

## Phase 4 — Verify

Run the tests:

```bash
python3 -m pytest tests/ -v
```

- If tests pass: proceed to Phase 5
- If tests fail: read the failure message carefully, fix the code, and re-run — do not report done until all previously-passing tests still pass AND the new tests pass
- If you cannot fix a failure after two attempts, stop and explain the failure to the developer — do not keep guessing

## Phase 5 — Report

Output a concise summary:

- What functions were added (names and one-line descriptions)
- Test results: how many pass, how many fail
- Any tradeoffs, assumptions, or limitations worth noting
- If anything in the spec was ambiguous, say so and explain what you assumed

Do not add implementation TODOs or future improvement notes unless specifically asked.
