# thor-animation · Spine 4.3 + PixiJS preview

| folder | what |
|---|---|
| `spine/` | **Spine source.** `thor.json` (4.3.26) + `images/`. Spine 4.3 → Import Data → `spine/thor.json`, images folder `spine/images/` → Save As `thor.spine`. After that the Spine project is the master. |
| `export/` | **Game files.** `thor.json` + `thor.atlas` + `thor.png` / `thor2.png` (straight alpha). For spine-pixi-v8 / spine-unity **4.3** runtime. |
| `preview/` | **Offline preview.** Double-click `preview/index.html`. Runtime: spine-pixi-v8 4.3.13 + Pixi v8 (in `lib/`). |
| `tools/` | `spine_anim.py` (keys + validate), `thor_anims.py` (key spec), `add_fx2.py` (FX bones/slots + blink mesh), `pack_atlas.py`, `bake_preview.py`. |
| `fx_source/` | Your hammer GIF and eye GIF, as delivered. |

## Preview
- Left panel = animation controller: Pause/Play (Space), Restart, Loop, → idle after, scrub, Speed, Mix,
  Character (size / X / Y / Flip / Reset / Copy JSON), filter (All · Ready · To do · P1–P3), animation list, detail.
- Click a body animation (track 0) to play. FX rows (track 1/2) toggle on/off over the body. Grey = to do (not in the file yet).
- Stage: Landscape 1920×1080 / Portrait 1080×1920. Drag the character to move, mouse wheel = size (feet stay put). The character always stays inside the canvas (size and position are clamped). Switching layout keeps the view; no Fit button.
  Placement is remembered in the browser. Copy JSON = feet x/y + scale for the game.
- Background: blank canvas by default. **Load BG…** (or drop an image) = background for the current layout. Clear BG = blank again.
- **Load export…** (or drop .json + .atlas + .png) = see a new Spine export without rebaking.
- Real runtime: IK and physics run here (unlike the GIFs).

## After editing in Spine
Export JSON + atlas (name `thor`) into `export/`, then:
```
python3 tools/bake_preview.py export thor preview [bg_landscape.png] [bg_portrait.png]
```

## Animations (v6)
| name | track | loop | length | what | made by |
|---|---|---|---|---|---|
| idle_breath | 0 | yes | 4.00s | breath, cape flag wave, free arm, blink @2.6s | keys (`tools/thor_anims.py`) |
| idle_look | 0 | yes | 4.00s | look up, cape, free arm, blinks @0.6s + 3.5s | keys |
| idle_grip | 0 | yes | 4.00s | hammer heft, cape, free arm, blink @3.0s, event `sfx_grip` @0.5s | keys |
| fx_hammer | 1 | yes | 1.10s | energy dome + rising arcs, **pivot on the hammer head emblem** | your hammer GIF (`fx_source/hammer_fx.gif`), 22 fr @ 20 fps → sequence `fx2/hammer_01..22` |
| fx_eyes | 2 | yes | 2.40s | eye burst (bolt → star → smoke + sparks) on both eyes, far eye 0.04 s later and smaller, then rest | your eye GIF (`fx_source/eye_fx.gif`), one cycle = 20 fr @ 25 fps → sequence `fx2/eyeg_01..20` |

FX tracks never key a body bone. Play an idle on track 0 and the FX loops on tracks 1 and 2 on top.

FX frame prep: hammer GIF on black → brightness = alpha. Eye GIF has a dark vignette background → removed with a
median background plate and an "unscreen" ((frame − bg) / (1 − bg)) so the white core stays white; one burst cycle
(GIF frames 28–47) centred on the burst, stored at 336 px (shown at 0.91 / 0.70 scale).

## Art
- **Cape:** your latest painting (registered, re-meshed, 3 chains × 4 bones, hem free).
- **Blink:** `13_head_blink` linked mesh of `13_head`, used by the idles.
