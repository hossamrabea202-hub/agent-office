# #440 grass re-layout + colour, applied from plan.csv (relayout.py) (i5, 2026-11-03). Aborts in PIE.
#   py grass440_ue.py mats                                     new MIs MI_vczndjqja_440 / MI_vlkhcbxia_440 / MI_MWAM_Grass_440
#                                                              (children of the current ones: summer tint + straw variation), saved
#   py grass440_ue.py apply --dry-run [--region x0,y0,x1,y1]   counts only
#   py grass440_ue.py apply [--region x0,y0,x1,y1]             removals + Z/XY heights + the _440 MI on the grass components
#                                                              (backup: every touched component's full instance list -> backup/)
#   py grass440_ue.py revert                                   restores every backed-up component exactly (instances + material)
# Nothing is saved by apply/revert: the Master saves the map after the owner's OK. New MIs only, no live material edited.
import csv, json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]; mode = A[0]
H = None
for h in ('C:/Users/hossam.rabea/agent-office/handoffs/grass-440/', 'C:/Users/hossa/Documents/agent-office/handoffs/grass-440/'):
    if os.path.exists(h + 'plan.csv'): H = h; break
BK = H + 'backup/'
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
DRY = '--dry-run' in A
REG = [float(v) for v in A[A.index('--region') + 1].split(',')] if '--region' in A else None
SCANS = {  # scan MI -> new MI name. Tint calibrated by base-colour lookdev (handoffs/grass-440/README.md)
    '/Game/CastleDefender/AssetPacks/Fab/Megascans/Plants/Wild_Grass_vczndjqja/Raw/MI_vczndjqja': 'MI_vczndjqja_440',
    '/Game/CastleDefender/AssetPacks/Fab/Megascans/Plants/Wild_Grass_vlkhcbxia/Raw/MI_vlkhcbxia': 'MI_vlkhcbxia_440'}
DST = '/Game/CastleDefender/Environment/Foliage/Grass440'
LC = unreal.LinearColor
TINT = {'MI_vczndjqja_440': LC(0.40, 0.43, 0.25, 1), 'MI_vlkhcbxia_440': LC(0.55, 0.56, 0.42, 1)}
VAR = {'Color Var Color 01': LC(0.62, 0.52, 0.30, 1),     # straw (was rust brown)
       'Color Var Color 02': LC(0.60, 0.62, 0.30, 1),     # fresh yellow-green (as before)
       'Color Var Color 03': LC(0.42, 0.37, 0.21, 1)}     # dry olive-brown (was purple-red)

def new_mi(name):
    p = DST + '/' + name
    return unreal.load_asset(p) if EAL.does_asset_exist(p) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())

if mode == 'mats':
    for src, name in SCANS.items():
        mi = new_mi(name); MEL.set_material_instance_parent(mi, unreal.load_asset(src))
        MEL.set_material_instance_vector_parameter_value(mi, 'Base Color Tint', TINT[name])
        for k, v in VAR.items(): MEL.set_material_instance_vector_parameter_value(mi, k, v)
        MEL.set_material_instance_vector_parameter_value(mi, 'Health Color Overlay', LC(0.30, 0.22, 0.08, 0))   # dry tips, not red
        MEL.set_material_instance_scalar_parameter_value(mi, 'Local Random Color Variation', 0.4)
        MEL.update_material_instance(mi); EAL.save_loaded_asset(mi)
        print('MI', mi.get_path_name(), 'tint', TINT[name])
    raise SystemExit

def comps():
    out = {}
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() not in ('Env_GrassTall', 'Env_BaseRubble', 'Meadow351'): continue
        for ci, c in enumerate(a.get_components_by_class(unreal.InstancedStaticMeshComponent)):
            out[(a.get_actor_label() + '#' + a.get_name(), ci)] = c
    return out

if mode == 'revert':
    C = comps(); n = 0
    for f in sorted(os.listdir(BK)) if os.path.exists(BK) else []:
        d = json.load(open(BK + f)); c = C.get((d['actor'], d['comp']))
        if not c: print('MISSING', d['actor'], d['comp']); continue
        c.modify(); c.clear_instances()
        xs = [unreal.Transform(unreal.Vector(*t[0:3]), unreal.Rotator(*t[3:6]), unreal.Vector(*t[6:9])) for t in d['xf']]
        c.add_instances(xs, False, True)
        mat = unreal.load_asset(d['mat']) if d['mat'] else None
        c.set_material(0, mat); n += 1
        os.remove(BK + f)
    print('reverted %d components' % n); raise SystemExit

if mode == 'apply':
    plan = {}
    for r in csv.DictReader(open(H + 'plan.csv')):
        plan.setdefault((r['actor'], int(r['comp'])), []).append(r)
    # guard: the plan addresses instances by index, so every component must still match the dump it was computed from
    # (same mesh, same count, positions within 10 cm); a component that differs is skipped and reported, never guessed
    dump = {}
    for r in csv.DictReader(open(H + 'grass_dump.csv')):
        dump.setdefault((r['actor'], int(r['comp'])), []).append((r['mesh'], float(r['x']), float(r['y'])))
    C = comps(); os.makedirs(BK, exist_ok=True)
    tot = {'remove': 0, 'scale': 0, 'keep': 0, 'comps': 0, 'skipped_region': 0, 'skipped_mismatch': 0}
    for key, rs in plan.items():
        c = C.get(key)
        if not c: print('MISSING component', key); continue
        n = c.get_instance_count()
        xf = [c.get_instance_transform(i, True) for i in range(n)]
        ref = dump.get(key, [])
        mesh_ok = ref and c.get_editor_property('static_mesh').get_name() == ref[0][0]
        pos_ok = len(ref) == n and all(abs(t.translation.x - x) <= 10 and abs(t.translation.y - y) <= 10 for t, (_, x, y) in zip(xf, ref))
        if not (mesh_ok and pos_ok):
            print('SKIP (does not match grass_dump.csv: re-run grass_dump_ue.py + relayout.py on this map)', key, 'live', n, 'dump', len(ref))
            tot['skipped_mismatch'] += 1; continue
        if REG:
            rs2 = [r for r in rs if REG[0] <= xf[int(r['idx'])].translation.x <= REG[2] and REG[1] <= xf[int(r['idx'])].translation.y <= REG[3]]
            tot['skipped_region'] += len(rs) - len(rs2); rs = rs2
        if not any(r['action'] != 'keep' for r in rs): continue
        mesh = c.get_editor_property('static_mesh'); m0 = c.get_material(0)
        is_grass = any(w in mesh.get_name() for w in ('vczndjqja', 'vlkhcbxia', 'MWAM_Grass'))
        tot['comps'] += 1
        for r in rs: tot[r['action']] += 1
        if DRY: continue
        fn = BK + '%s__%d.json' % (key[0].replace('#', '_'), key[1])
        if not os.path.exists(fn):                       # first apply only: the original state
            json.dump({'actor': key[0], 'comp': key[1], 'mat': m0.get_path_name() if m0 and '_440' not in m0.get_name() else (json.load(open(fn))['mat'] if os.path.exists(fn) else None),
                       'xf': [[t.translation.x, t.translation.y, t.translation.z, t.rotation.rotator().roll, t.rotation.rotator().pitch, t.rotation.rotator().yaw,
                               t.scale3d.x, t.scale3d.y, t.scale3d.z] for t in xf]}, open(fn, 'w'))
        c.modify()
        for r in rs:                                     # heights first (indices still valid)
            if r['action'] != 'scale': continue
            i = int(r['idx']); t = xf[i]; sxy = float(r['sxy'] or r['sz']); sz = float(r['sz'])
            c.update_instance_transform(i, unreal.Transform(t.translation, t.rotation.rotator(), unreal.Vector(sxy, sxy, sz)), True, False, True)
        rem = sorted((int(r['idx']) for r in rs if r['action'] == 'remove'), reverse=True)
        if rem: c.remove_instances(rem)
        if is_grass and m0 and '_440' not in m0.get_name():
            par = m0.get_editor_property('parent') if isinstance(m0, unreal.MaterialInstance) else None
            for src, name in SCANS.items():
                if m0.get_path_name().split('.')[0] == src or (par and par.get_path_name().split('.')[0] == src):
                    c.set_material(0, unreal.load_asset(DST + '/' + name)); break
    print(('DRY RUN ' if DRY else '') + 'apply%s: %s' % (' region %s' % REG if REG else '', tot))
    raise SystemExit
