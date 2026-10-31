# #366 tentacle skin stretched along the tentacles (adjustedfilm, 2026-10-31 night). UE 5.3 Python.
#   py "<repo>/handoffs/tentacle-skin-366/fix_tentacle_uv366_ue.py" --info                 READ-ONLY: tentacle actors, slots, materials,
#                                                                                          mesh axis, every texture sample of the material
#   py ".../fix_tentacle_uv366_ue.py" --build [--dry-run]                                  NEW assets only: M_..._UV366 (+ MI copies)
#   py ".../fix_tentacle_uv366_ue.py" --apply <label part> [--dry-run]                     swap on actors whose label contains it (backup json)
#   py ".../fix_tentacle_uv366_ue.py" --revert                                             put every swapped slot back from the backup
# Why it stretches: SK_CorruptedTentacle_01 is one mesh, ~254 m long at placed scale, and its UVs give the length far fewer
#   texels than the girth, so the cell / crack pattern smears into streaks.
# Fix: a copy of the tentacle material whose texture samples all read a length-aware cylindrical UV:
#   V = distance along the tentacle (world cm, actor scale included) / TileCm,  U = angle around the tentacle x a whole number
#   of tiles that makes texels square at the mean girth. Built from the PRE-SKINNED position, so the skin does not swim while
#   the tentacle sways or curls. Mips across the U wrap use seam-free derivatives (no seam line).
# The live material is never edited. Writes tentacle366_<mode>.txt next to itself.
import os, sys, json, unreal

A = sys.argv[1:]
DRY = '--dry-run' in A
MODE = next((m for m in ('--info', '--build', '--apply', '--revert') if m in A), '--info')
arg = lambda k, d: type(d)(A[A.index(k) + 1]) if k in A and A.index(k) + 1 < len(A) else d
TILE_CM = arg('--tile', 100.0)          # one texture tile per 1 m of skin (the cells read about palm-sized; tune in lookdev)
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\tentacle-skin-366'
MESH = '/Game/CastleDefender/Environment/Tentacles/Rig/SK_CorruptedTentacle_01'
SUFFIX = '_UV366'
BACKUP = os.path.join(HERE, 'tentacle366_backup.json')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
log = ['#366 tentacle UV %s%s' % (MODE, ' (DRY RUN)' if DRY else '')]


def root_of(mat):
    m = mat
    while isinstance(m, unreal.MaterialInstance) and m.get_editor_property('parent'): m = m.get_editor_property('parent')
    return m


def tentacle_slots():
    """[(actor, component, slot index, material)] for every skeletal mesh component that uses SK_CorruptedTentacle_01."""
    out = []
    for a in EAS.get_all_level_actors():
        for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
            sk = c.get_editor_property('skeletal_mesh_asset') if hasattr(c, 'skeletal_mesh_asset') else c.get_editor_property('skeletal_mesh')
            if not sk or not sk.get_path_name().startswith(MESH): continue
            for i in range(c.get_num_materials()):
                out.append((a, c, i, c.get_material(i)))
    return out


def mesh_axes():
    """long axis of the mesh (reference pose) + the two side axes and the mean radius around it (mesh cm)."""
    sk = unreal.load_asset(MESH)
    b = sk.get_bounds()
    e = [b.box_extent.x, b.box_extent.y, b.box_extent.z]
    k = e.index(max(e))
    side = [i for i in range(3) if i != k]
    unit = lambda i: unreal.LinearColor(*(1.0 if j == i else 0.0 for j in range(3)), 0.0)
    return unit(k), unit(side[0]), unit(side[1]), 0.5 * (e[side[0]] + e[side[1]]) * 0.5, 'XYZ'[k], e   # mean radius ~ half the mean half-extent (it tapers)


PROPS = [getattr(unreal.MaterialProperty, n) for n in dir(unreal.MaterialProperty) if n.startswith('MP_')]
WPO = [getattr(unreal.MaterialProperty, n) for n in ('MP_WORLD_POSITION_OFFSET',) if hasattr(unreal.MaterialProperty, n)]


def samples_of(mat, props=None):
    """every texture-sample expression reachable from the material's outputs (5.3: walk inputs from each property).
    Samples that also feed World Position Offset (the ripple) are left out: they run in the vertex shader."""
    if props is None:
        vs = {e.get_name() for e in samples_of(mat, WPO)}
        return [e for e in samples_of(mat, [p for p in PROPS if p not in WPO]) if e.get_name() not in vs]
    seen, todo, found = set(), [], []
    for prop in props:
        try: n = MEL.get_material_property_input_node(mat, prop)
        except Exception: n = None
        if n: todo.append(n)
    while todo:
        e = todo.pop()
        if e is None or e.get_name() in seen: continue
        seen.add(e.get_name())
        if isinstance(e, unreal.MaterialExpressionTextureSample): found.append(e)
        try: todo += [x for x in MEL.get_inputs_for_material_expression(mat, e) if x]
        except Exception as ex: log.append('  (inputs of %s unreadable: %s)' % (e.get_name(), ex))
        if isinstance(e, unreal.MaterialExpressionMaterialFunctionCall):
            log.append('  note: function call %s (samples inside it keep their own UVs)' % e.get_name())
    return found


UV_HLSL = r'''
float along = dot(PS, Axis) * length(WA);
float2 cr = float2(dot(PS, S1), dot(PS, S2));
float ang = atan2(cr.y, cr.x) * 0.15915494 + 0.5;
float tiles = max(1.0, round(6.2831853 * MeanR * length(WS) / TileCm));
float2 uv = float2(ang * tiles, along / TileCm);
float2 uv2 = float2(frac(ang + 0.5) * tiles, uv.y);
'''
OUT = {'UV': 'return uv;',
       'DX': 'float2 a = ddx(uv), b = ddx(uv2); return (abs(a.x) <= abs(b.x)) ? a : b;',
       'DY': 'float2 a = ddy(uv), b = ddy(uv2); return (abs(a.x) <= abs(b.x)) ? a : b;'}


def build_uv(m, axis, s1, s2, mean_r):
    """the three custom nodes (UV, DDX, DDY) fed by pre-skinned position and the actor's scale along / across."""
    pre = MEL.create_material_expression(m, unreal.MaterialExpressionPreSkinnedPosition, -3250, -600)
    ps = MEL.create_material_expression(m, unreal.MaterialExpressionVertexInterpolator, -3000, -600)   # vertex -> pixel
    MEL.connect_material_expressions(pre, '', ps, '')
    def const3(c, y):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -3000, y); e.set_editor_property('constant', c); return e
    def scalar(n, v, y):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -3000, y)
        e.set_editor_property('parameter_name', n); e.set_editor_property('default_value', v); return e
    def to_world(src, y):
        t = MEL.create_material_expression(m, unreal.MaterialExpressionTransform, -2750, y)
        t.set_editor_property('transform_source_type', unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL)
        t.set_editor_property('transform_type', unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
        MEL.connect_material_expressions(src, '', t, ''); return t
    ax, c1, c2 = const3(axis, -450), const3(s1, -300), const3(s2, -150)
    wa, ws = to_world(ax, -450), to_world(c1, -300)
    tile, mr = scalar('SkinTileCm', TILE_CM, 0), scalar('SkinMeanRadius', mean_r, 100)
    outs = {}
    for i, (k, tail) in enumerate(OUT.items()):
        cu = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, -2400, -600 + 250 * i)
        cu.set_editor_property('code', UV_HLSL + tail)
        cu.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT2)
        cu.set_editor_property('description', 'UV366_' + k)
        ins = []
        for n in ('PS', 'Axis', 'S1', 'S2', 'WA', 'WS', 'MeanR', 'TileCm'):
            ci = unreal.CustomInput(); ci.set_editor_property('input_name', n); ins.append(ci)
        cu.set_editor_property('inputs', ins)
        for n, src in (('PS', ps), ('Axis', ax), ('S1', c1), ('S2', c2), ('WA', wa), ('WS', ws), ('MeanR', mr), ('TileCm', tile)):
            MEL.connect_material_expressions(src, '', cu, n)
        outs[k] = cu
    return outs


def main():
    slots = tentacle_slots()
    axis, s1, s2, mean_r, axname, ext = mesh_axes()
    log.append('mesh %s: long axis %s, half extents %s, mean radius %.0f (mesh cm)' % (MESH.split('/')[-1], axname, [round(v) for v in ext], mean_r))
    log.append('tentacle slots in the level: %d on %d actors' % (len(slots), len({s[0].get_name() for s in slots})))
    mats = {}
    for a, c, i, m in slots:
        if m: mats.setdefault(m.get_path_name(), m)
    for p, m in mats.items():
        log.append('  material %s (root %s)' % (p, root_of(m).get_path_name()))
    roots = {root_of(m).get_path_name(): root_of(m) for m in mats.values()}

    if MODE == '--info':
        for a, c, i, m in slots[:40]:
            log.append('  %-32s %-22s slot %d %s scale %s' % (a.get_actor_label(), c.get_name(), i, m.get_name() if m else None, a.get_actor_scale3d()))
        for p, r in roots.items():
            ss = samples_of(r)
            log.append('root %s: %d texture samples' % (p, len(ss)))
            for e in ss:
                t = e.get_editor_property('texture')
                log.append('  %-40s %s' % (e.get_name(), t.get_path_name() if t else '-'))

    elif MODE == '--build':
        for p, r in roots.items():
            dst = p.rsplit('.', 1)[0] + SUFFIX
            log.append('new material %s (copy of %s)' % (dst, p))
            if DRY: log.append('  samples to remap: %d' % len(samples_of(r))); continue
            if EAL.does_asset_exist(dst): EAL.delete_asset(dst)               # our own copy only: rebuilt from the live one each run
            nm = EAL.duplicate_asset(p.rsplit('.', 1)[0], dst)
            ss = samples_of(nm)
            uv = build_uv(nm, axis, s1, s2, mean_r)
            for e in ss:
                MEL.connect_material_expressions(uv['UV'], '', e, 'UVs')
                try:
                    e.set_editor_property('mip_value_mode', unreal.TextureMipValueMode.TMVM_DERIVATIVE)
                    MEL.connect_material_expressions(uv['DX'], '', e, 'DDX(UVs)')
                    MEL.connect_material_expressions(uv['DY'], '', e, 'DDY(UVs)')
                except Exception as ex:
                    log.append('  %s: plain UV, no seam-free mips (%s)' % (e.get_name(), ex))
                log.append('  remapped %s' % e.get_name())
            MEL.recompile_material(nm); EAL.save_asset(dst)
        for p, m in mats.items():                                             # material instances: copy, re-parent to the new root
            if not isinstance(m, unreal.MaterialInstanceConstant): continue
            dst = p.rsplit('.', 1)[0] + SUFFIX
            log.append('new instance %s' % dst)
            if DRY: continue
            if EAL.does_asset_exist(dst): EAL.delete_asset(dst)
            ni = EAL.duplicate_asset(p.rsplit('.', 1)[0], dst)
            rp = root_of(m).get_path_name().rsplit('.', 1)[0] + SUFFIX
            MEL.set_material_instance_parent(ni, unreal.load_asset(rp)); EAL.save_asset(dst)

    elif MODE == '--apply':
        part = arg('--apply', '')
        if not part: raise SystemExit('--apply needs a label part, e.g. --apply TentacleHit_T_5')
        backup = json.load(open(BACKUP)) if os.path.exists(BACKUP) else []
        n = 0
        for a, c, i, m in slots:
            if part not in a.get_actor_label() or not m or m.get_path_name().split('.')[0].endswith(SUFFIX): continue
            new = m.get_path_name().rsplit('.', 1)[0] + SUFFIX
            if not EAL.does_asset_exist(new): log.append('  %s slot %d: %s missing, run --build first' % (a.get_actor_label(), i, new)); continue
            log.append('  %s %s slot %d: %s -> %s' % (a.get_actor_label(), c.get_name(), i, m.get_name(), new.split('/')[-1]))
            n += 1
            if DRY: continue
            backup.append({'actor': a.get_path_name(), 'comp': c.get_name(), 'slot': i, 'mat': m.get_path_name()})
            c.set_material(i, unreal.load_asset(new))
        if not DRY and n:
            json.dump(backup, open(BACKUP, 'w'), indent=1)
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        log.append('swapped %d slots' % n)

    elif MODE == '--revert':
        backup = json.load(open(BACKUP)) if os.path.exists(BACKUP) else []
        by = {a.get_path_name(): a for a in EAS.get_all_level_actors()}
        for b in backup:
            a = by.get(b['actor'])
            c = next((x for x in a.get_components_by_class(unreal.SkeletalMeshComponent) if x.get_name() == b['comp']), None) if a else None
            if not c: log.append('  gone: %s' % b['actor']); continue
            log.append('  %s slot %d back to %s' % (a.get_actor_label(), b['slot'], b['mat'].split('.')[-1]))
            if not DRY: c.set_material(b['slot'], unreal.load_asset(b['mat']))
        if not DRY and backup:
            os.remove(BACKUP); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()


main()
out = '\n'.join(log)
open(os.path.join(HERE, 'tentacle366_%s.txt' % MODE.strip('-')), 'w').write(out)
unreal.log(out); print(out)
