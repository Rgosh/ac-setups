#!/usr/bin/env python3
"""Check the cloud before it reaches anyone's game.

Every file here is fetched at runtime by AC Pro Engineer over raw.githubusercontent,
straight from `main`. There is no build step and no review between a push and a
driver's setup browser, so a manifest that disagrees with the files, or a car
file with a missing field, is live the moment it is pushed.

    tools/validate.py

Exits non-zero and says what is wrong. It checks the same field names
`core/src/setup_manager.rs` reads, so a field this accepts is a field the
application will find.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_TEXT = ["name", "source", "author", "car_id"]

REQUIRED_NUMBERS = [
    "fuel", "brake_bias", "engine_limiter",
    "pressure_lf", "pressure_rf", "pressure_lr", "pressure_rr",
    "wing_1", "wing_2",
    "camber_lf", "camber_rf", "camber_lr", "camber_rr",
    "toe_lf", "toe_rf", "toe_lr", "toe_rr",
    "spring_lf", "spring_rf", "spring_lr", "spring_rr",
    "rod_length_lf", "rod_length_rf", "rod_length_lr", "rod_length_rr",
    "arb_front", "arb_rear",
    "damp_bump_lf", "damp_bump_rf", "damp_bump_lr", "damp_bump_rr",
    "damp_rebound_lf", "damp_rebound_rf", "damp_rebound_lr", "damp_rebound_rr",
    "diff_power", "diff_coast", "final_ratio",
]

# Fields the Rust struct holds as u32. A negative here is silently clamped or
# refuses to parse, depending on where it lands, and either way the setup the
# driver loads is not the setup that was published.
UNSIGNED = [f for f in REQUIRED_NUMBERS if not f.startswith(("camber", "toe", "rod_length"))]


def main():
    problems = []
    files = sorted(
        f for f in os.listdir(ROOT) if f.endswith(".json") and f != "manifest.json"
    )

    manifest_path = os.path.join(ROOT, "manifest.json")
    try:
        with open(manifest_path, encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        sys.exit("manifest.json does not parse: %s" % error)

    listed = {entry["id"]: entry for entry in manifest}
    total = 0

    for file in files:
        car = file[: -len(".json")]
        try:
            with open(os.path.join(ROOT, file), encoding="utf-8") as handle:
                setups = json.load(handle)
        except json.JSONDecodeError as error:
            problems.append("%s does not parse: %s" % (file, error))
            continue

        if not isinstance(setups, list) or not setups:
            problems.append("%s is not a non-empty list" % file)
            continue

        total += len(setups)
        names = set()

        for index, setup in enumerate(setups):
            where = "%s[%d]" % (file, index)

            for field in REQUIRED_TEXT:
                if not setup.get(field):
                    problems.append("%s has no %s" % (where, field))

            if setup.get("car_id") != car:
                problems.append(
                    "%s says car_id=%r but lives in %s"
                    % (where, setup.get("car_id"), file)
                )

            # The application only shows a setup as downloadable when this is
            # true; false means it is treated as a local file that is not there.
            if setup.get("is_remote") is not True:
                problems.append("%s is not marked is_remote" % where)

            name = setup.get("name")
            if name in names:
                problems.append("%s repeats the name %r" % (where, name))
            names.add(name)

            for field in REQUIRED_NUMBERS:
                value = setup.get(field)
                if not isinstance(value, int) or isinstance(value, bool):
                    problems.append("%s.%s is %r, expected a whole number" % (where, field, value))
                elif field in UNSIGNED and value < 0:
                    problems.append("%s.%s is negative (%d)" % (where, field, value))

            gears = setup.get("gears")
            if not isinstance(gears, list) or any(not isinstance(g, int) for g in gears):
                problems.append("%s.gears is %r, expected a list of numbers" % (where, gears))

        entry = listed.pop(car, None)
        if entry is None:
            problems.append("%s has no entry in manifest.json" % file)
        else:
            if entry.get("count") != len(setups):
                problems.append(
                    "manifest says %s has %s setups, the file has %d"
                    % (car, entry.get("count"), len(setups))
                )
            authors = sorted({s.get("author", "") for s in setups if s.get("author")})
            if sorted(entry.get("authors", [])) != authors:
                problems.append(
                    "manifest lists authors %r for %s, the file has %r"
                    % (entry.get("authors"), car, authors)
                )

    for car in listed:
        problems.append("manifest lists %s but there is no %s.json" % (car, car))

    if problems:
        print("%d problem(s):" % len(problems))
        for problem in problems:
            print("  " + problem)
        return 1

    print("OK — %d cars, %d setups, manifest agrees with every file" % (len(files), total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
