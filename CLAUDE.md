# CLAUDE.md — working on ac-setups

This is the setup cloud [AC Pro Engineer](https://github.com/Rgosh/ac-pro-engineer)
reads. `README.md` describes the format; this describes how to work here without
breaking somebody's game.

## The thing to understand first

**There is nothing between a push and a driver's setup browser.** The
application fetches these files at runtime from `main` over
`raw.githubusercontent.com` — no build, no review, no cache to wait out. A
malformed `manifest.json` is live the moment it lands.

So: run `tools/validate.py` before pushing. It runs on every pull request too,
which is what makes it safe to accept a setup from someone you have never met.

## Do not invent setups

A file here is presented to a driver as a setup worth loading, and the
application's engineer reads the loaded setup and gives advice *against* it. A
plausible-looking set of numbers nobody has driven is therefore worse than no
entry at all, in two places at once.

There is also no arithmetic that produces one. The values are step indices into
ranges that live inside each car's encrypted `data.acd`: `spring_lf` is 80 on a
Lotus and 210 on a Z4, `wing_1` is 9 on one car and 0 on a car with no wing.
Nothing outside the game can turn one into the other.

Real setups come from three places: your own, someone else's with their
permission, or a pull request. `tools/import_setup.py` converts an Assetto
Corsa `.ini` into an entry so the forty-odd field names cannot be typed wrong.

## The bug that is already here

Eight of the published setups store anti-roll bars as a stiffness in N/m instead
of the click index the game reads — three BMW Z4 GT3 and five Mercedes SLS GT3.
AC clamps those to the stiffest setting, so what loads is not what the author
drove. `validate.py` reports them as warnings rather than errors, because a
heuristic must not be what stops a contributor's first pull request.

Fixing them needs the original `.ini` files or the author. It cannot be done by
converting the numbers: that needs the car's range, and the range is in
`data.acd`.
