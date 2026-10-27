"""checklive.py <live.t3d>: orphaned pins on live (non-deleted) nodes, and the Array_RemoveItem Item default."""
import re, sys
raw = open(sys.argv[1], 'rb').read()
t = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('utf-8', 'ignore')
body = {}
for m in re.finditer(r'Begin Object (?:Class=\S+ )?Name="([^"]+)"(.*?)\n\s*End Object', t, re.S):
    body[m.group(1)] = body.get(m.group(1), '') + m.group(2)
for n, b in body.items():
    for p in re.findall(r'CustomProperties Pin \((.*)\)', b):
        pn = re.search(r'PinName="([^"]+)"', p).group(1)
        if 'bOrphanedPin=True' in p: print('ORPHAN', n, pn)
        if 'Array_RemoveItem' in b and pn == 'Item':
            d = re.search(r'DefaultValue="([^"]*)"', p); print('RemoveItem', n, 'Item =', d.group(1) if d else None, re.search(r'PinCategory="([^"]*)"', p).group(1))
