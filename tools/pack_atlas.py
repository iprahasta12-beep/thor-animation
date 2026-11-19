"""Pack images/ into a Spine atlas (straight alpha, no rotation).
Usage: python3 pack_atlas.py SKELETON.json IMAGES_DIR OUT_DIR NAME [max_page=2048]"""
import sys, os, json
from PIL import Image
SK, IMG, OUT, NAME = sys.argv[1:5]; MAXP = int(sys.argv[5]) if len(sys.argv) > 5 else 2048; PAD = 2
J = json.load(open(SK)); paths = set()
for slots in J["skins"][0]["attachments"].values():
    for an, a in slots.items():
        p = a.get("path", an); seq = a.get("sequence")
        if seq:
            for i in range(seq.get("start", 1), seq.get("start", 1) + seq["count"]): paths.add(f'{p}{i:0{seq.get("digits", 2)}d}')
        elif a.get("type", "region") in ("region", "mesh", "linkedmesh"): paths.add(p)
ims = []
for p in paths:
    f = os.path.join(IMG, p + ".png")
    if not os.path.exists(f): print("MISSING", f); continue
    ims.append((p, Image.open(f).convert("RGBA")))
ims.sort(key=lambda x: (-x[1].height, -x[1].width))
pages = []  # each: [placements, shelves]
def place(im):
    w, h = im.width + PAD, im.height + PAD
    for pg in pages:
        for sh in pg["shelves"]:  # shelf: [y, height, x_used]
            if h <= sh[1] and sh[2] + w <= MAXP: pos = (sh[2], sh[0]); sh[2] += w; return pg, pos
        y = sum(s[1] for s in pg["shelves"])
        if y + h <= MAXP: pg["shelves"].append([y, h, w]); return pg, (0, y)
    pg = {"items": [], "shelves": [[0, h, w]]}; pages.append(pg); return pg, (0, 0)
for p, im in ims:
    if im.width > MAXP or im.height > MAXP: sys.exit(f"{p} bigger than page {MAXP}")
    pg, pos = place(im); pg["items"].append((p, im, pos))
os.makedirs(OUT, exist_ok=True); lines = []
for i, pg in enumerate(pages):
    W = max(x + im.width for _, im, (x, y) in pg["items"]); H = max(y + im.height for _, im, (x, y) in pg["items"])
    W = 1 << (W - 1).bit_length(); H = 1 << (H - 1).bit_length()
    sheet = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fn = f"{NAME}{'' if i == 0 else i + 1}.png"
    for p, im, pos in pg["items"]: sheet.paste(im, pos)
    sheet.save(os.path.join(OUT, fn), optimize=True)
    lines += [fn, f"size:{W},{H}", "filter:Linear,Linear"]
    for p, im, (x, y) in pg["items"]: lines += [p, f"bounds:{x},{y},{im.width},{im.height}"]
    lines.append("")
open(os.path.join(OUT, NAME + ".atlas"), "w").write("\n".join(lines))
print(f"{len(ims)} regions on {len(pages)} page(s)")
