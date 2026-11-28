# Fill the Glass
Strawberry vs Blueberry drops fall through pegs, rotating bar, sliding x1-x10 conveyor and a sponge trap into two glasses (CAP 300). First to overflow wins.
Seed 113: Blueberry 300 vs 298, 21 lead changes, 42 s.
Run: python3 sim.py; python3 render.py 113 v.mp4; python3 audio.py v.mp4.json a.wav; mux with ffmpeg.

## v2 (upgraded graphics)
sim2.py/render2.py/audio2.py: spawn every 4 f, neon glass panels, glossy drops with motion tails, peg flash, fruit squeezers, liquid gradient + foam + ripples, crown on leader, red pulse + heartbeat over 90%, final score card. Seed 117: Strawberry 100% vs 99%, 28 s.
