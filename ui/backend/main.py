import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scheduler import (
    apply_bank_holidays,
    generate_slots,
    parse_availability,
    parse_locations,
    parse_weightings,
    schedule_greedy,
    schedule_optimal,
)

app = FastAPI(title="Bootcamp Scheduler API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _serialize_schedule(schedule: list[dict]) -> list[dict]:
    result = []
    for entry in schedule:
        d1, d2 = entry["slot"]
        result.append(
            {
                "slot": [str(d1), str(d2)],
                "trainers": entry["trainers"],
                "location": entry.get("location"),
            }
        )
    return result


def _run_schedule(
    filepath: Path,
    solver: str,
    config: dict,
    apply_holidays: bool,
) -> tuple[list[dict], str, int]:
    result = parse_availability(str(filepath))
    if len(result) == 4:
        dates, trainers, trainer_info, weekly_caps = result
        has_extended = True
    else:
        dates, trainers = result
        trainer_info = None
        weekly_caps = None
        has_extended = False

    if apply_holidays and trainer_info:
        apply_bank_holidays(trainers, trainer_info)

    slots = generate_slots(dates, trainers)

    locations = None
    weightings = None
    try:
        locations = parse_locations(str(filepath))
    except Exception:
        pass
    try:
        weightings = parse_weightings(str(filepath))
    except Exception:
        pass

    if solver == "greedy":
        schedule = schedule_greedy(dates, trainers, slots, config=config)
        solver_used = "greedy"
    else:
        schedule = schedule_optimal(
            dates,
            trainers,
            slots,
            config=config,
            trainer_info=trainer_info,
            weekly_caps=weekly_caps,
            locations=locations,
            weightings=weightings,
        )
        solver_used = "optimal"

    return schedule, solver_used


@app.get("/api/files")
def list_files():
    files = sorted(p.name for p in DATA_DIR.glob("*.xlsx"))
    return files


@app.get("/api/trainers")
def get_trainers(file: str = Query(...)):
    filepath = DATA_DIR / file
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file}")

    result = parse_availability(str(filepath))
    if len(result) == 4:
        dates, trainers, trainer_info, weekly_caps = result
        has_locations = False
        has_weightings = False
        try:
            parse_locations(str(filepath))
            has_locations = True
        except Exception:
            pass
        try:
            parse_weightings(str(filepath))
            has_weightings = True
        except Exception:
            pass
    else:
        dates, trainers = result
        trainer_info = None
        has_locations = False
        has_weightings = False

    return {
        "trainers": sorted(trainers.keys()),
        "has_locations": has_locations,
        "has_weightings": has_weightings,
    }


class ScheduleRequest(BaseModel):
    file: str
    solver: str = "optimal"
    config: Optional[dict] = None
    apply_bank_holidays: bool = True


@app.post("/api/schedule")
def run_schedule(req: ScheduleRequest):
    filepath = DATA_DIR / req.file
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {req.file}")

    config = {}
    if req.config:
        config = {
            "experienced": set(req.config.get("experienced", [])),
            "trainees": set(req.config.get("trainees", [])),
        }

    t0 = time.monotonic()
    schedule, solver_used = _run_schedule(
        filepath, req.solver, config, req.apply_bank_holidays
    )
    duration_ms = int((time.monotonic() - t0) * 1000)

    return {
        "schedule": _serialize_schedule(schedule),
        "solver_used": solver_used,
        "total_bootcamps": len(schedule),
        "duration_ms": duration_ms,
    }


@app.post("/api/schedule/compare")
def compare_schedules(req: ScheduleRequest):
    filepath = DATA_DIR / req.file
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {req.file}")

    config = {}
    if req.config:
        config = {
            "experienced": set(req.config.get("experienced", [])),
            "trainees": set(req.config.get("trainees", [])),
        }

    greedy_schedule, _ = _run_schedule(
        filepath, "greedy", config, req.apply_bank_holidays
    )
    optimal_schedule, _ = _run_schedule(
        filepath, "optimal", config, req.apply_bank_holidays
    )

    return {
        "greedy": {
            "schedule": _serialize_schedule(greedy_schedule),
            "total_bootcamps": len(greedy_schedule),
        },
        "optimal": {
            "schedule": _serialize_schedule(optimal_schedule),
            "total_bootcamps": len(optimal_schedule),
        },
    }
