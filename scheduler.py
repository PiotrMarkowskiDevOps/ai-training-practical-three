# scheduler.py
#
# Build your bootcamp scheduler here.
#
# Work through the challenges in order:
#   Run /next in Claude Code to see what to do next.
#   Run /spec to write a specification for the next function.
#   Run /build to implement from your spec.
#   Run python3 -m pytest tests/ -v to verify what you've built.
#
# Each challenge adds new functions — don't remove old ones.

from datetime import date
import openpyxl


def parse_availability(filepath: str) -> tuple[list[date], dict[str, dict[date, bool]]]:
    """Read trainer availability from an xlsx file.

    Returns (dates, trainers) where dates is a sorted list of date objects
    and trainers maps trainer name -> {date -> bool}.
    """
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    # Parse dates from header row (row 0), skipping column A ("Name")
    header = rows[0]
    dates: list[date] = []
    for cell in header[1:]:
        if cell is not None:
            dates.append(date.fromisoformat(str(cell)))
    dates = sorted(dates)

    # Parse trainer rows (rows 1+)
    trainers: dict[str, dict[date, bool]] = {}
    for row in rows[1:]:
        if not row or row[0] is None:
            continue
        name = str(row[0]).strip()
        avail: dict[date, bool] = {}
        for i, d in enumerate(dates):
            cell_val = row[i + 1] if (i + 1) < len(row) else None
            avail[d] = cell_val == "Yes"
        trainers[name] = avail

    return (dates, trainers)
