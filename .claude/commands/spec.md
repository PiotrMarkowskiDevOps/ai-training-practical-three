---
description: Write a technical specification for the next function to implement
---

You are a senior engineer helping write a rigorous technical specification. Your job is to interview the developer, surface things they haven't thought about, and produce a spec detailed enough that another developer could implement it correctly without asking follow-up questions.

## Step 1 — Understand what's being built

The developer will describe a function or feature (either via `$ARGUMENTS` or by you asking). Before writing anything, ask targeted questions to fill in gaps. Work through these areas:

**Inputs**
- What are the parameters? What types?
- Are any optional? What are the defaults?
- What file formats are involved? What does the structure look like?
- What are the valid ranges or constraints on inputs?

**Outputs**
- What does it return? Exact type and shape?
- What guarantees does the caller get (sorted? unique? complete?)?
- What does it return on empty input?

**Rules and constraints**
- Are there business rules that must always hold? (e.g. "every bootcamp must have exactly 2 trainers")
- What ordering or priority rules apply?

**Edge cases** — ask specifically about:
- Empty or missing input files
- Blank cells or missing values in spreadsheets
- Trainer names that appear in one sheet but not another
- Inputs that make the problem unsolvable (no valid slots, no trainers available)

Keep questions concise. Ask the most important ones first. If `$ARGUMENTS` already answers most questions, skip straight to writing the spec.

## Step 2 — Write the spec

Once you have enough information, write the specification in two places:

1. **Named file** — `specs/NN-function-name.md` where `NN` is the challenge number (e.g. `specs/04-generate-slots.md`). Derive the number from the challenge being worked on, or ask if unclear.
2. **Current file** — also write the same content to `specs/current.md` (overwrite it). This is what `/build` reads.

Use this exact structure for both files:

```markdown
# Spec: <function name>

## Overview
One paragraph: what this function does and why it exists.

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| ...       | ...  | yes/no   | ...         |

Include file format details where relevant (column names, expected structure, encoding).

## Outputs

Describe the return value with exact type. Include what structure it has and what guarantees hold (sorted? complete? no duplicates?).

## Rules

Numbered, testable constraints:
1. Rule one
2. Rule two
...

## Acceptance Criteria

Specific pass/fail statements:
- **AC1**: Given [input], must return [output]
- **AC2**: ...
(minimum 3, ideally 5+, using real data from `data/basic.xlsx` where possible)

## Test Cases

At least 3 concrete pytest-style examples:
```python
def test_something():
    result = the_function(...)
    assert result == ...
```

## Edge Cases

| Case | Input | Expected behaviour |
|------|-------|--------------------|
| ...  | ...   | ...                |

## Engineering Notes

- Library choices (e.g. use `openpyxl` not `xlrd`)
- Performance considerations
- Error handling: what to raise, when, with what message
- Anything non-obvious about the implementation
```

## Step 3 — Confirm with the developer

After writing both files, briefly summarise what you wrote (3–5 bullets) and ask: "Does this capture everything, or is there anything to adjust?"

Do not proceed to implement anything. The spec is the deliverable.
