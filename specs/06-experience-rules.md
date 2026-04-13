# Spec: schedule_greedy (experience rules extension)

## Overview

Extends `schedule_greedy` to enforce trainer experience levels when a `config` dict is provided. Every scheduled bootcamp must include at least one experienced trainer. Trainees may only be assigned alongside an experienced trainer. Slots where this constraint cannot be satisfied are skipped. When no config is provided, behaviour is identical to the previous implementation.

## Inputs

| Parameter  | Type                           | Required | Description |
|------------|--------------------------------|----------|-------------|
| `dates`    | `list[date]`                   | yes      | Sorted working dates from `parse_availability` |
| `trainers` | `dict[str, dict[date, bool]]`  | yes      | Trainer availability map |
| `slots`    | `list[tuple[date, date]]`      | yes      | Valid candidate slots from `generate_slots` |
| `config`   | `dict \| None`                 | no       | Experience configuration. Default: `None` |

**Config structure:**
```python
config = {
    "experienced": {"Alice Chen", "Bob Smith", "Diana Müller"},  # set of experienced trainer names
    "trainees": {"Carol Jones"},                                   # set of trainee names
    # Trainers in neither set (e.g. Eve Brown) are uncategorised — can pair with anyone
}
```
Both keys are optional within config. Unknown trainer names in the sets are ignored.

## Outputs

Returns `list[dict]` — same structure as before:
```python
[{"slot": (date(...), date(...)), "trainers": ["Name A", "Name B"]}, ...]
```

**Guarantees:**
- Every entry has exactly 2 trainers
- Both trainers available on both days
- No trainer double-booked across entries
- When config is provided: every entry contains at least one experienced trainer
- Trainer names within each entry are sorted alphabetically

## Rules

1. If `config` is `None` or `config` has no `"experienced"` key: behave exactly as before (no experience filtering)
2. For each slot, find candidates who are available on both days and not yet booked
3. If config has `"experienced"`: filter to only schedule slots where at least 1 candidate is experienced
4. Selection strategy: pick 1 experienced trainer first, then pick the best available second (any category — experienced, uncategorised, or trainee — since rule 2 is already satisfied)
5. If fewer than 2 candidates remain after applying experience filter, skip the slot
6. Booking tracking is unchanged: both days are marked as booked for assigned trainers

## Acceptance Criteria

- **AC1**: With `config=CONFIG` on `basic.xlsx`, every bootcamp entry contains at least one name from `CONFIG["experienced"]`
- **AC2**: With `config=CONFIG`, any trainee in an entry is always paired with an experienced trainer
- **AC3**: With `config=None`, `schedule_greedy` schedules ≥4 bootcamps (no regression)
- **AC4**: The Mon 6 Apr – Tue 7 Apr slot is skipped with `config=CONFIG` — only Carol (trainee) and Eve (uncategorised) are available, neither is experienced
- **AC5**: With `config=CONFIG`, no trainer is double-booked on the same day across entries
- **AC6**: `schedule_greedy(dates, trainers, [], config=CONFIG)` returns `[]`

## Test Cases

```python
from scheduler import parse_availability, generate_slots, schedule_greedy

CONFIG = {
    "experienced": {"Alice Chen", "Bob Smith", "Diana Müller"},
    "trainees": {"Carol Jones"},
}

def test_every_bootcamp_has_experienced_trainer():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    schedule = schedule_greedy(dates, trainers, slots, config=CONFIG)
    for entry in schedule:
        names = set(entry["trainers"])
        assert names & CONFIG["experienced"], f"No experienced trainer in {entry['slot']}"

def test_trainee_always_paired_with_experienced():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    schedule = schedule_greedy(dates, trainers, slots, config=CONFIG)
    for entry in schedule:
        names = set(entry["trainers"])
        if names & CONFIG["trainees"]:
            assert names & CONFIG["experienced"]

def test_no_config_still_works():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    schedule = schedule_greedy(dates, trainers, slots)
    assert len(schedule) >= 4
```

## Edge Cases

| Case | Input | Expected behaviour |
|------|-------|--------------------|
| No config | `config=None` | No experience filtering, behaviour unchanged |
| Config with empty experienced set | `{"experienced": set()}` | Treated as no filter (no experienced set → no constraint) |
| Only trainees/uncategorised available | Carol + Eve only | Slot skipped |
| Only 1 experienced available | 1 experienced + 0 others unbooked | Slot skipped (need 2 trainers total) |
| Experienced trainer already booked | All experienced booked on those days | Slot skipped |

## Engineering Notes

- Modify `schedule_greedy` in place — do not create a new function
- Extract `experienced = config.get("experienced", set()) if config else set()` before the loop
- Selection: `exp_candidates = [c for c in candidates if c in experienced]` → if empty, `continue`; otherwise `first = exp_candidates[0]`, `remaining = [c for c in candidates if c != first]`, `assigned = sorted([first, remaining[0]])`
- Sorting the assigned pair alphabetically maintains deterministic output
- The `trainees` key in config does not need explicit handling — the rule "must include 1 experienced" already ensures trainees are always paired with one
