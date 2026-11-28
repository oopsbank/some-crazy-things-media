# Territory War
4 teams (fire, water, leaf, bolt) on a 48x48 grid; each ball moves in its own color and steals enemy cells it bounces off. Skills on cooldown: EXPLOSION (r6 circle), SPLIT (3 clone balls 260 f), GROW (28 frontier cells), BOLT (30-cell line, 3 wide). 40 s timer, most land wins.
Seed 189: Leaf beats Bolt by 1 tile, 13 lead changes.
Run: python3 sim.py; python3 render.py 189 v.mp4; python3 audio.py v.mp4.json a.wav; mux with ffmpeg.

## v2 (2 teams, sim2/render2/audio2)
Fire vs Water, army size follows territory, items every 50 f (star +3 balls, bomb r6, bolt speed), skills METEOR / TSUNAMI, LAST STAND +8 balls under 40%, first to 62% (win lines on tug bar) or 30 s. Seed 8: Fire wins at 27.6 s, 23 lead changes.
