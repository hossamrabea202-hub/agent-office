# Castle v2 pass (Master, 2026-10-31): run once in the editor with the Python console:
#   exec(open(r'C:/Users/hossa/Documents/agent-office/CastleDecals2/castle_v2_apply.py').read())
# STEP 1 import the 4 new decals  STEP 2 snake cracks off in the stone materials (old values saved for undo)
# STEP 3 place wall cracks / impacts / stair wear / base grime (new folder "CastleDecals_v2", tag CastleV2)
# STEP 4 optimisation (small-light shadows off, draw distance on small props)  -> report _castle_v2.txt
# Undo: delete folder CastleDecals_v2 in the Outliner; run castle_v2_undo_cracks.py for the material values.
import os, json, math, random, unreal
ROOT = r'C:\Users\hossa\Documents\agent-office\CastleDecals2'
REP = os.path.join(ROOT, '_castle_v2.txt'); L = []
def log(s): L.append(s); open(REP, 'w').write('\n'.join(L))
EAL, MEL, tools = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary, unreal.AssetToolsHelpers.get_asset_tools()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
DROOT = '/Game/CastleDefender/Environment/Decals/Castle2'
NAMES = ('WallCrackA', 'WallCrackB', 'WallImpact', 'StairWear')
DO = globals().get('V2_STEPS', (1, 2, 3, 4))

# ---------------- STEP 1: import
MI = {}
if 1 in DO:
    M = unreal.load_asset('/Game/CastleDefender/Environment/Decals/M_LP2Decal')
    def imp(path, dst, srgb, kind=None):
        t = unreal.AssetImportTask(); t.filename = path; t.destination_path = dst; t.automated = True; t.replace_existing = True; t.save = True
        tools.import_asset_tasks([t]); a = unreal.load_asset(dst + '/' + os.path.splitext(os.path.basename(path))[0])
        a.set_editor_property('srgb', srgb)
        if kind == 'normal': a.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
        if kind == 'masks': a.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
        a.set_editor_property('address_x', unreal.TextureAddress.TA_CLAMP); a.set_editor_property('address_y', unreal.TextureAddress.TA_CLAMP)
        EAL.save_asset(a.get_path_name()); return a
    for n in NAMES:
        d = os.path.join(ROOT, 'textures'); dst = DROOT + '/' + n
        bc = imp(os.path.join(d, 'T_Decal_%s_BaseColor.png' % n), dst, True)
        orm = imp(os.path.join(d, 'T_Decal_%s_ORM.png' % n), dst, False, 'masks')
        nm = imp(os.path.join(d, 'T_Decal_%s_Normal_DirectX.png' % n), dst, False, 'normal')
        p = dst + '/MI_Decal_' + n
        mi = unreal.load_asset(p) if EAL.does_asset_exist(p) else tools.create_asset('MI_Decal_' + n, dst, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, M)
        for pn, t in (('BaseColor', bc), ('ORM', orm), ('Normal', nm)): MEL.set_material_instance_texture_parameter_value(mi, pn, t)
        MEL.set_material_instance_scalar_parameter_value(mi, 'NormalStrength', 1.0 if n != 'StairWear' else 0.6)
        EAL.save_asset(p); MI[n] = mi
    log('STEP1 imported %s' % ', '.join(NAMES))
else:
    for n in NAMES: MI[n] = unreal.load_asset(DROOT + '/' + n + '/MI_Decal_' + n)

# ---------------- STEP 2: old flat "snake" crack layer off
if 2 in DO:
    ar = unreal.AssetRegistryHelpers.get_asset_registry(); old = {}
    for a in ar.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialInstanceConstant')):
        n = str(a.asset_name)
        if not n.startswith('MI_Castle_'): continue
        mi = unreal.load_asset(str(a.package_name))
        if 'CrackAmount' in [str(x) for x in MEL.get_scalar_parameter_names(mi)]:
            old[str(a.package_name)] = MEL.get_material_instance_scalar_parameter_value(mi, 'CrackAmount')
            MEL.set_material_instance_scalar_parameter_value(mi, 'CrackAmount', 0.0); EAL.save_asset(str(a.package_name))
    json.dump(old, open(os.path.join(ROOT, '_crackamount_before.json'), 'w'), indent=1)
    log('STEP2 CrackAmount -> 0 on %d castle MIs (old values in _crackamount_before.json)' % len(old))

# ---------------- STEP 3: placement
def trace(a, b):
    h = unreal.SystemLibrary.line_trace_single(world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
    if not h: return None
    t = h.to_tuple()
    if not t[0]: return None
    return t[4], t[6] if len(t) > 6 else t[5], t[9] if len(t) > 9 else None   # location, impact normal, actor
def is_stone(actor):
    if actor is None: return False
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        for i in range(c.get_num_materials()):
            m = c.get_material(i)
            if m and ('Castle_StoneWall' in m.get_name() or 'Castle_Trim' in m.get_name() or 'Castle_StepCap' in m.get_name() or 'Castle_WalkFlag' in m.get_name() or 'Castle_GateArch' in m.get_name()): return True
    return False
def place(mi, loc, normal, w, h, depth, roll, label, sort=1):
    rot = unreal.MathLibrary.make_rot_from_x(normal * -1.0)
    rot = unreal.Rotator(roll, rot.pitch, rot.yaw)
    d = eas.spawn_actor_from_class(unreal.DecalActor, loc, rot)
    dc = d.decal
    dc.set_editor_property('decal_material', mi); dc.set_editor_property('decal_size', unreal.Vector(depth, w, h))
    dc.set_editor_property('sort_order', sort); dc.set_editor_property('fade_screen_size', 0.004)
    d.set_actor_label(label); d.set_folder_path('CastleDecals_v2'); d.tags = [unreal.Name('CastleV2')]
    return d
if 3 in DO:
    random.seed(1031)
    old = [a for a in eas.get_all_level_actors() if unreal.Name('CastleV2') in a.tags]
    for a in old: eas.destroy_actor(a)
    walls = [a for a in eas.get_all_level_actors() if isinstance(a, unreal.StaticMeshActor) and is_stone(a)]
    big = []
    for a in walls:
        o, e = a.get_actor_bounds(False)
        if max(e.x, e.y) > 200 and e.z > 150: big.append((a, o, e))
    big.sort(key=lambda t: -t[2].x * t[2].y * t[2].z)
    nc = ni = 0
    for a, o, e in big[:120]:
        area = 4 * (e.x + e.y) * 2 * e.z / 1e4      # m2 of side faces
        k = min(4, max(1, int(area / 60)))
        for j in range(k):
            side = random.choice((0, 1, 2, 3)); u = random.uniform(-0.8, 0.8); z = o.z + random.uniform(-0.6, 0.7) * e.z
            if side < 2:
                s = 1 if side == 0 else -1; start = unreal.Vector(o.x + s * (e.x + 150), o.y + u * e.y, z); end = unreal.Vector(o.x, o.y + u * e.y, z)
            else:
                s = 1 if side == 2 else -1; start = unreal.Vector(o.x + u * e.x, o.y + s * (e.y + 150), z); end = unreal.Vector(o.x + u * e.x, o.y, z)
            hit = trace(start, end)
            if not hit: continue
            loc, nrm, ha = hit
            if abs(nrm.z) > 0.35 or not is_stone(ha): continue
            if random.random() < 0.72:
                sz = random.uniform(140, 300); place(MI[random.choice(('WallCrackA', 'WallCrackB'))], loc, nrm, sz, sz, 30, random.uniform(0, 360), 'V2_Crack_%d' % nc, 2); nc += 1
            else:
                sz = random.uniform(90, 170); place(MI['WallImpact'], loc, nrm, sz, sz, 30, random.uniform(0, 360), 'V2_Impact_%d' % ni, 2); ni += 1
    log('STEP3 walls: %d candidate wall meshes, %d cracks, %d impacts' % (len(big), nc, ni))
    # stair wear: every tread top under stair-like actors
    ns = 0
    stairs = [a for a in eas.get_all_level_actors() if isinstance(a, unreal.StaticMeshActor) and any(k in (a.get_actor_label() + (a.static_mesh_component.static_mesh.get_name() if a.static_mesh_component.static_mesh else '')).lower() for k in ('stair', 'step', 'tread'))]
    seen = set()
    for a in stairs:
        o, e = a.get_actor_bounds(False)
        if e.z < 15: continue
        long_x = e.x >= e.y; n_s = int(max(e.x, e.y) * 2 / 32)
        for i in range(max(1, n_s)):
            t = -1 + (i + 0.5) * 2 / max(1, n_s)
            px, py = (o.x + t * e.x, o.y) if long_x else (o.x, o.y + t * e.y)
            hit = trace(unreal.Vector(px, py, o.z + e.z + 200), unreal.Vector(px, py, o.z - e.z - 50))
            if not hit: continue
            loc, nrm, ha = hit
            if nrm.z < 0.9: continue
            key = (round(loc.x / 25), round(loc.y / 25), round(loc.z / 8))
            if key in seen: continue
            seen.add(key)
            w = (min(e.x, e.y) * 2) * 0.55
            place(MI['StairWear'], loc, nrm, 26, w, 12, (0 if long_x else 90), 'V2_StairWear_%d' % ns, 1); ns += 1
            if ns > 900: break
    log('STEP3 stairs: %d stair actors, %d tread wear decals' % (len(stairs), ns))
    # base grime: band at the foot of the outer walls
    mud = unreal.load_asset('/Game/CastleDefender/Environment/Decals/MudSplashA/MI_Decal_MudSplashA')
    moss = unreal.load_asset('/Game/CastleDefender/Environment/Decals/MossPatchA/MI_Decal_MossPatchA')
    nb = 0
    for a, o, e in big[:120]:
        for side in range(4):
            for u in (-0.6, 0.0, 0.6):
                zt = o.z - e.z + 40
                if side < 2:
                    s = 1 if side == 0 else -1; start = unreal.Vector(o.x + s * (e.x + 150), o.y + u * e.y, zt); end = unreal.Vector(o.x, o.y + u * e.y, zt)
                else:
                    s = 1 if side == 2 else -1; start = unreal.Vector(o.x + u * e.x, o.y + s * (e.y + 150), zt); end = unreal.Vector(o.x + u * e.x, o.y, zt)
                hit = trace(start, end)
                if not hit: continue
                loc, nrm, ha = hit
                if abs(nrm.z) > 0.3 or not is_stone(ha): continue
                g = trace(loc + nrm * 30 + unreal.Vector(0, 0, 100), loc + nrm * 30 - unreal.Vector(0, 0, 400))
                if not g or (loc.z - g[0].z) > 120: continue    # only where the wall really meets the ground
                c = unreal.Vector(loc.x, loc.y, g[0].z + 45)
                place(random.choice((mud, moss)) if (mud and moss) else (mud or moss), c, nrm, 30, random.uniform(220, 320), 110, 0, 'V2_BaseGrime_%d' % nb, 1); nb += 1
    log('STEP3 base grime decals: %d' % nb)

# ---------------- STEP 4: optimisation
if 4 in DO:
    sl = 0; tl = 0; dd = 0
    for a in eas.get_all_level_actors():
        for lc in a.get_components_by_class(unreal.LocalLightComponent):
            tl += 1
            if lc.get_editor_property('cast_shadows') and lc.get_editor_property('attenuation_radius') < 900:
                lc.set_editor_property('cast_shadows', False); sl += 1
        if isinstance(a, unreal.StaticMeshActor) and a.get_folder_path() and 'castle' not in str(a.get_folder_path()).lower():
            c = a.static_mesh_component; o, e = a.get_actor_bounds(False)
            if max(e.x, e.y, e.z) < 120 and c.get_editor_property('ld_max_draw_distance') == 0:
                c.set_editor_property('ld_max_draw_distance', 7000.0); dd += 1
    log('STEP4 lights: %d local lights, shadows off on %d small ones (radius < 9 m); draw distance 70 m on %d small props' % (tl, sl, dd))
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
log('SAVED. Actors now: %d' % len(eas.get_all_level_actors()))
print('CASTLE V2 DONE')
