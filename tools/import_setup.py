#!/usr/bin/env python3
"""Turn an Assetto Corsa setup .ini into a cloud entry.

Adding a setup by hand means writing out forty-odd JSON fields whose names do
not match the ones in the file you are copying from -- `FRONT_BIAS` becomes
`brake_bias`, `TOE_OUT_LF` becomes `toe_lf`, and a typo in any of them is a
setup that loads with one wrong value and no error. This does the mapping, and
the mapping is the one `setup_manager.rs` reads, field for field.

    tools/import_setup.py SETUP.ini --car bmw_z4_gt3 --track spa \
        --name "Spa" --author "AFN PRO" --credits "..."

It appends to <car>.json, refuses to write a duplicate name, and regenerates
manifest.json. Run tools/validate.py afterwards -- or just run it, it is
called at the end.
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# section -> json field, exactly as core/src/setup_manager.rs reads them.
# Unsigned in the Rust struct; these are the ones that may not go negative.
UNSIGNED = {
    "FUEL": "fuel",
    "FRONT_BIAS": "brake_bias",
    "ENGINE_LIMITER": "engine_limiter",
    "PRESSURE_LF": "pressure_lf",
    "PRESSURE_RF": "pressure_rf",
    "PRESSURE_LR": "pressure_lr",
    "PRESSURE_RR": "pressure_rr",
    "WING_1": "wing_1",
    "WING_2": "wing_2",
    "SPRING_RATE_LF": "spring_lf",
    "SPRING_RATE_RF": "spring_rf",
    "SPRING_RATE_LR": "spring_lr",
    "SPRING_RATE_RR": "spring_rr",
    "ARB_FRONT": "arb_front",
    "ARB_REAR": "arb_rear",
    "DAMP_BUMP_LF": "damp_bump_lf",
    "DAMP_BUMP_RF": "damp_bump_rf",
    "DAMP_BUMP_LR": "damp_bump_lr",
    "DAMP_BUMP_RR": "damp_bump_rr",
    "DAMP_REBOUND_LF": "damp_rebound_lf",
    "DAMP_REBOUND_RF": "damp_rebound_rf",
    "DAMP_REBOUND_LR": "damp_rebound_lr",
    "DAMP_REBOUND_RR": "damp_rebound_rr",
    "DIFF_POWER": "diff_power",
    "DIFF_COAST": "diff_coast",
    "FINAL_RATIO": "final_ratio",
}

# Camber, toe and rod length are step indices that go either side of zero.
SIGNED = {
    "CAMBER_LF": "camber_lf",
    "CAMBER_RF": "camber_rf",
    "CAMBER_LR": "camber_lr",
    "CAMBER_RR": "camber_rr",
    "TOE_OUT_LF": "toe_lf",
    "TOE_OUT_RF": "toe_rf",
    "TOE_OUT_LR": "toe_lr",
    "TOE_OUT_RR": "toe_rr",
    "ROD_LENGTH_LF": "rod_length_lf",
    "ROD_LENGTH_RF": "rod_length_rf",
    "ROD_LENGTH_LR": "rod_length_lr",
    "ROD_LENGTH_RR": "rod_length_rr",
}


def parse_ini(path):
    """AC setup files are `[SECTION]` / `VALUE=n`, and nothing more exotic."""
    values, section = {}, None
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
            elif "=" in line and section:
                key, _, raw = line.partition("=")
                values[(section, key.strip())] = raw.strip()
    return values


def to_entry(values, car, track, name, author, credits, notes):
    entry = {
        "name": name,
        "source": track,
        "author": author,
        "credits": credits,
        "car_id": car,
        "is_remote": True,
    }
    if notes:
        entry["notes"] = notes

    def number(section, signed):
        raw = values.get((section, "VALUE"))
        if raw is None:
            return 0
        try:
            value = int(float(raw))
        except ValueError:
            return 0
        # An unsigned field arriving negative is a misread, not a setting.
        return value if signed else max(value, 0)

    for section, field in UNSIGNED.items():
        entry[field] = number(section, signed=False)
    for section, field in SIGNED.items():
        entry[field] = number(section, signed=True)

    gears = []
    index = 1
    while ("GEAR_%d" % index, "VALUE") in values:
        gears.append(number("GEAR_%d" % index, signed=False))
        index += 1
    entry["gears"] = gears
    return entry


def rebuild_manifest():
    manifest = []
    for file in sorted(os.listdir(ROOT)):
        if not file.endswith(".json") or file == "manifest.json":
            continue
        car = file[: -len(".json")]
        with open(os.path.join(ROOT, file), encoding="utf-8") as handle:
            setups = json.load(handle)
        manifest.append(
            {
                "id": car,
                "count": len(setups),
                "authors": sorted({s.get("author", "") for s in setups if s.get("author")}),
            }
        )
    with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ini", help="the .ini saved by Assetto Corsa")
    parser.add_argument("--car", required=True, help="folder name, e.g. bmw_z4_gt3")
    parser.add_argument("--track", required=True, help="folder name, e.g. spa")
    parser.add_argument("--name", help="shown in the browser; defaults to the file name")
    parser.add_argument("--author", required=True, help="who made this setup")
    parser.add_argument("--credits", default="", help="whose work it is based on")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    if not os.path.isfile(args.ini):
        sys.exit("no such file: %s" % args.ini)

    name = args.name or os.path.splitext(os.path.basename(args.ini))[0]
    entry = to_entry(
        parse_ini(args.ini), args.car, args.track, name, args.author, args.credits, args.notes
    )

    path = os.path.join(ROOT, args.car + ".json")
    setups = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            setups = json.load(handle)
    if any(s.get("name") == name for s in setups):
        sys.exit(
            "%s already has a setup called %r — pass a different --name" % (args.car, name)
        )

    setups.append(entry)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(setups, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    rebuild_manifest()
    print("added %r to %s.json (%d setups now)" % (name, args.car, len(setups)))
    subprocess.run([sys.executable, os.path.join(HERE, "validate.py")], check=True)


if __name__ == "__main__":
    main()
