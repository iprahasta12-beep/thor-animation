"""Bake a Spine export into preview/data.js (works from file://, no server).
Usage: python3 bake_preview.py EXPORT_DIR NAME PREVIEW_DIR [bg_landscape.png] [bg_portrait.png]
EXPORT_DIR holds NAME.json (or NAME.skel), NAME.atlas and the atlas page PNGs."""
import sys, os, json, base64
EXP, NAME, PREV = sys.argv[1:4]; bgs = sys.argv[4:6]
def uri(p):
    ext = os.path.splitext(p)[1].lower().strip('.'); mt = 'jpeg' if ext in ('jpg', 'jpeg') else ext
    return f"data:image/{mt};base64," + base64.b64encode(open(p, 'rb').read()).decode()
atlas = open(os.path.join(EXP, NAME + '.atlas')).read()
pages = {}; lines = atlas.splitlines()
for i, l in enumerate(lines):
    if l.strip().lower().endswith(('.png', '.webp', '.jpg')) and (i == 0 or not lines[i - 1].strip()):
        pages[l.strip()] = uri(os.path.join(EXP, l.strip()))
D = {"name": NAME, "atlas": atlas, "pages": pages}
js = os.path.join(EXP, NAME + '.json')
if os.path.exists(js): D["json"] = json.load(open(js))
else: D["skelB64"] = base64.b64encode(open(os.path.join(EXP, NAME + '.skel'), 'rb').read()).decode()
out = "window.SPINE_DATA = " + json.dumps(D, separators=(',', ':')) + ";\n"
if bgs:
    out += "window.BG_DATA = " + json.dumps({k: uri(p) for k, p in zip(('landscape', 'portrait'), bgs) if p}) + ";\n"
open(os.path.join(PREV, 'data.js'), 'w').write(out)
print('data.js', round(len(out) / 1e6, 1), 'MB', list(pages))
