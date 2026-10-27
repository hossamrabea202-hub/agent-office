"""nodediff.py <paste.t3d> <live.t3d>: which pasted nodes are missing from the live graph (by class + member)."""
import re, sys
from collections import Counter
def nodes(p):
    raw = open(p, 'rb').read()
    t = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('utf-8', 'ignore')
    cls, body = {}, {}
    for m in re.finditer(r'Begin Object (?:Class=(\S+) )?Name="([^"]+)"(.*?)\n\s*End Object', t, re.S):
        n = m.group(2)
        if m.group(1): cls[n] = m.group(1).rsplit('.', 1)[1]
        body[n] = body.get(n, '') + m.group(3)
    c = Counter(); names = {}
    for n, k0 in cls.items():
        if not k0.startswith('K2Node'): continue
        b = body.get(n, '')
        mem = re.search(r'(?:FunctionReference|VariableReference|EventReference)=\((?:MemberParent=[^,]*,)?MemberName="([^"]+)"', b)
        cf = re.search(r'CustomFunctionName="([^"]+)"', b)
        k = k0 + ':' + (mem.group(1) if mem else cf.group(1) if cf else '')
        c[k] += 1; names.setdefault(k, []).append(n)
    return c, names
a, an = nodes(sys.argv[1]); b, bn = nodes(sys.argv[2])
print('paste', sum(a.values()), 'live', sum(b.values()))
for k in sorted(set(a) | set(b)):
    if b[k] < a[k]: print('MISSING', a[k] - b[k], 'x', k, an[k][:4])
    elif b[k] > a[k]: print('EXTRA  ', b[k] - a[k], 'x', k, bn[k][:4])
