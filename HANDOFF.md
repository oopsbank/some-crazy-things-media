# Animal Fight — handoff

New YouTube Shorts format (no channel yet). Two animal balls bounce in a square arena; each animal has 2 active skills on cooldown. Physics decides the winner. We render many seeds and keep the closest fight.

## Current film: Hedgehog vs Snake (approved direction)
- Hedgehog: SPIKE BURST (12 spikes out, 6 dmg each, cd 80 f), ROLL (1.9x speed 45 f, 10 dmg on contact, cd 130 f)
- Snake: VENOM (3 orbs, 3 dmg + poison 1 dmg/10 f, cd 75 f), SHED SKIN (heal 8, cd 280 f). User asked what Shed Skin does; consider renaming to HEAL.
- Body bump: 2 dmg each. SPEED=11 (user said 14 too fast, 10 with passive skills too simple/slow).
- Last render: seed 138, 33 s, 16 lead changes, Snake wins with 8 HP.

## STANDARD FORMAT (approved by user, Turtle vs Skunk v3) — use for every new film
Reference code: sim3.py / render3.py / audio3.py (Turtle vs Skunk). Copy and adapt for new pairs.
- Each animal has 3 skills: skill 1, skill 2, and an ULTIMATE (skill 3, long cooldown ~12-15 s, gold-bordered bar that pulses when full).
- All skill bars charge from EMPTY at fight start (initial cd = full CD). Give the two ultimates different cooldowns so they never fire on the same frame.
- Ultimate cast = hit-stop: ~16 frozen frames, screen dims, rays from caster, "ULTIMATE" + skill name in the band above the arena, charge-up riser sound; then white flash + big screen shake on release. Ultimate impacts: colored flash, shake, particle burst, heavy SFX.
- Small HP bar follows under each animal (turns red and blinks below 25 HP), in addition to the HP panel under the arena.
- Animal art = pixel sprites (style P1, user-approved): pixelart.pixel_icon('<emoji>',104) — Noto emoji -> 24 px, 14 colours, dark outline, NEAREST upscale. Ball fill is a dark tint of the animal colour so the sprite pops.
- Basic skills must look polished too: trails, glow, hit particles, block sparks, soft composited clouds (draw translucent shapes on a separate layer and alpha_composite, never fill RGBA directly on the layer or it erases what is underneath).
- Balance with sim (win split about 45-55 over 300+ seeds), then pick a seed with many lead changes, both ultimates cast at least twice, 30-37 s, winner on <=10 HP.
- Pipeline: python3 sim3.py; python3 render3.py <seed> v.mp4; python3 audio3.py v.mp4.json a.wav; ffmpeg mux as above. Events in the json are already remapped to rendered frames (hit-stop included).

## Turtle vs Skunk v3 (current, approved)
Seed 351, 36 s, Turtle wins on 4 HP. Turtle: SHELL (invulnerable 50 f, cd 170), BITE (dash, 11 dmg, cd 100), ult TIDAL WAVE (ring, 14 dmg, washes away clouds, cd 440). Skunk: SPRAY (5 droplets x3, cd 70), STINK CLOUD (1 dmg/8 f inside, cd 120), ult TOXIC BOMB (16 dmg in radius 230 + cloud, blocked by SHELL, cd 370). Not yet posted.

## Octopus vs Crab v3 (sim4/render4/audio4) — current
Seed 533, 41 s, Crab wins on 2 HP, win split 51/49 over 2500 seeds.
Octopus: INK MINE (proximity trap, 4 dmg + slow, cd 90) | TENTACLE WHIP | ult KRAKEN. Crab: PEARL (ricochets 3x, 7 dmg, cd 70) | CLAW BOOMERANG | ult CRAB CRUSH. Not yet posted.
(INK, CAMO BLINK, BUBBLES, BURROW are coded in sim4/render4 but not used; A1/B1 tuples pick skill 1.)

## Shovel vs Axe (sim5/render5/audio5) — objects, only skill 1 + ultimate (user asked to drop skill 2)
Seed 58, 39 s, Axe wins on 4 HP. Win split 48/52.
Shovel: DIG [stands still digging (vulnerable), red zone marks where the axe is heading, then teleports up into the zone: AoE 10] | ult BURY [dirt clod; hit = axe rooted + silenced 2 s + 4 dmg / 10 f].
Axe: WHIRLWIND [spinning damage aura 5 / 6 f] | ult TIMBER [4 trees sprout all over (2 near the shovel), each falls along its own telegraphed line, 18 dmg each].
Effects that can spill outside the arena are clipped with put(lay,ov) in render5. Not yet posted.

## RULE: every animal has UNIQUE moves (user, 2026-11-28)
No two animals may share a move or a move mechanic. Before designing a new animal, check this registry and add the new moves to it.
Each animal has exactly 3 fixed skills (skill 1, skill 2, ultimate). Do NOT rotate skill 1 (user clarified: they wanted a different skill 1, not a rotating one).
Registry (mechanic in brackets):
- Hedgehog: SPIKE BURST [radial ring of projectiles], ROLL [speed dash, contact dmg]
- Snake: VENOM [aimed orbs + poison DoT], SHED SKIN [self heal]
- Turtle: SHELL [full invulnerability window], BITE [aimed lunge, contact dmg], TIDAL WAVE ult [expanding ring, clears zones]
- Skunk: SPRAY [cone of droplets], STINK CLOUD [lingering damage zone], TOXIC BOMB ult [thrown bomb, AoE + zone]
- Octopus: INK MINE [proximity trap + slow], TENTACLE WHIP [instant melee lash + pull], KRAKEN ult [telegraphed eruptions at predicted spot]
- Crab: PEARL [ricochet projectile], CLAW BOOMERANG [out-and-back projectile, 2 hits], CRAB CRUSH ult [leap, untargetable, landing shockwave]
- Shovel: DIG [telegraphed zone + teleport strike], BURY ult [root + silence + DoT]
- Axe: WHIRLWIND [damage aura], TIMBER ult [multiple telegraphed line strikes from sprouting trees]
Already-used mechanics to avoid for new animals: dash/lunge, invulnerability, self heal, cone, lingering zone, ring wave, ricochet, trap, pull, out-and-back, telegraphed eruption, leap, zone-teleport strike, root/silence, aura, line strike.
Spare ideas already coded but unused (free to give to a new animal): aimed blobs + slow (INK), homing bubbles, burrow pop-up (BURROW).

## Publishing
Buffer org "My organization"; YouTube channels: Pixel Life (Animal Fight goes here), Pocket City, Some Crazy Thingzz. Pixel Life hit the daily posting limit on 2026-11-28; Hedgehog vs Snake post 6b0a8fd6cf6d91773010c5ba is in error state waiting for a reschedule decision. Two Pixel Life logo drafts (pixel arena mark / PIXEL LIFE text) were proposed; user has not chosen.

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
