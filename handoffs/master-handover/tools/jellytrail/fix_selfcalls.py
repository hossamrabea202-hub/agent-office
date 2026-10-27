"""fix_selfcalls.py: BP_JellyTrailManager lost all 10 calls to its own custom events on paste (MemberParent=own class
CallFunction nodes are dropped). Rebuild = live EventGraph (stale export nodes removed) + the 10 calls from
paste_trailmanager_2_graph.t3d as FunctionReference=(MemberName=X,bSelfContext=True), relinked by pin name.
Writes paste_trailmanager_fixed.t3d (full EventGraph replace)."""
import os, re, sys
W = r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027'
sys.path.insert(0, W)
import kit2 as K
import t3dlib as T
from kit2 import G, BPC
MGR = BPC('/Game/CastleDefender/Gameplay/JellyTrail/BP_JellyTrailManager')
EXP = 'live_BP_JellyTrailManager'

raw = open(os.path.join(W, 't3d', EXP + '.t3d'), 'rb').read()
t = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('utf-8', 'ignore')
live = set(re.findall(r"Nodes\(\d+\)=\"[^']*'([^']+)'\"", t))

g = G(MGR)
N = g.load_graph(EXP, 'EventGraph')
stale = {n for n in N if n not in live}
g.nodes = [n for n in g.nodes if n.name not in stale]
for n in g.nodes:
    for p in n.pins:
        p.links = [l for l in p.links if l[0] not in stale]
N = {n.name: n for n in g.nodes}

pt = open(os.path.join(W, 'jellytrail', 'paste_trailmanager_2_graph.t3d'), encoding='utf-8', errors='ignore').read()
pnodes = {nm: (c, b) for c, nm, b in re.findall(r'Begin Object Class=(\S+) Name="([^"]+)"\n(.*?)\nEnd Object', pt, re.S)}
pin_by_id = {}
for nm, (c, b) in pnodes.items():
    for line in re.findall(r'CustomProperties Pin \((.*)\)', b):
        pin_by_id[re.search(r'PinId=([0-9A-F]+)', line).group(1)] = (nm, re.search(r'PinName="([^"]+)"', line).group(1))

missing = [nm for nm, (c, b) in pnodes.items() if nm not in live]
added = {}
for nm in missing:
    c, b = pnodes[nm]
    pos = re.search(r'NodePosX=(-?\d+).*?NodePosY=(-?\d+)', b, re.S)
    node = g.add(c, b, nm, int(pos.group(1)), int(pos.group(2)))
    node.props = [re.sub(r'FunctionReference=\([^)]*MemberName="([^"]+)"[^)]*\)', r'FunctionReference=(MemberName="\1",bSelfContext=True)', s) for s in node.props]
    added[nm] = node
for nm, node in added.items():
    for p in node.pins:
        for tn, tid in p.old_links:
            tnode, tpin = pin_by_id[tid]
            other = added.get(tnode) or N.get(tnode)
            if other is None:
                print('!! %s.%s -> %s not live' % (nm, p.name, tnode)); continue
            q = other.p(tpin)
            if any(l[0] == nm for l in q.links): continue
            p.links.append((other.name, q.id)); q.links.append((nm, p.id))
    print(nm, [s for s in node.props if 'FunctionReference' in s][0], [(p.name, [l[0] for l in p.links]) for p in node.pins if p.links])
n, size = g.emit(os.path.join(W, 'jellytrail', 'paste_trailmanager_fixed.t3d'))
print('nodes', n, 'chars', size, 'stale dropped', len(stale))
