# Spec: parse_availability (extended) + schedule_optimal (caps)

## Overview

Two changes in this challenge:

1. **`parse_availability`** is extended to detect the richer spreadsheet format (`intermediate.xlsx` and `advanced.xlsx`) and return a 4-tuple `(dates, trainers, trainer_info, weekly_caps)` when extra metadata columns are present. For `basic.xlsx` (no extra columns) it still returns a 2-tuple to preserve backwards compatibility.

2. **`schedule_optimal`** is extended to enforce two new constraints when the extra data is provided: a per-trainer weekly day cap (e.g. Bob can work at most 2 days/week = 1 bootcamp/week), and a per-week total bootcamp cap read from the spreadsheet cap row.

## Inputs

### parse_availability

| Parameter  | Type  | Required | Description |
|------------|-------|----------|-------------|
| `filepath` | `str` | yes      | Path to `.xlsx` file — `basic.xlsx` (basic format) or `intermediate.xlsx`/`advanced.xlsx` (extended format) |

**Basic format** (`basic.xlsx`):
- Row 1: `Name`, then date strings
- Rows 2+: trainer name, then `"Yes"` or empty

**Extended format** (`intermediate.xlsx`, `advanced.xlsx`):
- Row 1: `Name`, `Home Location`, `French`, `Max/Week`, then date strings (dates start at column index 4)
- Row 2: cap row — `Name` column is `None`; only Monday date columns have values (the per-week bootcamp cap)
- Rows 3+: trainer name, home location, French flag, max days/week, then `"Yes"` or empty

### schedule_optimal (new parameters)

| Parameter      | Type                          | Required | Description |
|----------------|-------------------------------|----------|-------------|
| `trainer_info` | `dict[str, dict] \| None`     | no       | Maps trainer name → `{home_location, french_speaking, max_per_week}`. Default: `None` |
| `weekly_caps`  | `dict[tuple, int] \| None`    | no       | Maps `(iso_year, iso_week)` → max bootcamps that week. Default: `None` |

(All other existing parameters unchanged.)

## Outputs

### parse_availability

- **Basic format:** returns `tuple[list[date], dict[str, dict[date, bool]]]` — 2-tuple as before
- **Extended format:** returns `tuple[list[date], dict[str, dict[date, bool]], dict[str, dict], dict[tuple[int,int], int]]` — 4-tuple

`trainer_info` structure:
```python
{
    "Alice Chen": {"home_location": "London", "french_speaking": False, "max_per_week": None},
    "Bob Smith":  {"home_location": "Manchester", "french_speaking": False, "max_per_week": 2},
    ...
}
```

`weekly_caps` structure:
```python
{
    (2026, 12): 2,  # ISO week 12: max 2 bootcamps
    (2026, 13): 2,
    (2026, 14): 1,
    (2026, 15): 2,
}
```
Keys are `(iso_year, iso_week)` from `date.isocalendar()`. Only weeks with a non-None cap row value are included.

### schedule_optimal

Same `list[dict]` format as before.

## Rules

### parse_availability
1. Detect extended format by checking if `header[1]` is a date string — if parsing it as `date.fromisoformat(str(header[1]))` raises `ValueError`/`TypeError`, it is the extended format
2. In extended format, dates start at column index 4 (skip `Name`, `Home Location`, `French`, `Max/Week`)
3. The cap row is the first data row where column 0 (`Name`) is `None`
4. Cap values appear only on Monday date columns; use `date.isocalendar()` to get the ISO week key
5. `french_speaking` is `True` only when the cell value is exactly `"Yes"` (case-sensitive)
6. `max_per_week` is `None` when the cell is empty; otherwise cast to `int`
7. For basic format, `trainer_info` and `weekly_caps` are not returned (2-tuple, not 4-tuple)

### schedule_optimal caps
8. Per-trainer weekly cap: if `trainer_info[name]["max_per_week"]` is set, trainer may work at most `max_per_week // 2` bootcamps in any single ISO week (since each bootcamp uses 2 days)
9. Per-week total cap: if `weekly_caps[(yr, wk)]` is set, at most that many bootcamps may be scheduled in that ISO week across all slots

## Acceptance Criteria

- **AC1**: `parse_availability(INTERMEDIATE_XLSX)` returns a tuple of length 4
- **AC2**: `trainer_info["Alice Chen"]` contains keys `home_location`, `french_speaking`, `max_per_week`
- **AC3**: `trainer_info["Bob Smith"]["max_per_week"] == 2`
- **AC4**: `weekly_caps` is non-empty; all keys are `(int, int)` tuples; all values are `int`
- **AC5**: With `trainer_info` and `weekly_caps`, Bob appears in at most 1 bootcamp per ISO week in the result
- **AC6**: No ISO week in the result exceeds its `weekly_caps` value
- **AC7**: `parse_availability(BASIC_XLSX)` still returns a 2-tuple (no regression)

## Test Cases

```python
from scheduler import parse_availability, generate_slots, schedule_optimal

INTERMEDIATE = "data/intermediate.xlsx"
CONFIG = {
    "experienced": {"Alice Chen", "Bob Smith", "Diana Müller"},
    "trainees": {"Carol Jones"},
}

def test_parse_returns_4_tuple():
    result = parse_availability(INTERMEDIATE)
    assert len(result) == 4

def test_trainer_info_fields():
    _, _, trainer_info, _ = parse_availability(INTERMEDIATE)
    assert "Alice Chen" in trainer_info
    info = trainer_info["Alice Chen"]
    assert "home_location" in info
    assert "french_speaking" in info
    assert "max_per_week" in info

def test_bob_max_per_week():
    _, _, trainer_info, _ = parse_availability(INTERMEDIATE)
    assert trainer_info["Bob Smith"]["max_per_week"] == 2

def test_weekly_caps_structure():
    _, _, _, weekly_caps = parse_availability(INTERMEDIATE)
    assert len(weekly_caps) > 0
    for (yr, wk), cap in weekly_caps.items():
        assert isinstance(yr, int) and isinstance(wk, int) and isinstance(cap, int)

def test_per_trainer_cap_respected():
    dates, trainers, trainer_info, weekly_caps = parse_availability(INTERMEDIATE)
    slots = generate_slots(dates, trainers)
    schedule = schedule_optimal(dates, trainers, slots, config=CONFIG,
                                trainer_info=trainer_info, weekly_caps=weekly_caps)
    bob_weeks = {}
    for entry in schedule:
        d1, _ = entry["slot"]
        if "Bob Smith" in entry["trainers"]:
            yr, wk, _ = d1.isocalendar()
            bob_weeks[(yr, wk)] = bob_weeks.get((yr, wk), 0) + 1
    for week, count in bob_weeks.items():
        assert count <= 1
```

## Edge Cases

| Case | Input | Expected behaviour |
|------|-------|--------------------|
| `max_per_week` is `None` | Alice has no cap | No constraint added for Alice |
| Cap row missing | Extended file with no cap row | `weekly_caps = {}` |
| Basic file | `basic.xlsx` | Returns 2-tuple; existing tests unaffected |
| Week has no cap entry | Week not in `weekly_caps` | No constraint for that week |
| `trainer_info=None` | Not passed to `schedule_optimal` | No cap constraints applied |

## Engineering Notes

- **Detection:** `try: date.fromisoformat(str(header[1])) except (ValueError, TypeError): extended = True`
- **Cap row:** skip rows where `row[0] is None` when building trainer dict; store separately as cap row
- **ISO week key:** `d.isocalendar()` returns `(year, week, weekday)` — use `(year, week)` as the dict key
- **CP-SAT trainer cap:**
  ```python
  for each trainer with max_per_week:
      for each ISO week:
          week_vars = [x[t_idx, s_idx] for s_idx where slot starts in that week]
          model.add(sum(week_vars) <= max_per_week // 2)
  ```
- **CP-SAT weekly cap:**
  ```python
  for each (yr, wk) in weekly_caps:
      week_active = [active[s_idx] for s_idx where slot starts in week (yr, wk)]
      model.add(sum(week_active) <= weekly_caps[(yr, wk)])
  ```
- Use `defaultdict(list)` to group slots by ISO week before building constraints
