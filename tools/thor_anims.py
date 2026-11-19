# v6: idles back (track 0) + FX loops from your art (hammer GIF on track 1, eye GIF on track 2).
from spine_anim import wave
EVENTS = ["sfx_grip"]
LIMITS = {"spine": 1.5, "head": 4}
D = 4.0; P = D / 2
def breath(d): return {"chest": {"scale": [(0, 1, 1), (d * 0.43, 1.015, 1), (d, 1, 1)], "translate": [(0, 0, 0), (d * 0.43, 1.5, 0), (d, 0, 0)]},
                       "spine": {"rotate": [(0, 0), (d * 0.43, -0.6), (d, 0)]}}
def cape(k=1.0):   # flag wave: down each chain (0.2 s, x1.28 per bone) and across the cape
    out = {}
    for chain, base, off in (("o", 2.0, 0.0), ("m", 2.4, 0.05), ("i", 1.9, 0.25)):
        for seg in range(1, 5):
            out[f"cape_{chain}{seg}"] = {"rotate": wave(round(base * k * 1.28 ** (seg - 1), 3), P, D, 0.25 + off + 0.2 * (seg - 1))}
    return out
def free_arm(k=1.0, ph=0.0):
    return {"shoulder_r": {"rotate": wave(0.7 * k, D, D, 0.9 + ph)}, "forearm_r": {"rotate": wave(1.1 * k, D, D, 1.15 + ph)}, "hand_r": {"rotate": wave(1.6 * k, D, D, 1.4 + ph)}}
def blink(*times):
    ks = [(0, "13_head")]
    for t in times: ks += [(t, "13_head_blink"), (round(t + 0.1, 3), "13_head")]
    return {"head": {"attachment": ks}}
ANIMS = {
 "idle_breath": {"duration": D, "loop": True, "slots": blink(2.6), "bones": {**breath(D), **cape(), **free_arm(),
   "neck": {"rotate": [(0, 0), (1.85, 0.8), (D, 0)]}, "head": {"rotate": [(0, 0), (2.0, 0.8), (D, 0)]},
   "shoulder_l": {"rotate": [(0, 0), (1.7, -1.0), (3.0, 1.0), (D, 0)]}, "hammer": {"rotate": [(0, 0), (2.0, 0.6), (3.3, -0.8), (D, 0)]}}},
 "idle_look": {"duration": D, "loop": True, "slots": blink(0.6, 3.5), "bones": {**breath(D), **cape(), **free_arm(0.8, 0.3),
   "head": {"rotate": [(0, 0), (1.0, 3.5), (2.4, 3.5), (3.6, 0), (D, 0)]}, "neck": {"rotate": [(0, 0), (0.9, 1.4), (2.3, 1.4), (3.5, 0), (D, 0)]},
   "jaw": {"rotate": [(0, 0), (1.2, -1), (3.2, 0), (D, 0)]}}},
 "idle_grip": {"duration": D, "loop": True, "events": [(0.5, "sfx_grip")], "slots": blink(3.0), "bones": {**cape(1.1), **free_arm(1.2),
   "hand_l": {"scale": [(0, 1, 1), (0.5, 0.97, 0.97), (1.0, 1, 1), (D, 1, 1)]},
   "hammer": {"rotate": [(0, 0), (0.4, -1), (1.2, 6), (2.0, -1.5), (2.8, 0), (D, 0)]},
   "shoulder_l": {"rotate": [(0, 0), (0.4, 1.2), (1.2, -2), (2.0, 0.5), (2.8, 0), (D, 0)]},
   "chest": {"translate": [(0, 0, 0), (0.4, -2, 0), (1.0, 0, 0), (D, 0, 0)], "scale": [(0, 1, 1), (1.7, 1.012, 1), (D, 1, 1)]},
   "spine": {"rotate": [(0, 0), (0.4, 0.4), (1.2, -0.5), (2.4, 0), (D, 0)]}}},
 # FX loops: never key a body bone
 "fx_hammer": {"duration": 1.1, "loop": True,                         # your hammer GIF: 22 frames @ 20 fps, pivot on the emblem
   "slots": {"fx_hammer": {"attachment": [(0, "dome"), (1.1, "dome")]}},
   "sequences": {"fx_hammer": {"dome": [(0, "loop", 0, 0.05)]}}},
 "fx_eyes": {"duration": 2.4, "loop": True,                           # your eye GIF: one burst cycle, 20 frames @ 25 fps, then rest
   "slots": {"fx_eye_l": {"attachment": [(0, "burst"), (0.8, None)]},
             "fx_eye_r": {"attachment": [(0.04, "burst"), (0.84, None), (2.4, None)]}},
   "sequences": {"fx_eye_l": {"burst": [(0, "once", 0, 0.04)]}, "fx_eye_r": {"burst": [(0.04, "once", 0, 0.04)]}}},
}
