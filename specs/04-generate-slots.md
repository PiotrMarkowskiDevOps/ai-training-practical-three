# Spec: generate_slots

## Overview

Scans a list of dates and trainer availability to find all valid bootcamp delivery windows. A window is a consecutive 2-day pair (Mon–Tue or Thu–Fri) where at least 2 trainers are available on **both** days. The `pattern` parameter controls which day-pair types to consider. This is the second step in the scheduling pipeline — its output is the set of candidate slots that the scheduler can assign bootcamps to.

## Inputs

| Parameter  | Type                              | Required | Description |
|------------|-----------------------------------|----------|-------------|
| `dates`    | `list[date]`                      | yes      | Sorted list of working dates (from `parse_availability`) |
| `trainers` | `dict[str, dict[date, bool]]`     | yes      | Trainer availability map (from `parse_availability`) |
| `pattern`  | `str`                             | no       | Comma-separated day-pair patterns to include. Default: `"mon-tue,thu-fri"` |

**Pattern format:**
- `"mon-tue"` — only Monday+Tuesday pairs
- `"thu-fri"` — only Thursday+Friday pairs
- `"mon-tue,thu-fri"` — both (default)
- Pattern matching is case-insensitive

## Outputs

Returns `list[tuple[date, date]]` — each element is a `(day1, day2)` pair representing a valid bootcamp slot.

**Guarantees:**
- Every slot matches the requested pattern (Mon–Tue or Thu–Fri)
- Every slot has at least 2 trainers available on both days
- `day2` is always the calendar day immediately after `day1`
- The list is ordered by `day1` ascending
- No duplicates

## Rules

1. Only consider day pairs where `day1.weekday()` is 0 (Mon) and `day2.weekday()` is 1 (Tue), OR `day1.weekday()` is 3 (Thu) and `day2.weekday()` is 4 (Fri)
2. `day1` and `day2` must both exist in `dates` (do not generate synthetic dates)
3. A slot is valid only if `len([t for t in trainers if trainers[t][day1] and trainers[t][day2]]) >= 2`
4. If `pattern="mon-tue"`, exclude all Thu–Fri pairs; if `pattern="thu-fri"`, exclude all Mon–Tue pairs
5. Return an empty list if no valid slots exist — do not raise

## Acceptance Criteria

- **AC1**: `generate_slots(dates, trainers)` on `basic.xlsx` returns exactly 7 slots
- **AC2**: `(date(2026, 3, 16), date(2026, 3, 17))` (Mon–Tue week 1) is in the result
- **AC3**: `(date(2026, 4, 2), date(2026, 4, 3))` (Thu–Fri week 3, Good Friday) is **not** in the result — only 1 trainer available both days
- **AC4**: Every slot in the result is a `(date, date)` tuple where `d1.weekday(), d2.weekday()` is `(0,1)` or `(3,4)`
- **AC5**: `generate_slots(dates, trainers, pattern="mon-tue")` returns only Mon–Tue slots
- **AC6**: `generate_slots(dates, trainers, pattern="thu-fri")` returns only Thu–Fri slots
- **AC7**: If no trainers are available on any day, returns `[]`

## Test Cases

```python
from datetime import date
from scheduler import parse_availability, generate_slots

def test_seven_total_slots():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    assert len(slots) == 7

def test_week1_mon_tue_is_valid():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    assert (date(2026, 3, 16), date(2026, 3, 17)) in slots

def test_good_friday_slot_invalid():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    assert (date(2026, 4, 2), date(2026, 4, 3)) not in slots

def test_pattern_mon_tue_only():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers, pattern="mon-tue")
    for d1, d2 in slots:
        assert d1.weekday() == 0 and d2.weekday() == 1

def test_each_slot_has_two_trainers():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    for d1, d2 in slots:
        available = [n for n, av in trainers.items() if av[d1] and av[d2]]
        assert len(available) >= 2
```

## Edge Cases

| Case | Input | Expected behaviour |
|------|-------|--------------------|
| No trainers available | All availability `False` | Returns `[]` |
| Only 1 trainer available on a pair | e.g. Good Friday week | Slot excluded |
| Pattern filters all slots | `pattern="thu-fri"` but no Thu–Fri pairs in dates | Returns `[]` |
| Dates not consecutive | day1 and day2 not adjacent in calendar | Slot excluded (both must be in `dates`) |
| Empty dates list | `dates=[]` | Returns `[]` |

## Engineering Notes

- Iterate over `dates` looking for adjacent pairs matching the pattern — do not generate all possible pairs
- Check adjacency by index: `dates[i]` and `dates[i+1]` — only pair them if weekdays match the pattern
- Do not assume dates are consecutive calendar days (weekends are absent); check weekday values directly
- No external libraries needed — pure Python with `datetime`
