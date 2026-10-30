# Obsidian set v2, step 1 (checkking, 2026-10-30). Editor script, safe to re-run.
#   py "<repo>/handoffs/obsidian-set-v2/setup_set_v2_ue.py"
# Reads pieces.csv (the piece table) and:
#   1. adds the v2 variables to BPC_ObsidianSet and fills the table defaults (ids, bones, offsets, cover masks, tiers)
#   2. adds one hidden StaticMeshComponent per imported piece mesh to the hero, under KnightMesh, tag ObsK<k>
#      (k = row in the component's table), Overlay Material = M_ObsidianSetAura, no collision
#   3. tags KnightMesh "ObsKnight" and makes M_ObsHidden (masked, opacity 0) for the covered knight slots
#   4. bone offsets: the knight's ref pose is read from a temporary SkeletalMeshActor (no anim = ref pose), deleted after
# A piece whose mesh isn't imported yet is skipped: it is not in AvailMask, so Vesna won't offer it. Import it later
# (its import_*_ue.py), re-run this script, done. Nothing else changes when a piece is added.
# Writes setup_set_v2.txt next to itself.
import csv, os, unreal

REPO = r'C:\Users\hossa\Documents\agent-office'
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.join(REPO, 'handoffs', 'obsidian-set-v2')
ROOT = '/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign'
COMP = '/Game/CastleDefender/Gameplay/Castle/BPC_ObsidianSet'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
KNIGHT = '/Game/ShadowKight/Mesh/ShadowknightUE_SK'
AURA = '/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign/M_ObsidianSetAura'
HIDDEN = '/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign/M_ObsHidden'
KNIGHT_SLOTS = ['arms', 'chest', 'cloth', 'helmet', 'pants']   # ShadowknightUE_SK material slot order (#1 hero README)
TIER_AT = [2, 4, 6, 8, 11]                 # pieces worn for tiers 1..5
TIER_DR = [0.03, 0.06, 0.09, 0.12, 0.15]   # set damage reduction per tier (the hero multiplies by 1 - ObsSet.R * 0.15)

EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
log = []
rows = list(csv.DictReader(open(os.path.join(HERE, 'pieces.csv'), newline='')))

# ---------------------------------------------------------------- 3. hidden material
if not EAL.does_asset_exist(HIDDEN):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    m = tools.create_asset('M_ObsHidden', HIDDEN.rsplit('/', 1)[0], unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    m.set_editor_property('used_with_skeletal_mesh', True)
    c = unreal.MaterialEditingLibrary.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 0)
    c.set_editor_property('r', 0.0)
    unreal.MaterialEditingLibrary.connect_material_property(c, '', unreal.MaterialProperty.MP_OPACITY_MASK)
    unreal.MaterialEditingLibrary.recompile_material(m)
    EAL.save_asset(HIDDEN); log.append('made M_ObsHidden')

# ---------------------------------------------------------------- knight ref pose (temporary actor, deleted below)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tmp = eas.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, -100000))
skc = tmp.skeletal_mesh_component
skc.set_skinned_asset_and_update(unreal.load_asset(KNIGHT)) if hasattr(skc, 'set_skinned_asset_and_update') else skc.set_skeletal_mesh(unreal.load_asset(KNIGHT))
def bone_cs(bone):
    if skc.get_bone_index(bone) < 0: return None
    return skc.get_socket_transform(bone, unreal.RelativeTransformSpace.RTS_COMPONENT)

# ---------------------------------------------------------------- piece table
ids, bones, meshes, offsets = [], [], [], []
avail = 0
cover = [0] * len(KNIGHT_SLOTS)
for r in rows:
    pid = int(r['Id']); bit = 1 << (pid - 10)
    cover[KNIGHT_SLOTS.index(r['KnightSlot'])] |= bit if r['KnightSlot'] != 'chest' else 0   # chest: ArmorMode gate (#52) already hides it
    if pid == 10:
        avail |= bit; continue                      # the cuirass is the existing SK component, worn via Armor.R
    name = 'SM_ObsidianSovereign_%s%s' % (r['Folder'], '_' + r['Side'] if r['Side'] else '')
    path = '%s/%s/%s' % (ROOT, r['Folder'], name)
    if not EAL.does_asset_exist(path):
        log.append('  skip %s (not imported)' % name); continue
    t = bone_cs(r['Bone'])
    if t is None:
        log.append('  ERROR bone %s missing on the knight, %s skipped. Bones: %s' % (r['Bone'], name,
                   ', '.join(str(skc.get_bone_name(i)) for i in range(skc.get_num_bones())))); continue
    ids.append(pid); bones.append(unreal.Name(r['Bone'])); meshes.append(unreal.load_asset(path))
    offsets.append(t.inverse())                     # piece is modelled in knight space: piece-to-bone = inverse(bone-in-knight)
    log.append('  row %d: %s -> %s' % (len(ids) - 1, name, r['Bone']))
# a pair counts as available only when both sides are in
for r in rows:
    pid = int(r['Id'])
    if pid != 10 and pid in ids and ids.count(pid) == (2 if r['Side'] else 1): avail |= 1 << (pid - 10)
eas.destroy_actor(tmp)

# ---------------------------------------------------------------- 1. component variables + defaults
bp = unreal.load_asset(COMP)
I, Dd, NM = BEL.get_basic_type_by_name('int'), BEL.get_basic_type_by_name('real'), BEL.get_basic_type_by_name('name')
Dd.set_editor_property('pin_sub_category', 'double')
ARR = BEL.get_array_type
VARS = {
    'PieceId': ARR(I), 'PieceBone': ARR(NM), 'PieceOffset': ARR(BEL.get_struct_type(unreal.Transform.static_struct())),
    'PieceComps': ARR(BEL.get_object_reference_type(unreal.StaticMeshComponent)),
    'KnightCover': ARR(I), 'KnightMats': ARR(BEL.get_object_reference_type(unreal.MaterialInterface)),
    'HiddenMat': BEL.get_object_reference_type(unreal.MaterialInterface),
    'Knight': BEL.get_object_reference_type(unreal.SkeletalMeshComponent),
    'TierAt': ARR(I), 'TierDR': ARR(Dd), 'Tier': I, 'AvailMask': I, 'WornEff': I, 'LastWorn': I,
}
have = {str(v.get_editor_property('var_name')) for v in bp.get_editor_property('new_variables')}
for n, t in VARS.items():
    if n not in have:
        if not BEL.add_member_variable(bp, n, t): raise RuntimeError('could not add ' + n)
        log.append('  + BPC_ObsidianSet.' + n)
BEL.compile_blueprint(bp)
cdo = unreal.get_default_object(bp.generated_class())
for n, v in (('PieceId', ids), ('PieceBone', bones), ('PieceOffset', offsets), ('KnightCover', cover),
             ('HiddenMat', unreal.load_asset(HIDDEN)), ('TierAt', TIER_AT), ('TierDR', TIER_DR), ('AvailMask', avail), ('LastWorn', -1)):
    cdo.set_editor_property(n, v)
EAL.save_asset(COMP)
log.append('BPC_ObsidianSet: %d piece meshes, AvailMask %d, KnightCover %s' % (len(ids), avail, cover))

# ---------------------------------------------------------------- 2. hero: one hidden component per piece mesh
hero = unreal.load_asset(HERO)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
SDL = unreal.SubobjectDataBlueprintFunctionLibrary
handles = sds.k2_gather_subobject_data_for_blueprint(hero)
byname = {str(SDL.get_variable_name(sds.k2_find_subobject_data_from_handle(h))): h for h in handles}
if 'KnightMesh' not in byname: raise RuntimeError('hero has no KnightMesh component')
kobj = SDL.get_object(sds.k2_find_subobject_data_from_handle(byname['KnightMesh']))
tags = list(kobj.get_editor_property('component_tags'))
if unreal.Name('ObsKnight') not in tags:
    kobj.set_editor_property('component_tags', tags + [unreal.Name('ObsKnight')])
aura = unreal.load_asset(AURA) if EAL.does_asset_exist(AURA) else None
if aura is None: log.append('  WARN M_ObsidianSetAura missing: run handoffs/obsidian-set-bonus-96/make_M_ObsidianSetAura.py, then re-run this')
for k, (pid, mesh) in enumerate(zip(ids, meshes)):
    vname = 'Obs_%s' % mesh.get_name().replace('SM_ObsidianSovereign_', '')
    if vname in byname:
        h = byname[vname]
    else:
        h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=byname['KnightMesh'], new_class=unreal.StaticMeshComponent, blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add %s: %s' % (vname, fail))
        sds.rename_subobject(h, unreal.Text(vname)); log.append('  + hero.' + vname)
    c = SDL.get_object(sds.k2_find_subobject_data_from_handle(h))
    c.set_editor_property('static_mesh', mesh)
    c.set_editor_property('component_tags', [unreal.Name('ObsK%d' % k)])
    c.set_editor_property('visible', False)
    c.set_collision_profile_name('NoCollision')
    c.set_editor_property('generate_overlap_events', False)
    c.set_editor_property('relative_transform', unreal.Transform())   # knight space; the component re-attaches it to the bone at BeginPlay
    if aura: c.set_editor_property('overlay_material', aura)
BEL.compile_blueprint(hero)
EAL.save_asset(HERO)

out = 'Obsidian set v2 setup\n' + '\n'.join(log) + '\nNext: paste BPC_ObsidianSet_v2_graph.txt into BPC_ObsidianSet EventGraph (README step 3).'
open(os.path.join(HERE, 'setup_set_v2.txt'), 'w').write(out)
unreal.log(out)
