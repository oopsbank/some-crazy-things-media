# Race — handoff

New YouTube Shorts format (no channel yet): two sides race, physics decides, we render many seeds and keep the closest.

## Current film: Fire vs Water "road crossing" (sim.py / render.py / audio.py)
- Mini fire and water characters (emoji with eyes) hop down from the top: road A (2 lanes, opposite directions) -> sliding conveyor of multipliers x1 x2 x3 x5 x20 x100 -> road B (2 lanes) -> finish line.
- Cars squash them (fire = smoke, water = splash). A multiplied runner carries its value (shown above it); losing it to a car shows "-N".
- Big Fire and Big Water at the bottom start at 100 and decay (x0.9975/frame). Arrivals add their value. Radius = 2.4*v+10.
  When the two radii touch, the bigger one wins and the other evaporates. If one hits 0 it loses.
- Intro text: "BIGGER ONE TOUCHES = WINS". Ending "<X> WINS!".
- Last render: seed 88, 39 s, 10 lead changes; Fire got x100 then Water got x100 4 frames later and won by 3.

## Rule update (v2, seed 18)
- Each side starts with only 5 small runners (START_N); no automatic spawning. Each runner carries a value starting at 50 (BASE), always shown on its head.
- Multiplier tile xN: value *= N (50 -> x2 -> 100, x100 -> 5000). Every multiply (N>=2) spawns 2 new runners of the same side at the top (SPAWN, capped at MAXN=40 per side).
- Big ones have no eyes. Radius = K*sqrt(v)+10 with K=3.5. Car gap GAP=(1300,2000).
- Also ends when both sides have no runners left: the bigger one wins.
- Seed 18: 38 s, Fire comes back with a 5000 runner and wins 6422 vs 6228.

## Older variant (plinko/)
Two mirrored peg-board lanes, rotating bar, x2 gate, trap; first to 100 wins. Seed 88: Fire 100-99.

## Run
    python3 sim.py                     # seed search
    python3 render.py <seed> v.mp4
    python3 audio.py v.mp4.json a.wav
    ffmpeg -i v.mp4 -i a.wav -c:v copy -c:a aac -b:a 192k -shortest out_1080x1920.mp4
Needs Pillow, numpy, ffmpeg, JetBrains Mono ExtraBold, Noto Color Emoji.

## Tunables the user may ask for
car speed/density (LANES, gap 560-950), x100 rarity (TILES widths, CONV), decay rate, character/car art.

## Workflow
Talk Vietnamese to the user. Make films only when asked. Deliver: push mp4 + thumb to oopsbank/some-crazy-things-media main (pull first), then message the manager session with title/description/pinned comment.
