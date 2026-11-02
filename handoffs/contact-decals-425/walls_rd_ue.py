# #425 read-only: which wall meshes behind the planned props have Receives Decals off?
import collections, unreal
g = {'__name__': 'x'}; exec(open('C:/Users/hossam.rabea/agent-office/handoffs/contact-decals-425/place_contact425_ue.py', encoding='utf-8').read().split("if '--remove' in args")[0], g)
W = g['W']; c = collections.Counter(); walls = {}
for a, rule, o, e, hit, soot in g['plan']():
    if not hit: continue
    h = unreal.SystemLibrary.line_trace_single(W, o, hit[1] - hit[2] * 3.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [a], unreal.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    comp = t[10] if t else None
    if comp: walls[comp.get_owner().get_actor_label()] = comp.get_editor_property('receives_decals'); c[comp.get_editor_property('receives_decals')] += 1
print('props by wall receives_decals:', dict(c)); print('walls:', len(walls), 'off:', sorted(k for k, v in walls.items() if not v)[:12])
