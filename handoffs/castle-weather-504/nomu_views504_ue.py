# shots of 4 castle views (before/after named by argv[1]); views from the card report
import sys, unreal
sys.path.insert(0, 'C:/Users/hossam.rabea/agent-office/handoffs/contact-decals-425'); import importlib, lookdev_cap; importlib.reload(lookdev_cap)
V = unreal.Vector
tag = sys.argv[1]; ev = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5
H = 'C:/Users/hossam.rabea/agent-office/handoffs/castle-weather-504/shots/'
VIEWS = [l.split() for l in open('C:/Users/hossam.rabea/agent-office/handoffs/castle-weather-504/views504.txt') if l.strip() and not l.startswith('#')]
for v in VIEWS:
    n = v[0]; c = V(*map(float, v[1:4])); t = V(*map(float, v[4:7]))
    lookdev_cap.shot(H + 'cw504_%s_%s.png' % (n, tag), c, t, ev, 50.0)
