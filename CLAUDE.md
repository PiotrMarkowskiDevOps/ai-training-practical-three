# Bootcamp Scheduler

You are helping a developer build a real constraint optimisation system step by step.

## The Project

A scheduling tool that reads trainer availability from Excel spreadsheets and produces an optimal bootcamp schedule. Each bootcamp is a 2-day delivery requiring exactly 2 trainers.

Data files are in `data/`. Tests are in `tests/`. Implementation goes in `scheduler.py`.

## How Slash Commands Work

Custom commands live in `.claude/commands/` as markdown files. A file at `.claude/commands/spec.md` becomes the `/spec` command.

The file contains instructions Claude follows when the command is invoked. It can be plain markdown or include YAML frontmatter:

```
---
description: One-line description of what this command does
---

Instructions for Claude here...
```

The `description` field controls when Claude auto-suggests the command.

Commands can read files, write files, run shell commands, and reason about the codebase. `$ARGUMENTS` contains anything typed after the command name.

## Running Tests

```bash
python3 -m pytest tests/ -v                          # all tests
python3 -m pytest tests/test_01_availability.py -v   # one challenge
```

## Where to Start

Run `/next`.

## Git Workflow

After each challenge is complete and tests pass, commit the work:

- Use **Conventional Commits** format: `type(scope): description`
- Scope should reflect the challenge, e.g. `feat(scheduler): add parse_availability`
- One-liner only — no body, no bullet points
- **Never** add `Co-Authored-By`, AI attribution, or any mention of Claude in commit messages or PRs
