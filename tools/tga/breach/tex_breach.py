# Fresh broken-stone texture for the breach fracture faces (#327, TGA): blender -b --factory-startup -P tex_breach.py (env WORK)
# T_BreachFracture 1K BC/ORM/N: lighter, rougher, dusty freshly broken sandstone (castle stone colour family), tiling 1 m.
import bpy, os, numpy as np
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mine', 'tex_mine.py'), encoding='utf-8').read()
exec(src[:src.index('# ---- rock 2K')].replace("OUT = os.path.join(D, 'out', 'tex')", "OUT = os.path.join(os.environ.get('WORK', D), 'out', 'tex')"))
R = 1024
big = fbm(R, 3, 4, 70); fine = fbm(R, 50, 3, 71); con = ridged(R, 7, 3, 72); dust = ss(0.5, 0.75, fbm(R, 5, 3, 73))
h = 0.006 * big + 0.004 * con + 0.0015 * fine + 0.0004 * pn(R, 300, 74)        # conchoidal break surface
col = mix(lin(176, 156, 128), lin(198, 180, 150), big) * (0.9 + 0.2 * fine)[..., None]      # fresh inner sandstone
col = mix(col, lin(150, 132, 108), ss(0.6, 0.8, con) * 0.4); col = mix(col, lin(210, 200, 182), dust * 0.5)   # stone dust
rough = 0.7 + 0.22 * ss(0.38, 0.62, fbm(R, 4, 3, 75)) + 0.05 * (fine - 0.5) + 0.06 * dust
out('T_BreachFracture', col, rough, np.zeros_like(h), h, 1.0, 0.003)
print('TEX OK breach', flush=True)
