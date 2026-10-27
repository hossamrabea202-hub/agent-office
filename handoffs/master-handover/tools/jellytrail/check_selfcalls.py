import re, sys
p = sys.argv[1] if len(sys.argv) > 1 else r'C:\Unreal Backups\Castle Defender\Tools\PasteRegen_1027\t3d\after_BP_JellyTrailManager.t3d'
raw = open(p, 'rb').read()
t = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('utf-8', 'ignore')
live = set(re.findall(r"Nodes\(\d+\)=\"[^']*'([^']+)'\"", t))
body = {}
for m in re.finditer(r'Begin Object (?:Class=\S+ )?Name="([^"]+)"(.*?)\n\s*End Object', t, re.S):
    body[m.group(1)] = body.get(m.group(1), '') + m.group(2)
print('live', len(live))
for n in ('JT_36', 'JT_48', 'JT_55', 'JT_76', 'JT_178', 'JT_221', 'JT_225', 'JT_231', 'JT_240', 'JT_296'):
    b = body.get(n, '')
    ex = [re.search(r'PinName="([^"]+)"', q).group(1) for q in re.findall(r'CustomProperties Pin \((.*)\)', b) if 'LinkedTo=' in q]
    fr = re.search(r'FunctionReference=\(([^)]*)\)', b)
    print(n, n in live, fr.group(1) if fr else None, ex)
orph = [(n, re.search(r'PinName="([^"]+)"', q).group(1)) for n in live for q in re.findall(r'CustomProperties Pin \((.*)\)', body.get(n, '')) if 'bOrphanedPin=True' in q]
print('orphans', orph)
