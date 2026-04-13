# Spec: schedule_greedy

## Overview

Assigns trainer pairs to bootcamp slots using a greedy first-fit algorithm. Iterates slots in order, and for each slot picks the first 2 trainers who are available on both days and haven't already been booked on either day. Slots where fewer than 2 unbooked trainers are available are skipped. The `config` parameter is reserved for future experience rules (Challenge 6) and is ignored for now.

## Inputs

| Parameter  | Type                               | Required | Description |
|------------|------------------------------------|----------|-------------|
| `dates`    | `list[date]`                       | yes      | Sorted list of working dates (from `parse_availability`) |
| `trainers` | `dict[str, dict[date, bool]]`      | yes      | Trainer availability map (from `parse_availability`) |
| `slots`    | `list[tuple[date, date]]`          | yes      | Valid candidate slots (from `generate_slots`) |
| `config`   | `dict \| None`                     | no       | Reserved for experience rules — ignore for now. Default: `None` |

## Outputs

Returns `list[dict]` — one entry per successfully scheduled bootcamp:

```python
[
    {"slot": (date(2026, 3, 16), date(2026, 3, 17)), "trainers": ["Alice Chen", "Bob Smith"]},
    ...
]
```

**Guarantees:**
- Every entry has exactly 2 trainers
- Both trainers are available on both days of the slot
- No trainer appears on the same day in more than one entry
- Entries are in the same order as the input `slots` (slots that are skipped are omitted)

## Rules

1. Process slots in the order they appear in `slots`
2. For each slot, find all trainers available on both `day1` and `day2` who are not already booked on either day
3. If ≥2 such trainers exist, assign the first 2 (sorted alphabetically by name for determinism)
4. If <2 such trainers exist, skip the slot — do not add it to the result
5. After assigning a trainer to a slot, mark both `day1` and `day2` as booked for that trainer
6. `config` is accepted but ignored

## Acceptance Criteria

- **AC1**: Returns a `list` of `dict` entries each with `"slot"` and `"trainers"` keys
- **AC2**: Every entry has exactly 2 trainers
- **AC3**: Both trainers in each entry are available (`True`) on both days of the slot
- **AC4**: No trainer is booked on the same day twice across all entries
- **AC5**: At least 4 bootcamps are scheduled from `basic.xlsx`
- **AC6**: `schedule_greedy(dates, trainers, [], config=None)` returns `[]`

## Test Cases

```python
from datetime import date
from scheduler import parse_availability, generate_slots, schedule_greedy

def test_returns_list_of_dicts():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    schedule = schedule_greedy(dates, trainers, slots)
    assert isinstance(schedule, list)
    for entry in schedule:
        assert "slot" in entry and "trainers" in entry

def test_each_bootcamp_has_two_trainers():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    schedule = schedule_greedy(dates, trainers, slots)
    for entry in schedule:
        assert len(entry["trainers"]) == 2

def test_no_trainer_double_booked():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    schedule = schedule_greedy(dates, trainers, slots)
    day_bookings = {}
    for entry in schedule:
        d1, d2 = entry["slot"]
        for name in entry["trainers"]:
            assert name not in day_bookings.get(d1, set())
            assert name not in day_bookings.get(d2, set())
            day_bookings.setdefault(d1, set()).add(name)
            day_bookings.setdefault(d2, set()).add(name)

def test_at_least_four_bootcamps():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    schedule = schedule_greedy(dates, trainers, slots)
    assert len(schedule) >= 4
```

## Edge Cases

| Case | Input | Expected behaviour |
|------|-------|--------------------|
| Empty slots | `slots=[]` | Returns `[]` |
| Only 1 trainer available | All slots have just 1 trainer free | Returns `[]` |
| All slots valid | Every slot has ≥2 free trainers | All slots scheduled |
| Trainer blocked by earlier booking | Trainer used in slot 1, slot 2 same day | Slot 2 picks different trainers |

## Engineering Notes

- Track booked days as `set[tuple[str, date]]` of `(trainer_name, date)` pairs
- Alphabetical sort of candidate trainers ensures deterministic output regardless of dict iteration order
- `config` parameter must be accepted in the signature for forward-compatibility with Challenge 6 — just don't use it yet
