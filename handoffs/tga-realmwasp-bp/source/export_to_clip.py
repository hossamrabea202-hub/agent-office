# Turn a full-asset Blueprint export (Unreal's exporter) into the clipboard format of one graph (what Ctrl+A, Ctrl+C
# in that graph gives), so tools/applyall can merge against it.   python export_to_clip.py FULL.t3d GRAPH OUT.t3d
import re, sys
src = open(sys.argv[1], encoding='utf-8', errors='replace').read(); graph = sys.argv[2]
bp = re.search(r"ExportPath=\"/Script/Engine\.Blueprint'([^']+)'\"", src).group(1)
out = []
for name, mod, cls, body in re.findall(r'Begin Object Name="([^"]+)" ExportPath="/Script/(\w+)\.(\w+)\'[^"]*:%s\.[^"\']*\'"\n(.*?)\n\s*End Object' % re.escape(graph), src, re.S):
    if 'NodeGuid=' not in body: continue
    out.append('Begin Object Class=/Script/%s.%s Name="%s" ExportPath="/Script/%s.%s\'%s:%s.%s\'"' % (mod, cls, name, mod, cls, bp, graph, name))
    out += ['   ' + l.strip() for l in body.split('\n') if l.strip()]
    out.append('End Object')
open(sys.argv[3], 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('nodes', sum(1 for l in out if l.startswith('Begin Object')))
