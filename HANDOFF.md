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

## v4 (seed 313, current)
- Big blobs are crisp vector art (shapes.py: flame + drop, same aspect AR=1.3), anchored at the bottom (BOT) and growing upward.
- Gains go into a pending pool that flows in at 5%/frame (FEED), so size and number grow gradually.
- Pixel-exact touch: a runner hitting any pixel of its own big one is absorbed ('eat'); hitting the enemy's fizzles ('fizzle').
- Win: first big one whose top reaches the dashed line under the HUD (TOPWIN) fills the screen and wins. No touching rule. K=5.5.
- Seed 313: 39.8 s, FIRE wins 13789 vs 11020 (loser at 90% height), 7 lead changes.

## v3 (seed 484)
- Conveyor removed. Each runner is born with a head badge x1/x2/x3/x5/x20/x100 (weights MULTS) and value 50*m.
- Crossing the middle grass line (SPLIT_ROW) with m>=2 spawns 2 new runners of the same side at the top (cap MAXN).
- Big ones have no size cap and may overflow the screen; a runner touching its own big one is absorbed immediately ('eat').
- Win: the two big ones touch (CX=[200,880], rad=K*sqrt(v)+10, K=4.5) -> bigger wins; also if all runners are gone.
- Graphics: textured roads, shadows, glow, colored x-badges, tug bar HUD, winner swells to fill the screen.
- Seed 484: 33.6 s, FIRE wins 6795 vs 6294, 14 eats.

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
