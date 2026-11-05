#!/usr/bin/env python3
"""Build the training block: Intervals.icu events, the calendar page data, and a target report.

Targets are % of FTP, so workouts rescale when FTP changes.

  build_plan.py --athlete athlete.json --out-events events.json --out-page data.json
  build_plan.py ... --actuals actuals.json   # merge ridden workouts and CTL/ATL into the page
  build_plan.py ... --today 2026-11-03       # drop dates already past from events.json
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
ZONE_TOPS = [55, 75, 90, 105, 120, 150]  # Coggan power zones, % FTP


def steady(minutes, pct):
    return {"sec": minutes * 60, "from": pct, "to": pct}


def ramp(minutes, start, end):
    return {"sec": minutes * 60, "from": start, "to": end}


def section(title, steps, repeat=1):
    return {"title": title, "repeat": repeat, "steps": steps}


def warmup():
    return section("Warmup", [ramp(10, 50, 70), steady(2, 85), steady(3, 60)])


def cooldown(endurance_minutes):
    steps = [steady(endurance_minutes, 65)] if endurance_minutes else []
    return section("Cooldown", steps + [ramp(5, 60, 45)])


def vo2(reps, minutes, pct, tail):
    return {
        "name": f"VO2max {reps}×{minutes}",
        "type": "vo2max",
        "notes": (
            f"{reps} × {minutes} min at {pct}% FTP with equal easy spinning between. "
            "Hard but even: the last rep should match the first, with HR reaching about 158+ bpm by the end. "
            "If you cannot hold a rep, drop 3% for the rest of the set instead of stopping."
        ),
        "sections": [
            warmup(),
            section("Main Set", [steady(minutes, pct), steady(minutes, 55)], reps),
            cooldown(tail),
        ],
    }


def threshold(reps, minutes, pct, rest, tail):
    label = "Sweet Spot" if pct <= 90 else "Threshold"
    return {
        "name": f"{label} {reps}×{minutes}",
        "type": "sweet-spot" if pct <= 90 else "threshold",
        "notes": (
            f"{reps} × {minutes} min at {pct}% FTP. Comfortably hard: full sentences are a struggle, "
            "but you could keep going. This is the main FTP builder, so keep the power steady."
        ),
        "sections": [
            warmup(),
            section("Main Set", [steady(minutes, pct), steady(rest, 55)], reps),
            cooldown(tail),
        ],
    }


def endurance(blocks):
    minutes = blocks * 15 + 15
    return {
        "name": f"Endurance {minutes}",
        "type": "endurance",
        "notes": (
            "Steady zone 2 with short tempo lifts to stay engaged. Conversational throughout, "
            "and HR should stay near or below 135 bpm outside the lifts. Ease off if it drifts higher."
        ),
        "sections": [
            section("Warmup", [ramp(10, 50, 65)]),
            section("Main Set", [steady(12, 65), steady(3, 74)], blocks),
            section("Cooldown", [ramp(5, 60, 45)]),
        ],
    }


def vo2_long(reps, minutes, pct, blocks, tail=0):
    """VO2max set plus endurance in one ride, for weeks with fewer riding days."""
    workout = vo2(reps, minutes, pct, tail)
    workout["name"] += " + Endurance"
    workout["notes"] += " Then settle into steady zone 2. Short on time? Cut the endurance, not the main set."
    workout["sections"].insert(2, section("Endurance", [steady(12, 65), steady(3, 74)], blocks))
    return workout


def easy_endurance(minutes, day):
    """Flat zone 2 with no lifts, for a low-recovery day. day overrides the slot's usual weekday."""
    return {
        "name": f"Easy Endurance {minutes + 15}",
        "type": "endurance",
        "day": day,
        "notes": (
            "Low recovery, so keep this truly easy: steady zone 2 with no surges, conversational throughout. "
            "HR should stay near or below 135 bpm. If it won't, or your legs stay heavy, ease to 60% FTP or finish early. "
            "Saturday's intervals matter more than these minutes."
        ),
        "sections": [
            section("Warmup", [ramp(10, 50, 65)]),
            section("Main Set", [steady(minutes, 65)]),
            section("Cooldown", [ramp(5, 60, 45)]),
        ],
    }


def openers(reps, minutes, pct, tail):
    return {
        "name": f"Recovery Threshold {reps}×{minutes}",
        "type": "threshold",
        "notes": (
            "Lighter week. Controlled threshold work keeps your zone 4-5 minutes on target without "
            "digging a hole. Stop feeling fresh."
        ),
        "sections": [
            warmup(),
            section("Main Set", [steady(minutes, pct), steady(3, 55)], reps),
            cooldown(tail),
        ],
    }


def recovery(blocks):
    workout = endurance(blocks)
    workout["name"] = f"Easy Endurance {blocks * 15 + 15}"
    workout["notes"] = "Lighter week. Easy and relaxed: finish wanting more."
    return workout


def ramp_test():
    # Each step adds about 20 W at 125 W FTP, the standard ramp protocol.
    climb = [steady(1, pct) for pct in (64, 80, 96, 112, 128, 144, 160, 176)]
    return {
        "name": "Ramp Test",
        "type": "test",
        "notes": (
            "Come in rested and ride to failure. New FTP = 75% of your best 1-minute power. "
            "Zwift's built-in Ramp Test works too. Update FTP in both Zwift and Intervals.icu afterwards, "
            "or workout targets will differ between them. Stop immediately if you feel unwell."
        ),
        "sections": [
            section("Warmup", [ramp(5, 45, 65), steady(3, 65)]),
            section("Ramp to failure", climb),
            section("Cooldown", [steady(10, 50)]),
        ],
    }


# One row per training week, Monday first: (phase, key day, threshold day, endurance day).
WEEKS = [
    ("Build 1", easy_endurance(60, "thu"), vo2(5, 3, 108, 10), None),
    ("Build 1", None, vo2_long(5, 3, 110, 3), endurance(6)),
    ("Build 1", vo2(4, 4, 110, 10), threshold(3, 10, 90, 4, 10), endurance(5)),
    ("Recovery", openers(3, 5, 100, 5), recovery(2), recovery(3)),
    ("Build 2", ramp_test(), threshold(2, 10, 95, 5, 30), endurance(6)),
    ("Build 2", vo2(5, 4, 108, 10), threshold(3, 12, 90, 4, 10), endurance(5)),
    ("Build 2", vo2(5, 4, 110, 10), threshold(2, 20, 90, 5, 8), endurance(5)),
    ("Recovery", openers(3, 5, 100, 5), recovery(2), recovery(3)),
    ("Retest", ramp_test(), None, None),
]

SLOTS = ("key", "threshold", "endurance")


def fmt_duration(sec):
    return f"{sec // 60}m" if sec % 60 == 0 else f"{sec // 60}m{sec % 60}s"


def to_intervals_text(workout):
    """Render as Intervals.icu workout syntax, the format it parses and syncs to Zwift."""
    lines = []
    for sec in workout["sections"]:
        lines.append(f"{sec['title']} {sec['repeat']}x" if sec["repeat"] > 1 else sec["title"])
        for st in sec["steps"]:
            dur = fmt_duration(st["sec"])
            if st["from"] == st["to"]:
                lines.append(f"- {dur} {st['from']}%")
            else:
                lines.append(f"- {dur} ramp {st['from']}%-{st['to']}%")
        lines.append("")
    return "\n".join(lines).strip()


def flat_steps(workout):
    return [st for sec in workout["sections"] for _ in range(sec["repeat"]) for st in sec["steps"]]


def percent_samples(workout):
    for st in flat_steps(workout):
        for i in range(st["sec"]):
            yield st["from"] + (st["to"] - st["from"]) * i / st["sec"]


def zone_of(pct):
    for i, top in enumerate(ZONE_TOPS):
        if pct <= top:
            return i + 1
    return 7


def metrics(workout):
    secs = [0] * 8
    total = 0
    fourth = 0.0
    for pct in percent_samples(workout):
        secs[zone_of(pct)] += 1
        total += 1
        fourth += (pct / 100) ** 4
    intensity = (fourth / total) ** 0.25
    return {
        "minutes": round(total / 60),
        "tss": round(total / 3600 * intensity**2 * 100),
        "z23": round((secs[2] + secs[3]) / 60, 1),
        "z45": round((secs[4] + secs[5]) / 60, 1),
    }


def build(athlete):
    first_monday = date.fromisoformat(athlete["plan"]["first_monday"])
    end = date.fromisoformat(athlete["plan"]["end"])
    offsets = {slot: DAYS.index(athlete["ride_days"][slot]) for slot in SLOTS}
    workouts, weeks = [], []
    for w, (phase, *slots) in enumerate(WEEKS):
        monday = first_monday + timedelta(weeks=w)
        rides = []
        for slot, workout in zip(SLOTS, slots):
            if workout is None:
                continue
            offset = DAYS.index(workout["day"]) if "day" in workout else offsets[slot]
            day = monday + timedelta(days=offset)
            if day > end:
                continue
            ride = {"date": day.isoformat(), "phase": phase, "workout": workout, **metrics(workout)}
            rides.append(ride)
        workouts.extend(rides)
        weeks.append({
            "monday": monday.isoformat(),
            "phase": phase,
            "z23": round(sum(r["z23"] for r in rides)),
            "z45": round(sum(r["z45"] for r in rides)),
            "minutes": sum(r["minutes"] for r in rides),
            "tss": sum(r["tss"] for r in rides),
        })
    workouts.sort(key=lambda r: r["date"])
    return workouts, weeks


def report(weeks, targets, credit):
    print(f"{'week of':<12}{'phase':<10}{'min':>5}{'TSS':>5}{'Z2-3':>6}{'Z4-5':>6}  status")
    missed_hard = False
    for wk in weeks:
        wk["z23"] += credit.get(wk["monday"], 0)
        z23_ok = wk["z23"] >= targets["z2_z3_min"]
        z45_ok = wk["z45"] >= targets["z4_z5_min"]
        if z23_ok and z45_ok:
            status = "on target"
        elif wk["phase"] in ("Recovery", "Retest"):
            status = "below target by design"
        else:
            status = "MISSES TARGET"
            missed_hard = True
        print(f"{wk['monday']:<12}{wk['phase']:<10}{wk['minutes']:>5}{wk['tss']:>5}{wk['z23']:>6}{wk['z45']:>6}  {status}")
    return not missed_hard


def to_event(ride):
    workout = ride["workout"]
    return {
        "start_date_local": f"{ride['date']}T00:00:00",
        "name": workout["name"],
        "category": "WORKOUT",
        "event_type": "VirtualRide",
        "description": f"{workout['notes']}\n\n{to_intervals_text(workout)}",
        "duration_seconds": ride["minutes"] * 60,
        "training_load": ride["tss"],
        "tags": ["indoor", "zwift-coach", workout["type"]],
    }


def to_page_steps(workout, ftp):
    """Steps as [seconds, watts]. The calendar draws flat bars, so ramps become one bar per minute."""
    bars = []
    for st in flat_steps(workout):
        slices = 1 if st["from"] == st["to"] else max(1, st["sec"] // 60)
        for i in range(slices):
            pct = st["from"] + (st["to"] - st["from"]) * (i + 0.5) / slices
            bars.append([st["sec"] // slices, round(pct * ftp / 100)])
    return bars


def page_target(workout, ftp):
    main = next(sec for sec in workout["sections"] if sec["title"] == "Main Set") if workout["type"] != "test" else None
    if not main:
        return "Ride to failure"
    watts = round(main["steps"][0]["from"] * ftp / 100)
    return f"{watts} W" if workout["type"] != "endurance" else f"{round(65 * ftp / 100)} W + lifts"


def to_page_event(ride, ftp):
    workout = ride["workout"]
    return {
        "id": f"p_{ride['date']}",
        "date": ride["date"],
        "name": workout["name"],
        "type": workout["type"],
        "status": "planned",
        "minutes": ride["minutes"],
        "tss": ride["tss"],
        "watts": page_target(workout, ftp),
        "notes": workout["notes"],
        "steps": to_page_steps(workout, ftp),
    }


def merge_actuals(events, actuals):
    """Overlay ridden workouts on the plan. An actual replaces the plan entry it names, or is added."""
    by_date = {e["date"]: e for e in events}
    for done in actuals.get("rides", []):
        target = by_date.get(done.get("planned_date", done["date"]))
        if target:
            target.update(done)
            target["status"] = "done"
        else:
            events.append({"id": f"a_{done['date']}", "type": "endurance", "status": "done", **done})
    for moved in actuals.get("moved", []):
        target = by_date.get(moved["from"])
        if target:
            target["date"] = moved["to"]
    return sorted(events, key=lambda e: e["date"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--athlete", required=True)
    ap.add_argument("--out-events")
    ap.add_argument("--out-page")
    ap.add_argument("--actuals")
    ap.add_argument("--today", help="YYYY-MM-DD; rides before this date are left out of the events file")
    args = ap.parse_args()

    with open(args.athlete) as f:
        athlete = json.load(f)
    rides, weeks = build(athlete)
    ok = report(weeks, athlete["weekly_targets"], athlete["plan"].get("z2_z3_credit", {}))

    if args.out_events:
        keep = [r for r in rides if not args.today or r["date"] >= args.today]
        with open(args.out_events, "w") as f:
            json.dump([to_event(r) for r in keep], f, indent=1, ensure_ascii=False)
    if args.out_page:
        actuals = {}
        if args.actuals:
            with open(args.actuals) as f:
                actuals = json.load(f)
        page = {
            "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "ftp": athlete["ftp"],
            "events": merge_actuals([to_page_event(r, athlete["ftp"]) for r in rides], actuals),
            "form": actuals.get("form"),
        }
        with open(args.out_page, "w") as f:
            json.dump(page, f, ensure_ascii=False, separators=(",", ":"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
