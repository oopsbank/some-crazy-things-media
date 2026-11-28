# Animal Fight — handoff

New YouTube Shorts format (no channel yet). Two animal balls bounce in a square arena; each animal has 2 active skills on cooldown. Physics decides the winner. We render many seeds and keep the closest fight.

## Current film: Hedgehog vs Snake (approved direction)
- Hedgehog: SPIKE BURST (12 spikes out, 6 dmg each, cd 80 f), ROLL (1.9x speed 45 f, 10 dmg on contact, cd 130 f)
- Snake: VENOM (3 orbs, 3 dmg + poison 1 dmg/10 f, cd 75 f), SHED SKIN (heal 8, cd 280 f). User asked what Shed Skin does; consider renaming to HEAL.
- Body bump: 2 dmg each. SPEED=11 (user said 14 too fast, 10 with passive skills too simple/slow).
- Last render: seed 138, 33 s, 16 lead changes, Snake wins with 8 HP.

## Run
    python3 sim2.py                       # search seeds (prints win split + close fights)
    python3 render2.py <seed> v.mp4       # 1080x1920 30fps video, writes v.mp4.json events
    python3 audio2.py v.mp4.json a.wav    # synth SFX + beat
    ffmpeg -i v.mp4 -i a.wav -c:v copy -c:a aac -b:a 192k -shortest out_1080x1920.mp4
Needs Pillow, numpy, ffmpeg, JetBrains Mono ExtraBold, Noto Color Emoji (emoji used for animals; user may want custom drawn animals).

## Style
Reference the user liked: black bg, square grey arena, "A vs B" title on top, HP + skill cooldown bars under the arena, cast name flashes above arena, "WHO WINS?" intro, "<X> WINS!" ending with pop particles. Never use copyrighted characters.

## Ideas not done
Ultimate skill when HP < 20; more pairs (Turtle vs Skunk, Hedgehog vs Turtle); custom animal art.

## Workflow
Talk Vietnamese to the user. Make films only when asked. Deliver: push mp4 + thumb to oopsbank/some-crazy-things-media main (pull first), then message the manager session with title/description/pinned comment.
