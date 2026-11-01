import sys, re; sys.path.insert(0, '.')
from t3d_parse import *
N = parse('../exports/adjustedfilm/castle-scroll-411/BP_ZombieHUD_EventGraph.txt')
def src(n, pin):
    for pn, out, links, dv in N[n]['pins'].values():
        if pn == pin and not out: return links, dv
def expr(n, pin, depth=0):
    links, dv = src(n, pin)
    if not links: return dv
    m = links[0][0]; nn = N[m]; mem = member(nn) or nn['cls'][7:]
    if depth > 4: return mem
    args = []
    for pn, out, l, d in nn['pins'].values():
        if not out and pn not in ('self', 'execute', 'WorldContextObject'): args.append('%s=%s' % (pn, expr(m, pn, depth + 1)))
    return '%s(%s)' % (mem, ', '.join(args))
for k, n in N.items():
    if member(n) in ('DrawTexture', 'DrawTextureSimple'):
        links, dv = src(k, 'Texture')
        tex = dv or (links and expr(k, 'Texture'))
        if tex and ('Key' in str(tex) or 'Portrait' in str(tex) or 'Gold' in str(tex)):
            print(k, str(tex)[-50:]); 
            for p in ('ScreenX', 'ScreenY', 'ScreenW', 'ScreenH'): print('   ', p, str(expr(k, p))[:300])
