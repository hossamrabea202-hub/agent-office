# Turns a whole-asset Blueprint export (the T3D the Master's export scripts write, with nested EdGraph objects) into
# the clipboard form that tools/applyall expects (top-level node objects with Class + ExportPath), so hand-offs can be
# merge-validated without a fresh Ctrl+A/Ctrl+C export.   python graph_from_asset.py <asset.t3d> <out.t3d> [GraphName]
import re, sys
src_path, out_path = sys.argv[1], sys.argv[2]; graph = sys.argv[3] if len(sys.argv) > 3 else 'EventGraph'
src = open(src_path, encoding='utf-8', errors='replace').read().split('\n')
cls = {}
for l in src:
    m = re.match(r'\s*Begin Object Class=(/Script/BlueprintGraph\.\S+) Name="([^"]+)" ExportPath="[^"]*%s\.' % re.escape(graph), l)
    if m: cls[m.group(2)] = m.group(1)
out = []; i = 0; n = 0
while i < len(src):
    m = re.match(r'(\s*)Begin Object Name="([^"]+)" ExportPath="([^"]*%s\.[^"]*)"' % re.escape(graph), src[i])
    if m and m.group(2) in cls:
        ind, name = m.group(1), m.group(2); block = ['Begin Object Class=%s Name="%s" ExportPath="%s"' % (cls[name], name, m.group(3))]
        i += 1; depth = 1
        while i < len(src) and depth > 0:
            s = src[i].strip()
            if s.startswith('Begin Object'): depth += 1
            if s == 'End Object': depth -= 1
            block.append(src[i][len(ind):] if src[i].startswith(ind) else src[i]); i += 1
        out.extend(block); n += 1
    else: i += 1
open(out_path, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('%s: %d of %d %s nodes -> %s' % (src_path, n, len(cls), graph, out_path))
