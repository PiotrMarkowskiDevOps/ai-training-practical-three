# Spec: parse_locations + schedule_optimal (location assignment)

## Overview

Two changes in this challenge:

1. **`parse_locations(filepath)`** reads the `Locations` sheet from `advanced.xlsx` and returns a list of location dicts describing where bootcamps can be delivered.

2. **`schedule_optimal`** is extended to accept `locations=None`. When provided, each scheduled bootcamp is assigned to a location (added as a `"location"` key in the output dict). Locations that require French-speaking trainers enforce that constraint. Total bootcamps per location are capped by demand.

## Inputs

### parse_locations

| Parameter  | Type  | Required | Description |
|------------|-------|----------|-------------|
| `filepath` | `str` | yes      | Path to `.xlsx` file containing a `Locations` sheet |

**Locations sheet format** (`advanced.xlsx`):
```
Name        | Country     | Demand | French Required | Max Parallel | Max/Week
London      | UK          | 3      | No              | 1            |
Paris       | France      | 2      | Yes             | 1            |
Amsterdam   | Netherlands | 1      | No              | 1            |
Stockholm   | Sweden      | 1      | No              | 1            |
```
- Row 1: header
- Rows 2+: one location per row
- `French Required`: `"Yes"` or `"No"`
- `Demand`: integer — max bootcamps at this location

### schedule_optimal (new parameter)

| Parameter   | Type               | Required | Description |
|-------------|--------------------|----------|-------------|
| `locations` | `list[dict] \| None` | no     | Location list from `parse_locations`. Default: `None` |

(All other parameters unchanged.)

## Outputs

### parse_locations

Returns `list[dict]`, one entry per location row:

```python
[
    {"name": "London",    "country": "UK",          "demand": 3, "french_required": False},
    {"name": "Paris",     "country": "France",       "demand": 2, "french_required": True},
    {"name": "Amsterdam", "country": "Netherlands",  "demand": 1, "french_required": False},
    {"name": "Stockholm", "country": "Sweden",       "demand": 1, "french_required": False},
]
```

**Guarantees:**
- Every dict has `name`, `country`, `demand`, `french_required` keys
- `french_required` is `bool` (`True` only when cell value is exactly `"Yes"`)
- `demand` is `int`
- Order matches spreadsheet row order

### schedule_optimal (with locations)

Same `list[dict]` format, with an added `"location"` key:
```python
{"slot": (...), "trainers": [...], "location": "London"}
```

**Guarantees:**
- Every active entry has a `"location"` key when `locations` is provided
- If a location's `french_required` is `True`, at least one trainer in the entry has `french_speaking=True` in `trainer_info`
- Total bootcamps assigned to each location ≤ location's `demand`

## Rules

### parse_locations
1. Read the sheet named `"Locations"` (not the active sheet)
2. Skip the header row (row 1)
3. Skip rows where `Name` column is `None`
4. `french_required = True` only when the cell value is exactly `"Yes"` (case-sensitive)
5. `demand` is cast to `int`

### schedule_optimal with locations
6. Introduce `y[s_idx, l_idx]` boolean variables: slot `s` assigned to location `l`
7. Each active slot is assigned to exactly 1 location: `sum(y[s, l] for all l) == active[s]`
8. French constraint: for each French-required location `l`, for each slot `s`:
   `y[s, l] <= sum(x[t, s] for t in french_speakers)`
9. Demand cap: `sum(y[s, l] for all s) <= demand[l]` for each location `l`
10. Objective remains maximise total active slots

## Acceptance Criteria

- **AC1**: `parse_locations("data/advanced.xlsx")` returns a non-empty list of dicts
- **AC2**: Every dict has `name`, `country`, `demand`, `french_required` keys
- **AC3**: `next(l for l in locations if l["name"] == "Paris")["french_required"] is True`
- **AC4**: `next(l for l in locations if l["name"] == "London")["french_required"] is False`
- **AC5**: With `locations` provided, each entry in the schedule has a `"location"` key
- **AC6**: All bootcamps assigned to a `french_required` location include at least 1 French-speaking trainer
- **AC7**: No location has more bootcamps assigned than its `demand`

## Test Cases

```python
from scheduler import parse_availability, generate_slots, schedule_optimal, parse_locations

ADVANCED = "data/advanced.xlsx"
CONFIG = {
    "experienced": {"Alice Chen", "Bob Smith", "Diana Müller"},
    "trainees": {"Carol Jones"},
}

def test_parse_locations_returns_list():
    locations = parse_locations(ADVANCED)
    assert isinstance(locations, list) and len(locations) > 0

def test_paris_requires_french():
    locations = parse_locations(ADVANCED)
    paris = next(l for l in locations if l["name"] == "Paris")
    assert paris["french_required"] is True

def test_london_no_french():
    locations = parse_locations(ADVANCED)
    london = next(l for l in locations if l["name"] == "London")
    assert london["french_required"] is False

def test_french_location_has_french_speaker():
    dates, trainers, trainer_info, weekly_caps = parse_availability(ADVANCED)
    slots = generate_slots(dates, trainers)
    locations = parse_locations(ADVANCED)
    schedule = schedule_optimal(dates, trainers, slots, config=CONFIG,
                                trainer_info=trainer_info, weekly_caps=weekly_caps,
                                locations=locations)
    for entry in schedule:
        loc = entry.get("location")
        if loc:
            loc_data = next((l for l in locations if l["name"] == loc), None)
            if loc_data and loc_data["french_required"]:
                french = {n for n in entry["trainers"]
                          if trainer_info.get(n, {}).get("french_speaking", False)}
                assert french
```

## Edge Cases

| Case | Input | Expected behaviour |
|------|-------|--------------------|
| No French speakers available | All trainers `french_speaking=False` | Paris bootcamps simply not scheduled (solver skips) |
| Demand = 0 | Location with `demand=0` | 0 bootcamps assigned there |
| `locations=None` | Not passed to `schedule_optimal` | No location assignment, `"location"` key absent from entries |
| Location sheet missing | File without Locations sheet | `KeyError` from openpyxl (acceptable — advanced.xlsx always has it) |

## Engineering Notes

- Read sheet by name: `wb["Locations"]` not `wb.active`
- `french_speakers` set: derive from `trainer_info` — `{name for name, info in trainer_info.items() if info.get("french_speaking")}` — only relevant when `locations` is provided
- The `y[s_idx, l_idx]` variables are only needed when `locations` is not `None`; guard with `if locations:`
- CP-SAT constraint for French: must hold per `(slot, location)` pair — even if solver assigns 0 bootcamps to Paris, no violation
- Do not change the objective — demand acts as an upper bound, not a target
- `trainer_info` must be passed alongside `locations` for French constraint to work; if `trainer_info` is `None`, treat `french_speakers` as empty set (no French speakers known)
