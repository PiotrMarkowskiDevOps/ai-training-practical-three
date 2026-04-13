# Spec: parse_availability

## Overview

Reads a trainer availability spreadsheet (`.xlsx`) and returns a sorted list of dates plus a nested dict mapping each trainer to their availability on each date. This is the entry point for all scheduling — every other function depends on its output.

## Inputs

| Parameter  | Type  | Required | Description                                      |
|------------|-------|----------|--------------------------------------------------|
| `filepath` | `str` | yes      | Path to an `.xlsx` file with an Availability sheet |

**File format — `Availability` sheet:**
- Row 1: headers — column A is `"Name"`, remaining columns are date strings in `"YYYY-MM-DD"` format
- Rows 2+: one trainer per row — column A is the trainer's full name, remaining cells are `"Yes"` (available) or empty/`None` (not available)
- Sheet name: `"Availability"` (use the active/first sheet if not found by name)
- Encoding: handled by openpyxl (UTF-8 compatible)

Example layout (`data/basic.xlsx`, 5 trainers, 20 dates):

```
Name        | 2026-03-16 | 2026-03-17 | ...
Alice Chen  | Yes        | Yes        | ...
Bob Smith   | Yes        |            | ...
```

## Outputs

Returns a `tuple` with at least 2 elements:

```python
(dates, trainers)
```

- `dates`: `list[datetime.date]` — all dates parsed from the header row, sorted ascending, as `date` objects (not strings, not datetimes)
- `trainers`: `dict[str, dict[datetime.date, bool]]` — for every trainer, for every date, `True` if the cell was `"Yes"`, `False` otherwise

**Guarantees:**
- `dates` is sorted ascending
- Every trainer dict contains an entry for every date (no missing keys)
- Availability values are strictly `bool` (`True`/`False`), never `None` or `"Yes"`

## Rules

1. Parse dates from the header row (row 1) using `datetime.date.fromisoformat()` — skip column A (`"Name"` header)
2. Parse trainer names from column A of each data row — skip row 1
3. A cell value of `"Yes"` (case-sensitive) maps to `True`; any other value (empty, `None`, anything else) maps to `False`
4. The returned `dates` list must be sorted ascending
5. Every trainer's availability dict must contain an entry for every date in `dates`
6. The return value must be a `tuple` with the dates list at index 0 and the trainers dict at index 1

## Acceptance Criteria

- **AC1**: `parse_availability("data/basic.xlsx")` returns a tuple where `result[0]` is a list of 20 `date` objects
- **AC2**: `result[0]` is sorted — `result[0] == sorted(result[0])`
- **AC3**: `result[1]` contains exactly 5 trainers, including `"Alice Chen"` and `"Bob Smith"`
- **AC4**: `result[1]["Alice Chen"][date(2026, 3, 16)]` is `True`
- **AC5**: `result[1]["Carol Jones"][date(2026, 3, 16)]` is `False`
- **AC6**: Every trainer in `result[1]` has an entry for every date in `result[0]` — no `KeyError` possible
- **AC7**: All values in all trainer dicts are `bool` — `isinstance(v, bool)` is `True` for all

## Test Cases

```python
from datetime import date
from scheduler import parse_availability

def test_returns_tuple_with_two_elements():
    result = parse_availability("data/basic.xlsx")
    assert isinstance(result, tuple)
    assert len(result) >= 2

def test_dates_are_sorted_date_objects():
    dates = parse_availability("data/basic.xlsx")[0]
    assert len(dates) == 20
    assert all(isinstance(d, date) for d in dates)
    assert dates == sorted(dates)

def test_alice_available_monday_week1():
    trainers = parse_availability("data/basic.xlsx")[1]
    assert trainers["Alice Chen"][date(2026, 3, 16)] is True

def test_carol_not_available_monday_week1():
    trainers = parse_availability("data/basic.xlsx")[1]
    assert trainers["Carol Jones"][date(2026, 3, 16)] is False

def test_all_dates_in_every_trainer():
    dates, trainers = parse_availability("data/basic.xlsx")[:2]
    for name, avail in trainers.items():
        for d in dates:
            assert d in avail
```

## Edge Cases

| Case | Input | Expected behaviour |
|------|-------|--------------------|
| Cell is `None` | Empty cell in spreadsheet | Treated as `False` |
| Cell is `"yes"` (lowercase) | `"yes"` in a cell | Treated as `False` — match is case-sensitive |
| Extra whitespace in name | `" Alice Chen "` | Strip whitespace from trainer names |
| Date column already sorted | Dates in header are in order | Output is still explicitly sorted (don't assume order) |
| Single trainer, single date | 1 row, 1 date column | Returns list of 1 date, dict with 1 trainer |

## Engineering Notes

- Use `openpyxl` (`load_workbook(filepath, read_only=True, data_only=True)`) — already in `requirements.txt`
- Use `datetime.date.fromisoformat(str(cell_value))` to parse date headers — header values may already be `date` objects or strings depending on openpyxl version; coerce with `str()` first
- Trainer names: strip leading/trailing whitespace
- Do **not** raise on missing cells — treat them as `False`
- Raise `FileNotFoundError` if the file does not exist (openpyxl raises this naturally)
