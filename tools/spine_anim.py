"""Stage 3: add animations to a Spine skeleton JSON, validate them, render a GIF preview.
Usage: python3 spine_anim.py SKELETON.json IMAGES_DIR anims.py OUT_DIR
anims.py defines ANIMS (and optional EVENTS, STATIC, LIMITS). See SKILL.md for the spec format.
"""
import sys, json, math, copy, os, importlib.util as U
import numpy as np, cv2
from PIL import Image

# ---------------- build ----------------
EASES = {"inout": (0.4, 0.0, 0.6, 1.0), "in": (0.5, 0.0, 1.0, 1.0), "out": (0.0, 0.0, 0.5, 1.0)}

def _curve(k0, k1, chans, ease):
    """Spine 4.x bezier: per channel [cx1, cy1, cx2, cy2] in absolute time/value."""
    if ease == "linear": return None
    if ease == "stepped": return "stepped"
    a, b, c, d = EASES[ease]
    t0, t1 = k0[0], k1[0]; out = []
    for i in range(chans):
        v0, v1 = k0[1 + i], k1[1 + i]
        out += [round(t0 + (t1 - t0) * a, 4), round(v0 + (v1 - v0) * b, 4),
                round(t0 + (t1 - t0) * c, 4), round(v0 + (v1 - v0) * d, 4)]
    return out

def _keys(keys, names, ease):
    out = []
    for i, k in enumerate(keys):
        k = list(k); e = k.pop() if isinstance(k[-1], str) else ease  # optional per-key ease
        keys[i] = tuple(k) + (e,)
    for i, k in enumerate(keys):
        e = {"time": round(k[0], 4)} if k[0] else {}
        for n, v in zip(names, k[1:1 + len(names)]): e[n] = round(v, 4)
        if i + 1 < len(keys):
            c = _curve(k[:1 + len(names)], keys[i + 1][:1 + len(names)], len(names), k[-1])
            if c is not None: e["curve"] = c
        out.append(e)
    return out

def build(J, ANIMS, EVENTS=()):
    J = copy.deepcopy(J); J["animations"] = {}
    if EVENTS: J["events"] = {e: {} for e in EVENTS}
    for name, A in ANIMS.items():
        ease = A.get("ease", "inout"); out = {}
        if A.get("bones"):
            out["bones"] = {}
            for b, tl in A["bones"].items():
                o = {}
                for kind, keys in tl.items():
                    names = {"rotate": ["value"], "translate": ["x", "y"], "scale": ["x", "y"],
                             "translatex": ["value"], "translatey": ["value"], "scalex": ["value"], "scaley": ["value"]}[kind]
                    o[kind] = _keys(list(keys), names, ease)
                out["bones"][b] = o
        if A.get("slots"):
            out["slots"] = {}
            for s, tl in A["slots"].items():
                o = {}
                if "alpha" in tl:  # (time, alpha) -> rgba keys on white
                    base = tl.get("color", "ffffff")
                    ks = _keys([(k[0], k[1]) + tuple(k[2:]) for k in tl["alpha"]], ["a"], ease)
                    for k in ks:
                        a = k.pop("a"); k["color"] = base + "%02x" % int(round(max(0, min(1, a)) * 255))
                        if isinstance(k.get("curve"), list):  # rgba needs 4 channels: r,g,b stay flat
                            c = k["curve"]; t1, t2 = c[0], c[2]
                            k["curve"] = sum([[t1, 1, t2, 1]] * 3, []) + c
                    o["rgba"] = ks
                if "attachment" in tl:
                    o["attachment"] = [dict(({"time": t} if t else {}), name=n) for t, n in tl["attachment"]]
                out["slots"][s] = o
        if A.get("sequences"):  # {slot: {attachment: [(time, mode, index, delay)]}}
            skin = {}
            for s, d in A["sequences"].items():
                skin[s] = {a: {"sequence": [dict(({"time": t} if t else {}), mode=m, index=i, delay=dl) for t, m, i, dl in ks]}
                           for a, ks in d.items()}
            out["attachments"] = {"default": skin}
        if A.get("physics"):  # {constraint_name: {prop: [(time, value)]}}
            out["physics"] = {c: {p: _keys(list(ks), ["value"], ease) for p, ks in d.items()} for c, d in A["physics"].items()}
        if A.get("events"):
            out["events"] = [dict(({"time": round(t, 4)} if t else {}), name=n) for t, n in A["events"]]
        J["animations"][name] = out
    return J

def wave(amp, period, dur, phase=0.0, steps=12):
    """Looping sine as keys: (time, value, 'linear') every period/steps, plus 0 and dur. period must divide dur.
    Dense linear keys = smooth, even motion (no ease stalls at the zero crossings)."""
    n = int(round(dur / period * steps)); out = []
    for i in range(n + 1):
        t = round(dur * i / n, 4); v = round(amp * math.sin(2 * math.pi * (t - phase) / period), 3)
        out.append((t, v, "linear"))
    out[-1] = (out[-1][0], out[0][1], "linear")  # exact loop
    return out

# ---------------- validate ----------------
def validate(J, ANIMS, STATIC=(), LIMITS=None):
    LIMITS = LIMITS or {}; errs = []
    bones = {b["name"] for b in J["bones"]}; slots = {s["name"] for s in J["slots"]}
    cons = {c["name"] for c in J.get("constraints", [])} | {c["name"] for c in J.get("physics", [])}
    for name, A in ANIMS.items():
        dur = A["duration"]
        for b, tl in A.get("bones", {}).items():
            if b not in bones: errs.append(f"{name}: bone '{b}' not in skeleton")
            if b in STATIC: errs.append(f"{name}: bone '{b}' is static (scope) but keyed")
            for kind, ks in tl.items():
                ts = [k[0] for k in ks]
                if ts != sorted(ts) or ts[-1] > dur + 1e-6 or ts[0] < 0: errs.append(f"{name}/{b}/{kind}: times out of order or range")
                if A.get("loop") and (ts[0] != 0 or abs(ts[-1] - dur) > 1e-6 or
                                      [v for v in ks[0][1:] if not isinstance(v, str)] != [v for v in ks[-1][1:] if not isinstance(v, str)]):
                    errs.append(f"{name}/{b}/{kind}: loop must start at 0 and end at duration with the same value")
                if kind == "rotate" and b in LIMITS:
                    mx = max(abs(k[1]) for k in ks)
                    if mx > LIMITS[b]: errs.append(f"{name}/{b}: rotate {mx}° over limit {LIMITS[b]}°")
        for s in list(A.get("slots", {})) + list(A.get("sequences", {})):
            if s not in slots: errs.append(f"{name}: slot '{s}' not in skeleton")
        for c in A.get("physics", {}):
            if c not in cons: errs.append(f"{name}: physics constraint '{c}' not in skeleton")
        for t, e in A.get("events", []):
            if t > dur: errs.append(f"{name}: event {e} after end")
    return errs

# ---------------- preview (FK only: no IK, no physics) ----------------
def _bez(c, t0, t1, v0, v1, t, ch=0):
    if c is None: return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    if c == "stepped": return v0
    cx1, cy1, cx2, cy2 = c[ch * 4:ch * 4 + 4]
    s = np.linspace(0, 1, 200)
    X = (1-s)**3*t0 + 3*(1-s)**2*s*cx1 + 3*(1-s)*s**2*cx2 + s**3*t1
    Y = (1-s)**3*v0 + 3*(1-s)**2*s*cy1 + 3*(1-s)*s**2*cy2 + s**3*v1
    return float(np.interp(t, X, Y))

def _sample(keys, fields, t, default):
    if not keys: return default
    ts = [k.get("time", 0) for k in keys]
    if t <= ts[0]: return [keys[0].get(f, d) for f, d in zip(fields, default)]
    if t >= ts[-1]: return [keys[-1].get(f, d) for f, d in zip(fields, default)]
    i = max(j for j in range(len(ts)) if ts[j] <= t); k0, k1 = keys[i], keys[i + 1]
    return [_bez(k0.get("curve"), ts[i], ts[i+1], k0.get(f, d), k1.get(f, d), t, ch) for ch, (f, d) in enumerate(zip(fields, default))]

def pose(J, anim, t):
    A = J["animations"].get(anim, {}).get("bones", {}); W = {}
    for b in J["bones"]:
        tl = A.get(b["name"], {})
        r = b.get("rotation", 0) + _sample(tl.get("rotate"), ["value"], t, [0])[0]
        tx, ty = _sample(tl.get("translate"), ["x", "y"], t, [0, 0])
        sx, sy = _sample(tl.get("scale"), ["x", "y"], t, [1, 1])
        x, y = b.get("x", 0) + tx, b.get("y", 0) + ty
        sx *= b.get("scaleX", 1); sy *= b.get("scaleY", 1)
        c, s = math.cos(math.radians(r)), math.sin(math.radians(r))
        L = np.array([[c * sx, -s * sy, x], [s * sx, c * sy, y], [0, 0, 1]])
        W[b["name"]] = (W[b["parent"]] @ L) if "parent" in b else L
    return W

def render(J, images, anim, t, scale=0.5, pad=40):
    W = pose(J, anim, t); sk = J["skeleton"]; names = [b["name"] for b in J["bones"]]
    ox, oy = -sk.get("x", 0), sk.get("y", 0) + sk.get("height", 1000)
    w, h = int(sk.get("width", 1000) * scale) + 2 * pad, int(sk.get("height", 1000) * scale) + 2 * pad
    can = np.zeros((h, w, 4), np.float32); can[..., :3] = 0.16
    toC = lambda p: ((p[0] + ox) * scale + pad, (oy - p[1]) * scale + pad)
    skin = J["skins"][0]["attachments"]
    slotA = J["animations"].get(anim, {}).get("slots", {})
    for s in J["slots"]:
        an = s.get("attachment"); alpha = 1.0
        st = slotA.get(s["name"], {})
        if "attachment" in st:
            for k in st["attachment"]:
                if k.get("time", 0) <= t: an = k["name"]
        if "rgba" in st:
            a = _sample([dict(k, a=int(k["color"][6:8], 16) / 255) for k in st["rgba"]], ["a"], t, [1])[0]; alpha = a
        if not an or an not in skin.get(s["name"], {}): continue
        a = skin[s["name"]][an]; p = a.get("path", an)
        fn = os.path.join(images, p + ".png")
        if not os.path.exists(fn): continue
        img = cv2.imread(fn, cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
        if img.shape[2] == 3: img = np.dstack([img, np.ones(img.shape[:2])])
        img = img[..., [2, 1, 0, 3]]; ih, iw = img.shape[:2]
        if a.get("type") == "mesh":
            v = a["vertices"]; uv = np.array(a["uvs"]).reshape(-1, 2) * [iw, ih]; P = []
            if len(v) == len(uv) * 2:  # unweighted
                M = W[s["bone"]]; P = [toC(M @ [v[2*i], v[2*i+1], 1]) for i in range(len(uv))]
            else:
                i = 0
                while i < len(v):
                    n = int(v[i]); i += 1; q = np.zeros(2)
                    for _ in range(n):
                        bi, x, y, wt = v[i:i+4]; i += 4; q += wt * (W[names[int(bi)]] @ [x, y, 1])[:2]
                    P.append(toC(q))
            P = np.array(P, np.float32); tr = np.array(a["triangles"]).reshape(-1, 3)
            for t3 in tr:
                src = uv[t3].astype(np.float32); dst = P[t3]
                x0, y0 = np.floor(dst.min(0)).astype(int); x1, y1 = np.ceil(dst.max(0)).astype(int) + 1
                x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, w), min(y1, h)
                if x1 <= x0 or y1 <= y0: continue
                Mx = cv2.getAffineTransform(src, (dst - [x0, y0]).astype(np.float32))
                patch = cv2.warpAffine(img, Mx, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
                m = np.zeros((y1 - y0, x1 - x0), np.float32); cv2.fillConvexPoly(m, np.round(dst - [x0, y0]).astype(np.int32), 1)
                pa = patch[..., 3] * m * alpha; reg = can[y0:y1, x0:x1]
                reg[..., :3] = reg[..., :3] * (1 - pa[..., None]) + patch[..., :3] * pa[..., None]
        else:
            M = W[s["bone"]]; r = math.radians(a.get("rotation", 0)); c, sn = math.cos(r), math.sin(r)
            sx, sy = a.get("scaleX", 1), a.get("scaleY", 1); aw, ah = a["width"], a["height"]
            def corner(u, vv):  # u,v in image px (y down) -> canvas
                lx, ly = (u - iw / 2) * aw / iw * sx, (ih / 2 - vv) * ah / ih * sy
                px, py = a.get("x", 0) + lx * c - ly * sn, a.get("y", 0) + lx * sn + ly * c
                return toC(M @ [px, py, 1])
            src = np.float32([[0, 0], [iw, 0], [0, ih]]); dst = np.float32([corner(0, 0), corner(iw, 0), corner(0, ih)])
            q = np.array([corner(0, 0), corner(iw, 0), corner(0, ih), corner(iw, ih)])
            x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int) + 1, [w, h])
            if x1 <= x0 or y1 <= y0: continue
            patch = cv2.warpAffine(img, cv2.getAffineTransform(src, (dst - [x0, y0]).astype(np.float32)), (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR)
            add = s.get("blend") == "additive"; pa = patch[..., 3:4] * alpha; reg = can[y0:y1, x0:x1]
            reg[..., :3] = reg[..., :3] + patch[..., :3] * pa if add else reg[..., :3] * (1 - pa) + patch[..., :3] * pa
    return Image.fromarray((np.clip(can[..., :3], 0, 1) * 255).astype(np.uint8))

def gif(J, images, anim, dur, out, fps=15, scale=0.5):
    fr = [render(J, images, anim, i / fps, scale) for i in range(int(round(dur * fps)) + (0 if dur else 1))]
    fr[0].save(out, save_all=True, append_images=fr[1:], duration=int(1000 / fps), loop=0)
    return len(fr)

if __name__ == "__main__":
    SK, IMG, SPEC, OUT = sys.argv[1:5]
    sp = U.spec_from_file_location("a", SPEC); D = U.module_from_spec(sp); sp.loader.exec_module(D)
    J = json.load(open(SK))
    errs = validate(J, D.ANIMS, getattr(D, "STATIC", ()), getattr(D, "LIMITS", None))
    for e in errs: print("ERROR", e)
    if errs: sys.exit(1)
    J2 = build(J, D.ANIMS, getattr(D, "EVENTS", ()))
    os.makedirs(OUT, exist_ok=True); json.dump(J2, open(os.path.join(OUT, os.path.basename(SK)), "w"), indent=1)
    if "--no-gif" in sys.argv: sys.exit(0)
    for name, A in D.ANIMS.items():
        n = gif(J2, IMG, name, A["duration"], os.path.join(OUT, name + ".gif"), scale=getattr(D, "PREVIEW_SCALE", 0.4))
        print(f"{name}: {A['duration']}s, {n} preview frames")
