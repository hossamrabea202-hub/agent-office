# Obsidian Sovereign helm, card #485 (i5 helper, 2026-11-04). Editor script, Master applies on i9. UE 5.8. Aborts in PIE.
#   py setup_helmet_ue.py --dry-run           reads everything, changes nothing, prints the plan and every check. Default.
#   py setup_helmet_ue.py --apply             imports + sets the data + adds the component, compiles, saves. Backup: helmet_backup.json
#   py setup_helmet_ue.py --apply --start-owned   same, and a NEW game starts with the helm owned + worn (owner decision, see README)
#   py setup_helmet_ue.py --revert            puts the data + EmberMinTier back and removes Obs_Helmet. Imported assets stay (add --delete-assets)
# What --apply does, in this order; it never re-runs setup_set_v2_ue.py, so the other 15 piece rows are not recomputed:
#   1. imports SM_ObsidianSovereign_Helmet + 3 textures into .../ObsidianSovereign/Helmet (NEW assets; refuses to overwrite),
#      makes MI_ObsidianSovereign_Helmet on M_ObsidianSovereign (same parent + same 3 parameters as the other pieces)
#   2. BPC_ObsidianSet class defaults: appends row k = 15 (PieceId 15, PieceBone head, PieceOffset = inverse(head in knight ref pose)),
#      AvailMask |= 32; EmberMinTier 3 -> 4 (ember2_ue.py: "when the helmet ships, set it to 4")
#   3. hero: StaticMeshComponent Obs_Helmet under KnightMesh, tag ObsK15, hidden, no collision, overlay as on the other pieces
#   4. hero's copy of BPC_ObsidianSet (it overrides the class data, faults-1205 F3): the same row + mask. STOPS if F3 isn't applied.
import json, os, sys, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
A = sys.argv[1:]
APPLY, REVERT = '--apply' in A, '--revert' in A
try:
    HERE = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
except NameError:                                        # the editor's py command doesn't always set __file__
    HERE = next(h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/obsidian-sovereign/helmet', 'C:/Users/hossa/Documents/agent-office/handoffs/obsidian-sovereign/helmet') if os.path.isdir(h))
BK = HERE + '/helmet_backup.json'
ROOT = '/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign'
DST = ROOT + '/Helmet'
SM, MI, TN = 'SM_ObsidianSovereign_Helmet', 'MI_ObsidianSovereign_Helmet', 'T_ObsidianSovereign_Helmet'
COMP = '/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
KNIGHT = '/Game/ShadowKight/Mesh/ShadowknightUE_SK'
MASTER = ROOT + '/M_ObsidianSovereign'
PID, BONE, BIT, VNAME = 15, 'head', 32, 'Obs_Helmet'
HEAD_EXPECT = (0.0, -4.4892, 157.1086)                   # measured on i5, cm. A different knight rig means the fit has to be redone
BBOX_EXPECT = ((-12.5, -18.0, 149.3), (12.5, 11.9, 183.0))  # UE cm, knight space, from the FBX (fit_report.json); checked after the import
EAL, BEL, MEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary, unreal.MaterialEditingLibrary
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); L = unreal.SubobjectDataBlueprintFunctionLibrary
stops = []
def stop(m): stops.append(m); print('STOP:', m)
def ok(m): print('ok  ', m)

def template_map(hero):
    out = {}
    for h in sub.k2_gather_subobject_data_for_blueprint(hero):
        d = L.get_data(h); o = L.get_object(d)
        if o: out[str(L.get_variable_name(d))] = (o, h)
    return out
def xf(t):
    r = t.rotation.rotator(); return [round(v, 3) for v in (t.translation.x, t.translation.y, t.translation.z, r.roll, r.pitch, r.yaw, t.scale3d.x)]
def ser(v):
    if isinstance(v, unreal.Transform): return ['XF'] + xf(v)
    if isinstance(v, unreal.Name): return ['N', str(v)]
    if hasattr(v, '__iter__') and not isinstance(v, str): return [ser(x) for x in v]
    return v
def de(v):
    if isinstance(v, list) and v and v[0] == 'XF':
        return unreal.Transform(unreal.Vector(*v[1:4]), unreal.Rotator(*v[4:7]), unreal.Vector(v[7], v[7], v[7]))
    if isinstance(v, list) and v and v[0] == 'N': return unreal.Name(v[1])
    if isinstance(v, list): return [de(x) for x in v]
    return v
def has_prop(o, n):
    try: o.get_editor_property(n); return True
    except Exception: return False
DATA = ('AvailMask', 'PieceId', 'PieceBone', 'PieceOffset')
EXTRA = ('EmberMinTier', 'ObsOwned', 'ObsWorn')
def snapshot(o): return {n: ser(o.get_editor_property(n)) for n in DATA + EXTRA if has_prop(o, n)}

setbp = unreal.load_asset(COMP); setc = setbp.generated_class(); cdo = unreal.get_default_object(setc)
hero = unreal.load_asset(HERO); T = template_map(hero)
tpl = next((o for o, _ in T.values() if o.get_class() == setc), None)
if not tpl: print('NO ObsidianSet component on the hero: abort'); raise SystemExit

# ------------------------------------------------------------------------------------------------- revert
if REVERT:
    if not os.path.exists(BK): print('no helmet_backup.json: nothing to revert'); raise SystemExit
    bk = json.load(open(BK))
    setbp.modify(); cdo.modify()
    for n, v in bk['class'].items(): cdo.set_editor_property(n, de(v))
    EAL.save_loaded_asset(setbp)
    hero.modify()
    if VNAME in T:
        sub.delete_subobject(T['KnightMesh'][1], T[VNAME][1], hero)
        print('removed hero.' + VNAME)
    BEL.compile_blueprint(hero)
    tpl = next((o for o, _ in template_map(hero).values() if o.get_class() == setc), None); tpl.modify()
    for n, v in bk['hero'].items(): tpl.set_editor_property(n, de(v))
    BEL.compile_blueprint(hero); EAL.save_loaded_asset(hero)
    print('REVERTED: class + hero data back to the backup, Obs_Helmet removed, both saved.')
    if '--delete-assets' in A:
        print('deleted', DST, EAL.delete_directory(DST))
    else:
        print('assets left in', DST, '(nothing references them; --revert --delete-assets removes them)')
    os.rename(BK, BK + '.reverted'); raise SystemExit

# ------------------------------------------------------------------------------------------------- checks (read only)
for n in ('%s.fbx' % SM, 'textures/%s_BaseColor.png' % TN, 'textures/%s_ORM.png' % TN, 'textures/%s_Normal_DirectX.png' % TN):
    (ok if os.path.exists(HERE + '/' + n) else stop)('file ' + n)
for p, why in ((MASTER, 'parent material'), (KNIGHT, 'knight')):
    (ok if EAL.does_asset_exist(p) else stop)('%s %s' % (why, p))
for n in (SM, MI, TN + '_BaseColor', TN + '_ORM', TN + '_Normal_DirectX'):
    if EAL.does_asset_exist('%s/%s' % (DST, n)): stop('%s/%s already exists: this script only makes NEW assets (--revert --delete-assets first)' % (DST, n))
# head bone + the method itself: the same ref-pose read must reproduce the offsets already saved for the other 15 rows
sk = unreal.load_asset(KNIGHT).get_editor_property('skeleton')
pose = unreal.AnimPoseExtensions.get_reference_pose(sk); W = unreal.AnimPoseSpaces.WORLD
head = unreal.AnimPoseExtensions.get_bone_pose(pose, BONE, W)
d = max(abs(a - b) for a, b in zip((head.translation.x, head.translation.y, head.translation.z), HEAD_EXPECT))
(ok if d < 0.01 else stop)('head bone in knight ref pose %s (expected %s)' % (xf(head), HEAD_EXPECT))
OFFSET = head.inverse()
print('     PROPOSED PieceOffset row:', xf(OFFSET), '(translation x y z, roll pitch yaw, scale)')
ids, bones, offs = [list(cdo.get_editor_property(n)) for n in ('PieceId', 'PieceBone', 'PieceOffset')]
worst = 0.0
for b, o in zip(bones, offs):
    t = unreal.AnimPoseExtensions.get_bone_pose(pose, str(b), W).inverse()
    worst = max(worst, abs(t.translation.x - o.translation.x), abs(t.translation.y - o.translation.y), abs(t.translation.z - o.translation.z))
(ok if worst < 0.05 else stop)('offset method reproduces the %d saved rows: worst translation error %.4f cm' % (len(offs), worst))
# class data
av = cdo.get_editor_property('AvailMask')
print('     class: rows %d, AvailMask %d, KnightCover %s, BundleMask %s' % (len(ids), av, list(cdo.get_editor_property('KnightCover')), list(cdo.get_editor_property('BundleMask'))))
already = PID in ids
if already: stop('class table already has piece 15')
else: ok('new row index k = %d, tag ObsK%d' % (len(ids), len(ids)))
K = len(ids)
if list(cdo.get_editor_property('KnightCover'))[3] != BIT: stop('KnightCover[3] (helmet slot) is not 32')
else: ok('KnightCover[3] = 32: the knight helmet slot hides exactly when the helm is worn')
if list(cdo.get_editor_property('BundleMask'))[0] != BIT: stop('BundleMask[0] (Helm bundle) is not 32')
else: ok('BundleMask[0] = 32, price %d' % list(cdo.get_editor_property('PartPrice'))[5])
if has_prop(cdo, 'EmberMinTier'):
    print('     EmberMinTier: class %d, hero copy %s -> 4' % (cdo.get_editor_property('EmberMinTier'), tpl.get_editor_property('EmberMinTier') if has_prop(tpl, 'EmberMinTier') else '?'))
else:
    print('WARN EmberMinTier not on the class (ember2_ue.py not applied here): left alone. If ember2 comes later, set it to 4 then.')
# hero
tags = {}
for n, (o, _) in T.items():
    if isinstance(o, unreal.StaticMeshComponent):
        for t in o.get_editor_property('component_tags'): tags[str(t)] = n
if 'ObsK%d' % K in tags: stop('tag ObsK%d is already on hero.%s' % (K, tags['ObsK%d' % K]))
if VNAME in T: stop('hero already has ' + VNAME)
if 'KnightMesh' not in T: stop('hero has no KnightMesh')
ref = T.get('Obs_Shoulders_L')
aura = ref[0].get_editor_property('overlay_material') if ref else None
print('     overlay taken from Obs_Shoulders_L:', aura.get_path_name() if aura else None)
hid, hrows, hav = tpl.get_editor_property('PieceId'), tpl.get_editor_property('PieceBone'), tpl.get_editor_property('AvailMask')
print('     hero copy: rows %d, AvailMask %d, ObsOwned %d, ObsWorn %d' % (len(hid), hav, tpl.get_editor_property('ObsOwned'), tpl.get_editor_property('ObsWorn')))
if len(hid) != len(ids) or hav != av:
    stop('hero copy differs from the class (rows %d vs %d, AvailMask %d vs %d): run faults-1205/f3_fix_ue.py --apply FIRST, then this' % (len(hid), len(ids), hav, av))
else: ok('hero copy matches the class: F3 is applied here')
# API smoke test: only constructs transient objects, imports nothing
ui = unreal.FbxImportUI(); ui.static_mesh_import_data.combine_meshes = True
ui.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
ok('import API present: AssetImportTask %s, FbxImportUI, add_new_subobject %s, rename_subobject %s, delete_subobject %s' % (
    bool(unreal.AssetImportTask()), hasattr(sub, 'add_new_subobject'), hasattr(sub, 'rename_subobject'), hasattr(sub, 'delete_subobject')))
if not APPLY:
    print('DRY RUN: nothing changed.' + (' %d STOP(s) above would block --apply.' % len(stops) if stops else ' --apply would go ahead.')); raise SystemExit
if stops: print('STOP: nothing changed, fix the %d item(s) above.' % len(stops)); raise SystemExit

# ------------------------------------------------------------------------------------------------- apply
if not os.path.exists(BK):
    json.dump({'class': snapshot(cdo), 'hero': snapshot(tpl)}, open(BK, 'w'))
tools = unreal.AssetToolsHelpers.get_asset_tools()
def task(path, opts=None):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = DST; t.automated = True; t.save = True; t.replace_existing = False
    if opts: t.options = opts
    return t
tex = {TN + '_BaseColor': (True, unreal.TextureCompressionSettings.TC_DEFAULT),
       TN + '_ORM': (False, unreal.TextureCompressionSettings.TC_MASKS),
       TN + '_Normal_DirectX': (False, unreal.TextureCompressionSettings.TC_NORMALMAP)}
tools.import_asset_tasks([task('%s/textures/%s.png' % (HERE, n)) for n in tex])
for n, (srgb, comp) in tex.items():
    t = unreal.load_asset('%s/%s' % (DST, n))
    t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
    if 'Normal' in n: t.set_editor_property('flip_green_channel', False)
    EAL.save_loaded_asset(t)
ui = unreal.FbxImportUI()
ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
ui.static_mesh_import_data.combine_meshes = True
ui.static_mesh_import_data.generate_lightmap_u_vs = False
ui.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
tools.import_asset_tasks([task('%s/%s.fbx' % (HERE, SM), ui)])
mesh = unreal.load_asset('%s/%s' % (DST, SM))
if not mesh: print('STOP: mesh import failed. Class + hero untouched; the textures are in', DST); raise SystemExit
b = mesh.get_bounding_box()
print('mesh: %d tris, bounds min (%.1f %.1f %.1f) max (%.1f %.1f %.1f)' % (mesh.get_num_triangles(0), b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z))
lo, hi = BBOX_EXPECT
if not (all(abs(u - v) < 1.0 for u, v in zip((b.min.x, b.min.y, b.min.z), lo)) and all(abs(u - v) < 1.0 for u, v in zip((b.max.x, b.max.y, b.max.z), hi))):
    print('STOP: bounds are not the expected %s (scale or axes wrong?). Class + hero untouched; assets are in %s' % (BBOX_EXPECT, DST)); raise SystemExit
mi = tools.create_asset(MI, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
MEL.set_material_instance_parent(mi, unreal.load_asset(MASTER))
for pn, tn in (('BaseColor', 'BaseColor'), ('ORM', 'ORM'), ('Normal', 'Normal_DirectX')):
    MEL.set_material_instance_texture_parameter_value(mi, pn, unreal.load_asset('%s/%s_%s' % (DST, TN, tn)))
EAL.save_loaded_asset(mi)
mesh.set_material(0, mi); EAL.save_loaded_asset(mesh)
# class defaults
setbp.modify(); cdo.modify()
cdo.set_editor_property('PieceId', ids + [PID])
cdo.set_editor_property('PieceBone', bones + [unreal.Name(BONE)])
cdo.set_editor_property('PieceOffset', offs + [OFFSET])
cdo.set_editor_property('AvailMask', av | BIT)
if has_prop(cdo, 'EmberMinTier'): cdo.set_editor_property('EmberMinTier', 4)
EAL.save_loaded_asset(setbp)
# hero component
hero.modify()
h, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=T['KnightMesh'][1], new_class=unreal.StaticMeshComponent, blueprint_context=hero))
if not fail.is_empty(): print('STOP: add component:', fail, '(class data is already written; run --revert)'); raise SystemExit
sub.rename_subobject(h, unreal.Text(VNAME))
c = L.get_object(L.get_data(h))
c.set_editor_property('static_mesh', mesh)
c.set_editor_property('component_tags', [unreal.Name('ObsK%d' % K)])
c.set_editor_property('visible', False)
c.set_collision_profile_name('NoCollision')
c.set_editor_property('generate_overlap_events', False)
c.set_editor_property('relative_transform', unreal.Transform())   # knight space; BeginPlay attaches it to the head bone with PieceOffset
if aura: c.set_editor_property('overlay_material', aura)
BEL.compile_blueprint(hero)
# the hero's own copy overrides the class (F3): same row, same mask. The compile can rebuild templates, so find it again
tpl = next((o for o, _ in template_map(hero).values() if o.get_class() == setc), None); tpl.modify()
tpl.set_editor_property('PieceId', list(tpl.get_editor_property('PieceId')) + [PID])
tpl.set_editor_property('PieceBone', list(tpl.get_editor_property('PieceBone')) + [unreal.Name(BONE)])
tpl.set_editor_property('PieceOffset', list(tpl.get_editor_property('PieceOffset')) + [OFFSET])
tpl.set_editor_property('AvailMask', tpl.get_editor_property('AvailMask') | BIT)
if has_prop(tpl, 'EmberMinTier'): tpl.set_editor_property('EmberMinTier', 4)
if '--start-owned' in A:
    tpl.set_editor_property('ObsOwned', tpl.get_editor_property('ObsOwned') | BIT)
    tpl.set_editor_property('ObsWorn', tpl.get_editor_property('ObsWorn') | BIT)
BEL.compile_blueprint(hero); EAL.save_loaded_asset(hero)
# read back, because a compile that lost the data must not pass silently
tpl = next((o for o, _ in template_map(hero).values() if o.get_class() == setc), None)
rows = list(tpl.get_editor_property('PieceId')); print('read back: hero rows %d, last id %d, AvailMask %d, ObsOwned %d, ObsWorn %d; class rows %d, AvailMask %d' % (
    len(rows), rows[-1], tpl.get_editor_property('AvailMask'), tpl.get_editor_property('ObsOwned'), tpl.get_editor_property('ObsWorn'),
    len(cdo.get_editor_property('PieceId')), cdo.get_editor_property('AvailMask')))
print('APPLIED + SAVED: %s, %s, BPC_ObsidianSet, hero BP. Play test: README step 4.' % (SM, MI))
