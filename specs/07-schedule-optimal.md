# Spec: schedule_optimal

## Overview

A CP-SAT constraint-programming solver that finds the globally optimal bootcamp schedule — maximising the total number of bootcamps scheduled while respecting all constraints. Unlike the greedy approach, it considers all slots simultaneously and avoids locally-good choices that block better global solutions. Has the same interface as `schedule_greedy` and enforces the same experience rules via `config`. Later challenges will extend it with trainer caps, locations, and weightings — the signature must be forward-compatible.

## Inputs

| Parameter  | Type                           | Required | Description |
|------------|--------------------------------|----------|-------------|
| `dates`    | `list[date]`                   | yes      | Sorted working dates from `parse_availability` |
| `trainers` | `dict[str, dict[date, bool]]`  | yes      | Trainer availability map |
| `slots`    | `list[tuple[date, date]]`      | yes      | Valid candidate slots from `generate_slots` |
| `config`   | `dict \| None`                 | no       | Experience config with optional `"experienced"` and `"trainees"` keys. Default: `None` |

**Config structure (same as `schedule_greedy`):**
```python
config = {
    "experienced": {"Alice Chen", "Bob Smith", "Diana Müller"},
    "trainees": {"Carol Jones"},
}
```

## Outputs

Returns `list[dict]` — same format as `schedule_greedy`:
```python
[{"slot": (date(...), date(...)), "trainers": ["Name A", "Name B"]}, ...]
```

**Guarantees:**
- Every entry has exactly 2 trainers
- Both trainers available on both days of their slot
- No trainer appears on the same calendar day in more than one entry
- When config provided: every entry has at least 1 experienced trainer
- Result is globally optimal: no other valid assignment schedules more bootcamps
- Entries are ordered by slot start date ascending
- Returns `[]` if no feasible solution found or `slots` is empty

## Rules

1. Each slot is either scheduled (active) or skipped
2. Exactly 2 trainers must be assigned to each active slot
3. A trainer may only be assigned to a slot if available (`True`) on both days
4. No trainer can be booked on the same calendar day in more than one slot
5. If `config["experienced"]` is provided: each active slot must include at least 1 experienced trainer
6. Objective: maximise the total number of active slots
7. Solver timeout: 30 seconds (`solver.parameters.max_time_in_seconds = 30`)
8. Return best feasible solution found within timeout; return `[]` only if no feasible solution exists

## Acceptance Criteria

- **AC1**: Returns a `list` of dicts each with `"slot"` and `"trainers"` keys
- **AC2**: Every entry has exactly 2 trainers, both available on both days
- **AC3**: No trainer is double-booked on the same day across entries
- **AC4**: With `config=CONFIG` on `basic.xlsx`, every entry contains at least 1 trainer from `CONFIG["experienced"]`
- **AC5**: With `config=CONFIG` on `basic.xlsx`, optimal finds ≥5 bootcamps (greedy finds 4 due to local choices)
- **AC6**: `len(schedule_optimal(...)) >= len(schedule_greedy(...))` — optimal never finds fewer than greedy
- **AC7**: `schedule_optimal(dates, trainers, [], config=None)` returns `[]`

## Test Cases

```python
from scheduler import parse_availability, generate_slots, schedule_greedy, schedule_optimal

CONFIG = {
    "experienced": {"Alice Chen", "Bob Smith", "Diana Müller"},
    "trainees": {"Carol Jones"},
}

def test_returns_list_of_dicts():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    schedule = schedule_optimal(dates, trainers, slots, config=CONFIG)
    assert isinstance(schedule, list)
    for entry in schedule:
        assert "slot" in entry and "trainers" in entry

def test_each_bootcamp_has_two_trainers():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    schedule = schedule_optimal(dates, trainers, slots, config=CONFIG)
    for entry in schedule:
        assert len(entry["trainers"]) == 2

def test_experience_rules_enforced():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    schedule = schedule_optimal(dates, trainers, slots, config=CONFIG)
    for entry in schedule:
        assert set(entry["trainers"]) & CONFIG["experienced"]

def test_optimal_finds_at_least_five():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    schedule = schedule_optimal(dates, trainers, slots, config=CONFIG)
    assert len(schedule) >= 5

def test_optimal_not_worse_than_greedy():
    dates, trainers = parse_availability("data/basic.xlsx")
    slots = generate_slots(dates, trainers)
    greedy = schedule_greedy(dates, trainers, slots, config=CONFIG)
    optimal = schedule_optimal(dates, trainers, slots, config=CONFIG)
    assert len(optimal) >= len(greedy)
```

## Edge Cases

| Case | Input | Expected behaviour |
|------|-------|--------------------|
| Empty slots | `slots=[]` | Returns `[]` |
| No feasible solution | All slots require experienced, none available | Returns `[]` |
| Single slot, 2 trainers | Exactly 1 valid slot with exactly 2 available trainers | Returns that 1 bootcamp |
| Solver timeout | Very large problem | Returns best solution found so far |

## Engineering Notes

**CP-SAT model:**

```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
```

**Variables:**
- `x[t_idx, s_idx]` = `model.new_bool_var(...)` — trainer `t` assigned to slot `s`. Only create this variable when `trainers[name][d1]` and `trainers[name][d2]` are both `True`. Unavailable combinations don't get a variable (implicitly 0).
- `active[s_idx]` = `model.new_bool_var(...)` — slot `s` is scheduled

**Key constraints:**
```python
# Exactly 2 trainers per active slot
model.add(sum(x[t, s] for all t) == 2 * active[s])

# No double-booking: trainer works at most 1 bootcamp per day
for each trainer t, for each date d:
    model.add(sum(x[t, s] for s where d in slot s) <= 1)

# Experience: at least 1 experienced per active slot
model.add(sum(x[t, s] for t in experienced) >= active[s])
```

**Objective:**
```python
model.maximize(sum(active))
```

**Result extraction:**
```python
status = solver.solve(model)
if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    return []
```

- Sort trainer names before indexing to ensure deterministic variable naming
- Return entries ordered by slot index (which follows slot order from input `slots`)
- Forward-compatible: include optional kwargs `trainer_info=None, weekly_caps=None, locations=None, weightings=None` in signature — they will be wired up in later challenges
