# ac-setups

The setup cloud [AC Pro Engineer](https://github.com/Rgosh/ac-pro-engineer) reads.

The application fetches these files at runtime, straight from `main` over
`raw.githubusercontent.com`. There is no build step and no review between a push
and somebody's setup browser — whatever is on `main` is what a driver downloads
into their game a minute later.

## Layout

```
manifest.json        every car, how many setups it has, and who made them
<car_id>.json        the setups for one car, as a list
tools/validate.py    checks all of the above
tools/import_setup.py   turns an Assetto Corsa .ini into an entry
```

`<car_id>` is the folder name inside `assettocorsa/content/cars` — `bmw_z4_gt3`,
not "BMW Z4 GT3". `source` is the same for the track: the folder name under
`content/tracks`.

## Adding a setup

Save it in game, find the `.ini` under
`Documents/Assetto Corsa/setups/<car>/`, then:

```bash
tools/import_setup.py path/to/Spa.ini --car bmw_z4_gt3 --track spa \
    --name "Spa" --author "Your Name" --credits "whose work this builds on"
```

It writes the entry, regenerates `manifest.json` and validates the result. Doing
it by hand means forty-odd fields whose names do not match the ones in the file
you are copying from — `FRONT_BIAS` becomes `brake_bias`, `TOE_OUT_LF` becomes
`toe_lf` — and a typo is a setup that loads with one wrong value and no error.

Before pushing:

```bash
tools/validate.py
```

## What belongs here

Setups that someone has actually driven. A file here is presented to a driver as
a setup worth loading, and the application's engineer reads the loaded setup and
gives advice against it — so a plausible-looking set of numbers that was never
tested is worse than no entry at all, in two places at once.

Credit whoever made the setup in `author`, and whoever it is based on in
`credits`. If it came from someone else's work, ask them first.
