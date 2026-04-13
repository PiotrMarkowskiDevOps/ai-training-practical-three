# Spec: apply_bank_holidays + parse_weightings + schedule_optimal (weightings)

## Overview

Three additions for the full production system:

1. **`apply_bank_holidays(trainers, trainer_info)`** — modifies the `trainers` availability dict in place, setting any date that is a public holiday in the trainer's home country to `False`. Uses the `holidays` library with a mapping from city names to ISO country codes.

2. **`parse_weightings(filepath)`** — reads the `Weightings` sheet from `advanced.xlsx` and returns a `dict[str, int]` mapping trainer name to their preference weight.

3. **`schedule_optimal`** — extended to accept `weightings=None`. When provided, adds a soft secondary objective: among solutions with the same number of bootcamps, prefer those using higher-weighted trainers.

## Inputs

### apply_bank_holidays

| Parameter      | Type                          | Required | Description |
|----------------|-------------------------------|----------|-------------|
| `trainers`     | `dict[str, dict[date, bool]]` | yes      | Trainer availability map — **modified in place** |
| `trainer_info` | `dict[str, dict]`             | yes      | Trainer metadata with `home_location` key |

### parse_weightings

| Parameter  | Type  | Required | Description |
|------------|-------|----------|-------------|
| `filepath` | `str` | yes      | Path to `.xlsx` file containing a `Weightings` sheet |

**Weightings sheet format** (`advanced.xlsx`):
```
Name        | Weight
Alice Chen  | 3
Bob Smith   | 2
Carol Jones | 1
Diana Müller| 3
Eve Brown   | 1
```
- Row 1: header (`Name`, `Weight`)
- Rows 2+: one trainer per row

### schedule_optimal (new parameter)

| Parameter    | Type                    | Required | Description |
|--------------|-------------------------|----------|-------------|
| `weightings` | `dict[str, int] \| None` | no      | Trainer preference weights from `parse_weightings`. Default: `None` |

## Outputs

### apply_bank_holidays

Returns `None`. Modifies `trainers` in place — sets `trainers[name][date] = False` for any date that is a public holiday in the trainer's home country.

### parse_weightings

Returns `dict[str, int]` — trainer name → integer weight. Order matches spreadsheet row order.

### schedule_optimal

Unchanged `list[dict]` format. When `weightings` is provided, result prefers higher-weighted trainers but total bootcamp count is never sacrificed.

## Rules

### apply_bank_holidays
1. Determine each trainer's country from `trainer_info[name]["home_location"]` using this mapping (case-insensitive):
   - `london`, `manchester`, `bristol` → `"GB"`
   - `paris` → `"FR"`
   - `amsterdam` → `"NL"`
   - `stockholm` → `"SE"`
2. If a trainer's home location is unknown or not in the mapping, skip them (no holidays applied)
3. Use `holidays.country_holidays(country_code, years={year})` for each relevant year in the trainer's dates
4. For each date in `trainers[name]`: if that date is in the country's holidays, set to `False`
5. Only set to `False` — never override `False` with `True`
6. Different countries have different holidays — UK Good Friday blocks UK trainers, not French trainers

### parse_weightings
7. Read the sheet named `"Weightings"` (not active sheet)
8. Skip header row and any row where `Name` is `None`
9. Cast `Weight` to `int`

### schedule_optimal with weightings
10. Objective becomes: `BIG_M * sum(active) + sum(weight[t] * x[t,s] for all t,s)`
    where `BIG_M` is large enough that adding one more bootcamp always outweighs any weight difference (e.g. `BIG_M = 1000`)
11. Trainers not in `weightings` dict get weight `0`

## Acceptance Criteria

- **AC1**: After `apply_bank_holidays`, `trainers["Alice Chen"][date(2026, 4, 3)]` is `False` (Alice is London/UK; Good Friday is 3 Apr 2026)
- **AC2**: After `apply_bank_holidays`, `trainers["Diana Müller"][date(2026, 4, 3)]` remains `True` (Diana is Paris/France; Good Friday is not a French public holiday)
- **AC3**: `parse_weightings("data/advanced.xlsx")` returns a non-empty `dict` with `int` values
- **AC4**: `parse_weightings(...)["Alice Chen"] == max(weightings.values())` — Alice has the highest weight (3)
- **AC5**: Full pipeline (parse → apply_bank_holidays → generate_slots → schedule_optimal with all params) returns a non-empty schedule
- **AC6**: `apply_bank_holidays` returns `None` (modifies in place)

## Test Cases

```python
from datetime import date
from scheduler import apply_bank_holidays, parse_availability, parse_weightings, \
                     generate_slots, schedule_optimal, parse_locations

ADVANCED = "data/advanced.xlsx"

def test_good_friday_blocks_london_trainer():
    dates, trainers, trainer_info, _ = parse_availability(ADVANCED)
    trainers["Alice Chen"][date(2026, 4, 3)] = True  # force available
    apply_bank_holidays(trainers, trainer_info)
    assert trainers["Alice Chen"][date(2026, 4, 3)] is False

def test_good_friday_does_not_block_paris_trainer():
    dates, trainers, trainer_info, _ = parse_availability(ADVANCED)
    trainers["Diana Müller"][date(2026, 4, 3)] = True  # force available
    apply_bank_holidays(trainers, trainer_info)
    assert trainers["Diana Müller"][date(2026, 4, 3)] is True

def test_parse_weightings_structure():
    weightings = parse_weightings(ADVANCED)
    assert isinstance(weightings, dict)
    assert len(weightings) > 0
    for name, w in weightings.items():
        assert isinstance(w, (int, float))

def test_alice_has_highest_weight():
    weightings = parse_weightings(ADVANCED)
    assert weightings["Alice Chen"] == max(weightings.values())

def test_full_pipeline_runs():
    dates, trainers, trainer_info, weekly_caps = parse_availability(ADVANCED)
    apply_bank_holidays(trainers, trainer_info)
    slots = generate_slots(dates, trainers)
    locations = parse_locations(ADVANCED)
    weightings = parse_weightings(ADVANCED)
    config = {"experienced": {"Alice Chen", "Bob Smith", "Diana Müller"}, "trainees": {"Carol Jones"}}
    schedule = schedule_optimal(dates, trainers, slots, config=config,
                                trainer_info=trainer_info, weekly_caps=weekly_caps,
                                locations=locations, weightings=weightings)
    assert isinstance(schedule, list)
    assert len(schedule) > 0
```

## Edge Cases

| Case | Input | Expected behaviour |
|------|-------|--------------------|
| Unknown home location | `home_location = "Tokyo"` | No holidays applied for that trainer |
| `home_location = None` | Missing location | Skip trainer |
| Trainer not in weightings | Name not in dict | Treated as weight 0 |
| All weights equal | Same weight for all | Objective reduces to pure bootcamp count |
| Good Friday in UK | 2026-04-03, Alice (London) | Set to `False` |
| Good Friday in France | 2026-04-03, Diana (Paris) | Unchanged — not a French holiday |

## Engineering Notes

- **Library:** `import holidays` — already in `requirements.txt`
- **Country holiday lookup:**
  ```python
  import holidays as hols
  country_holidays = hols.country_holidays("GB", years=2026)
  date(2026, 4, 3) in country_holidays  # True
  ```
- **City-to-code mapping** (build as a module-level dict for easy extension):
  ```python
  LOCATION_COUNTRY_CODES = {
      "london": "GB", "manchester": "GB", "bristol": "GB",
      "paris": "FR", "amsterdam": "NL", "stockholm": "SE",
  }
  ```
- **Years:** collect `{d.year for d in trainers[name]}` to handle multi-year date ranges
- **Weighted objective in CP-SAT:**
  ```python
  BIG_M = 1000
  weight_bonus = sum(weightings.get(name, 0) * x[t_idx, s_idx]
                     for t_idx, name in enumerate(trainer_names)
                     for s_idx in range(n_slots) if (t_idx, s_idx) in x)
  model.maximize(BIG_M * sum(active) + weight_bonus)
  ```
- Modify `apply_bank_holidays` to guard against `trainer_info` being `None` for a trainer name — use `.get(name, {})`
