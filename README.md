# news-image-20261118

Sum up Wednesday 18 November 2026's world news in one image — a make.fun
entry (`news-image-20261118`, $250, deadline 2026-11-20 00:00 UTC).

## What it draws

A newspaper front page, drawn entirely in code (no image assets, no
network):

- **Masthead:** WEDNESDAY 18 NOVEMBER 2026
- **Lead story — the Kerch Bridge:** the collapsed road span hanging into
  the strait, smoke over the gap, and a train crossing the surviving rail
  section. Headline: **THE BRIDGE, BROKEN** — "Road span down in the
  strait — trains run on; 141 drones overnight".
- **Three mini-stories:** Gulf strikes back (missile/drone trails over a
  Strait of Hormuz map), Three leaders, one table (US, China and Russia
  flags over the Shenzhen skyline), One light-day from home (Voyager 1,
  one pale dot of light a full day away).

## How it works

`main.py` is pure Python 3 standard library — no PIL, no external fonts.
It rasterises flat vector shapes and a hand-built single-stroke capital
font onto a 1024x1024 canvas and writes a deterministic PNG (fixed
geometry, no time, no randomness, zlib level 9, no ancillary chunks).

## Run

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
```

Two runs produce byte-identical output (verified: same sha256).
Output: 1024x1024 PNG, well under the 1 MiB limit.

## License

MIT — see `LICENSE`.
