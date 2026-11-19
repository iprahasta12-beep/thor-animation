"""v5: blink linked mesh (kept as an asset) + hammer energy dome (GIF, 22 fr) + eye bursts (sprite sheet, 8 fr). Old FX removed."""
import json, math, shutil, pickle
J = json.load(open('/home/claude/out/thor.json')); RX, RY = 735, 1730
def Y(x, y): return (x - RX, RY - y)
W = {}
for b in J['bones']:
    r = b.get('rotation', 0); x, y = b.get('x', 0), b.get('y', 0)
    if 'parent' in b:
        px, py, pr = W[b['parent']]; a = math.radians(pr)
        x, y = px + x * math.cos(a) - y * math.sin(a), py + x * math.sin(a) + y * math.cos(a); r += pr
    W[b['name']] = (x, y, r)
def add_bone(name, parent, cx, cy, world_angle=0.0):
    px, py, pr = W[parent]; wx, wy = Y(cx, cy); a = math.radians(-pr); dx, dy = wx - px, wy - py
    J['bones'].append({'name': name, 'parent': parent, 'x': round(dx * math.cos(a) - dy * math.sin(a), 2),
                       'y': round(dx * math.sin(a) + dy * math.cos(a), 2), 'rotation': round(world_angle - pr, 2), 'length': 40, 'color': 'c878ffff'})
    W[name] = (wx, wy, world_angle)
skin = J['skins'][0]['attachments']
def add_slot(name, bone, after=None):
    names = [x['name'] for x in J['slots']]; i = names.index(after) + 1 if after else len(names)
    J['slots'].insert(i, {'name': name, 'bone': bone, 'blend': 'additive'}); skin[name] = {}
# blink asset (no animation uses it now)
shutil.copy('/home/claude/newart/13_head_blink.png', '/home/claude/out/images/13_head_blink.png')
h = skin['head']['13_head']
skin['head']['13_head_blink'] = {'type': 'linkedmesh', 'source': '13_head', 'width': h['width'], 'height': h['height'], 'timelines': True}
# hammer dome: base of the dome on the hammer head centre; image 311x328, dome base at (187,305) px in the image
S = 2.0; IW, IH = 311, 328; BX, BY = 187, 305
add_bone('fx_dome', 'hammer', 760, 845)            # pivot = hammer head emblem (rune)
add_slot('fx_hammer', 'fx_dome', after='bracer_l')
skin['fx_hammer']['dome'] = {'path': 'fx2/hammer_', 'sequence': {'count': 22, 'start': 1, 'digits': 2},
    'x': round((IW / 2 - BX) * S, 1), 'y': round((BY - IH / 2) * S, 1), 'scaleX': S, 'scaleY': S, 'width': IW, 'height': IH}
# eyes: burst centred on each eye (head layer px -> canvas)
M = pickle.load(open('/home/claude/meshes.pkl', 'rb'))['head']; L, T = M['L'], M['T']
for name, (ex, ey), sc in (('fx_eye_l', (113, 64), 0.913), ('fx_eye_r', (172, 62), 0.70)):   # frames stored at 336 px
    add_bone(name + '_b', 'head', L + ex, T + ey)
    add_slot(name, name + '_b')
    skin[name]['burst'] = {'path': 'fx2/eyeg_', 'sequence': {'count': 20, 'start': 1, 'digits': 2}, 'scaleX': sc, 'scaleY': sc, 'width': 336, 'height': 336}
names=[b['name'] for b in J['bones']]; assert len(names)==len(set(names)), 'duplicate bone'
json.dump(J, open('/home/claude/out/thor.json', 'w'), indent=1)
print(len(J['bones']), 'bones', len(J['slots']), 'slots')
