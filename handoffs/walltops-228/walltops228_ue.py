# #228 Wall-walk tops: stretched, smeary texture -> world-aligned (triplanar) materials at a real scale (adjustedfilm, 2026-10-31).
#   py "<repo>/handoffs/walltops-228/walltops228_ue.py"                       REPORT (default, changes nothing): every mesh
#        component on castle actors (name has Castle/Wall/Tower/Rampart/Walk/Battle/Merlon), its mesh, materials, the
#        tiling-like scalar params and texture params of each MI -> walltops228_report.txt (post it on card #228).
#        Flags likely culprits: wood-named materials on wall actors, and MIs whose tiling param is < 1.
#   py ".../walltops228_ue.py" --fix MI_A MI_B ...   [--size 300]  [--dry-run]
#        makes M_WallWorldAligned once (WorldAlignedTexture / WorldAlignedNormal, texture size in cm), then for each named
#        MI a child MI_<name>_WA with that MI's own BaseColor / Normal / ORM textures, and swaps it in on every level
#        component using the MI (logged).
#   py ".../walltops228_ue.py" --revert           puts every logged material back.
import os, sys, unreal

A = sys.argv[1:]
DRY, FIX, REVERT = '--dry-run' in A, '--fix' in A, '--revert' in A
SIZE = float(A[A.index('--size') + 1]) if '--size' in A else 300.0
DST = '/Game/CastleDefender/Environment/WallTops'
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\walltops-228'
SWAPLOG, REPORT = os.path.join(HERE, 'walltops228_swaps.txt'), os.path.join(HERE, 'walltops228_report.txt')
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
KEYS = ('castle', 'wall', 'tower', 'rampart', 'walk', 'battle', 'merlon', 'parapet')
log = []


def comps():
    for a in EAS.get_all_level_actors():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            yield a, c


def kind(name):
    n = name.lower()
    if any(k in n for k in ('normal', 'nrm', '_n', 'nor')): return 'Normal'
    if any(k in n for k in ('orm', 'arm', 'rough', 'mask', 'rma', 'mra')): return 'ORM'
    if any(k in n for k in ('base', 'albedo', 'diffuse', 'color', 'colour', 'bc', 'diff')): return 'BaseColor'
    return None


def report():
    out, seen = ['#228 wall-top report (actor | component | mesh | slot | material | tiling params | textures | flag)'], {}
    for a, c in comps():
        if not any(k in (a.get_actor_label() + a.get_name()).lower() for k in KEYS): continue
        sm = c.get_editor_property('static_mesh')
        for i in range(c.get_num_materials()):
            m = c.get_material(i)
            if not m: continue
            til, tex = [], []
            if isinstance(m, unreal.MaterialInstance):
                for p in m.get_editor_property('scalar_parameter_values'):
                    nm = str(p.parameter_info.name)
                    if any(k in nm.lower() for k in ('til', 'uv', 'scale', 'repeat', 'size')): til.append('%s=%g' % (nm, p.parameter_value))
                for p in m.get_editor_property('texture_parameter_values'):
                    tex.append('%s=%s' % (p.parameter_info.name, p.parameter_value.get_name() if p.parameter_value else '-'))
            flag = []
            if 'wood' in m.get_name().lower(): flag.append('WOOD ON A WALL ACTOR')
            for t in til:
                try:
                    if float(t.split('=')[1]) < 1.0: flag.append('TILING < 1 (stretched)')
                except ValueError: pass
            out.append(' | '.join([a.get_actor_label(), c.get_name(), sm.get_name() if sm else '-', str(i), m.get_path_name(), ', '.join(til) or '-', ', '.join(tex) or '-', '; '.join(flag)]))
            seen[m.get_path_name()] = seen.get(m.get_path_name(), 0) + 1
    out += ['', 'Materials by use count:'] + ['%4d  %s' % (n, p) for p, n in sorted(seen.items(), key=lambda kv: -kv[1])]
    open(REPORT, 'w').write('\n'.join(out)); log.append('report: %d lines -> %s' % (len(out), REPORT))


def fcall(m, path, x, y):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionMaterialFunctionCall, x, y)
    e.set_editor_property('material_function', unreal.load_asset(path)); return e


def stype(tex):
    cs = str(tex.get_editor_property('compression_settings')).upper()
    if 'NORMAL' in cs: return unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    if 'MASK' in cs: return unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
    if 'GRAYSCALE' in cs: return unreal.MaterialSamplerType.SAMPLERTYPE_GRAYSCALE if tex.get_editor_property('srgb') else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE
    return unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if tex.get_editor_property('srgb') else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR


def textures_of(mi):
    got = {}
    if isinstance(mi, unreal.MaterialInstance):
        for p in mi.get_editor_property('texture_parameter_values'):
            k = kind(str(p.parameter_info.name))
            if k and p.parameter_value and k not in got: got[k] = (p.parameter_value, str(p.parameter_info.name))
    return got


def base_material(seed):
    # seed = textures of the first MI: they become the defaults and set each sampler type (a mismatch would not compile)
    path = DST + '/M_WallWorldAligned'
    if EAL.does_asset_exist(path): return unreal.load_asset(path)
    log.append('create ' + path)
    if DRY: return None
    m = AT.create_asset('M_WallWorldAligned', DST, unreal.Material, unreal.MaterialFactoryNew())
    size = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -1200, 400)
    size.set_editor_property('parameter_name', 'TextureSizeCm'); size.set_editor_property('default_value', SIZE)
    sz3 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -1000, 400)
    sz2 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -1100, 400)
    MEL.connect_material_expressions(size, '', sz2, 'A'); MEL.connect_material_expressions(size, '', sz2, 'B')
    MEL.connect_material_expressions(sz2, '', sz3, 'A'); MEL.connect_material_expressions(size, '', sz3, 'B')
    wat = '/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture'
    wan = '/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedNormal'
    y = -300
    for name, fn, prop in (('BaseColor', wat, unreal.MaterialProperty.MP_BASE_COLOR), ('Normal', wan, unreal.MaterialProperty.MP_NORMAL), ('ORM', wat, None)):
        if name not in seed: log.append('  no %s texture on the first MI: %s left out' % (name, name)); continue
        t = MEL.create_material_expression(m, unreal.MaterialExpressionTextureObjectParameter, -1200, y)
        t.set_editor_property('parameter_name', name); t.set_editor_property('texture', seed[name][0])
        t.set_editor_property('sampler_type', stype(seed[name][0]))
        f = fcall(m, fn, -700, y)
        MEL.connect_material_expressions(t, '', f, 'TextureObject'); MEL.connect_material_expressions(sz3, '', f, 'TextureSize')
        if prop: MEL.connect_material_property(f, 'XYZ Texture', prop)
        else:
            for ch, p in (('g', unreal.MaterialProperty.MP_ROUGHNESS), ('r', unreal.MaterialProperty.MP_AMBIENT_OCCLUSION), ('b', unreal.MaterialProperty.MP_METALLIC)):
                k = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -300, y + {'r': 0, 'g': 80, 'b': 160}[ch])
                for c_ in 'rgba': k.set_editor_property(c_, c_ == ch)
                MEL.connect_material_expressions(f, 'XYZ Texture', k, ''); MEL.connect_material_property(k, '', p)
        y += 300
    MEL.recompile_material(m); EAL.save_asset(path); return m


def fix(names):
    swaps, base = [], None
    for nm in names:
        src = None
        for a, c in comps():
            for i in range(c.get_num_materials()):
                m = c.get_material(i)
                if m and m.get_name() == nm: src = m
        if not src: log.append('not in the level: ' + nm); continue
        tx = textures_of(src)
        if base is None: base = base_material(tx)
        wa = DST + '/' + nm + '_WA'
        log.append(('reuse ' if EAL.does_asset_exist(wa) else 'create ') + wa)
        if DRY: mi = None
        else:
            mi = unreal.load_asset(wa) if EAL.does_asset_exist(wa) else AT.create_asset(nm + '_WA', DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
            mi.set_editor_property('parent', base)
            MEL.set_material_instance_scalar_parameter_value(mi, 'TextureSizeCm', SIZE)
        for k, (tex, pn) in tx.items():
            log.append('  %s <- %s (%s)' % (k, tex.get_name(), pn))
            if mi: MEL.set_material_instance_texture_parameter_value(mi, k, tex)
        if not tx: log.append('  %s has no texture params (a plain Material?): set the textures on %s_WA by hand' % (nm, nm))
        if mi: EAL.save_asset(wa)
        for a, c in comps():
            for i in range(c.get_num_materials()):
                m = c.get_material(i)
                if m and m.get_name() == nm:
                    swaps.append('%s|%s|%d|%s' % (a.get_name(), c.get_name(), i, m.get_path_name()))
                    if mi: c.set_material(i, mi)
    log.append('swapped %d slots' % len(swaps))
    if swaps and not DRY: open(SWAPLOG, 'a').write('\n'.join(swaps) + '\n'); unreal.EditorLevelLibrary.save_current_level()


def revert():
    if not os.path.exists(SWAPLOG): raise SystemExit('nothing to revert')
    rows = [l.split('|') for l in open(SWAPLOG).read().splitlines() if l]
    for a, c in comps():
        for an, cn, i, old in rows:
            if a.get_name() == an and c.get_name() == cn:
                log.append('revert %s.%s[%s] -> %s' % (an, cn, i, old))
                if not DRY: c.set_material(int(i), unreal.load_asset(old))
    if not DRY: os.rename(SWAPLOG, SWAPLOG + '.reverted'); unreal.EditorLevelLibrary.save_current_level()


if REVERT: revert()
elif FIX:
    skip = {A.index('--size') + 1} if '--size' in A else set()
    fix([x for j, x in enumerate(A) if j > A.index('--fix') and j not in skip and not x.startswith('--')])
else: report()
unreal.log('#228 walltops' + (' (DRY RUN)' if DRY else '') + '\n' + '\n'.join(log))
