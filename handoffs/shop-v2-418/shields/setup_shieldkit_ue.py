# #418 shields, step 1 (TGA). Editor script, safe to re-run. UE 5.8.
#   py "<repo>/handoffs/shop-v2-418/shields/setup_shieldkit_ue.py"
# Before: import the shield meshes  py "<repo>/assets/laptop2/WeaponPack/import_weapons_ue.py" HeaterShield RoundShield
# DRY_RUN = True (default): changes NOTHING, checks the meshes, the hero and the socket, writes setup_shieldkit.txt.
# DRY_RUN = False:
#   1. SG_ShieldKit (SaveGame Blueprint: Owned, Worn) and BPC_ShieldKit (ActorComponent) in /Game/CastleDefender/Gameplay/Castle,
#      with the variables and the shield table defaults from shieldkit_data.json
#   2. hero: adds BPC_ShieldKit as "ShieldKit" and a StaticMeshComponent "OffHand" (tag OffHand) under the hero's Mesh at
#      OFFHAND_SOCKET, hidden, no collision. The grip offsets start at 0: tune GripLoc / GripRot per shield in BPC_ShieldKit's
#      defaults once in the viewport (README step 3), the same way the Obsidian shield was placed.
# Then paste BPC_ShieldKit_graph.txt into BPC_ShieldKit's EventGraph. Nothing existing is edited except adding 2 components to the hero.
import os, json, unreal

DRY_RUN = True
OFFHAND_SOCKET = 'hand_l'        # use the Obsidian shield's socket if it has its own (README step 3)

REPO = r'C:\Users\hossa\Documents\agent-office'
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.join(REPO, 'handoffs', 'shop-v2-418', 'shields')
DIR = '/Game/CastleDefender/Gameplay/Castle'
KIT, SG = DIR + '/BPC_ShieldKit', DIR + '/SG_ShieldKit'
HERO = '/Game/CastleDefender/Gameplay/ThirdPerson/Blueprints/BP_ThirdPersonCharacter'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
D = json.load(open(os.path.join(HERE, 'shieldkit_data.json')))
log = ['DRY_RUN = %s' % DRY_RUN]
missing = []
for s in D['shields']:
    ok = EAL.does_asset_exist(s['mesh']); log.append('%-8s %s  (%s, %d g, block %d %%, x%.2f)' % ('ok' if ok else 'MISSING', s['mesh'], s['name'], s['price'], s['block'] * 100, s['mult']))
    if not ok: missing.append(s['mesh'])
ok = EAL.does_asset_exist(HERO); log.append('%-8s %s' % ('ok' if ok else 'MISSING', HERO))
if not ok: missing.append(HERO)
log.append('existing: BPC_ShieldKit %s, SG_ShieldKit %s' % (EAL.does_asset_exist(KIT), EAL.does_asset_exist(SG)))

def finish(msg):
    out = '#418 shields setup\n' + '\n'.join(log) + '\n' + msg
    open(os.path.join(HERE, 'setup_shieldkit.txt'), 'w').write(out); unreal.log(out)

def var_names(bp, wanted):
    BEL.compile_blueprint(bp); have = set()
    gc = bp.generated_class(); cdo = unreal.get_default_object(gc) if gc else None
    for n in wanted:
        try:
            cdo.get_editor_property(n); have.add(n)
        except Exception:
            pass
    return have

def make_bp(path, parent):
    if EAL.does_asset_exist(path): return unreal.load_asset(path)
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', parent)
    d, n = path.rsplit('/', 1)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(n, d, unreal.Blueprint, f); log.append('created ' + path); return bp

def add_vars(bp, vars_):
    have = var_names(bp, list(vars_))
    for n, t in vars_.items():
        if n not in have:
            if not BEL.add_member_variable(bp, n, t): raise RuntimeError('could not add %s' % n)
            log.append('  + %s.%s' % (bp.get_name(), n))
    BEL.compile_blueprint(bp)

def apply():
    I, Dd, Str = (BEL.get_basic_type_by_name(n) for n in ('int', 'real', 'string'))
    OBJ, ARR = BEL.get_object_reference_type, BEL.get_array_type
    VEC, ROT = BEL.get_struct_type(unreal.Vector.static_struct()), BEL.get_struct_type(unreal.Rotator.static_struct())
    sg = make_bp(SG, unreal.SaveGame); add_vars(sg, {'Owned': I, 'Worn': I}); EAL.save_asset(SG)
    kit = make_bp(KIT, unreal.ActorComponent)
    add_vars(kit, {'Names': ARR(Str), 'Prices': ARR(I), 'BlockChance': ARR(Dd), 'BlockMult': ARR(Dd), 'Meshes': ARR(OBJ(unreal.StaticMesh)),
                   'GripLoc': ARR(VEC), 'GripRot': ARR(ROT), 'Owned': I, 'Worn': I, 'LastMult': Dd, 'OffHand': OBJ(unreal.StaticMeshComponent)})
    cdo = unreal.get_default_object(kit.generated_class())
    sh = D['shields']
    cdo.set_editor_property('Names', [s['name'] for s in sh]); cdo.set_editor_property('Prices', [s['price'] for s in sh])
    cdo.set_editor_property('BlockChance', [s['block'] for s in sh]); cdo.set_editor_property('BlockMult', [s['mult'] for s in sh])
    cdo.set_editor_property('Meshes', [unreal.load_asset(s['mesh']) for s in sh])
    old_loc = list(cdo.get_editor_property('GripLoc')); old_rot = list(cdo.get_editor_property('GripRot'))
    cdo.set_editor_property('GripLoc', (old_loc + [unreal.Vector(0, 0, 0)] * len(sh))[:len(sh)])        # keeps offsets tuned earlier
    cdo.set_editor_property('GripRot', (old_rot + [unreal.Rotator(0, 0, 0)] * len(sh))[:len(sh)])
    cdo.set_editor_property('Worn', -1); cdo.set_editor_property('LastMult', 1.0)
    EAL.save_asset(KIT); log.append('BPC_ShieldKit defaults: %s' % [s['name'] for s in sh])
    hero = unreal.load_asset(HERO)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); SDL = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sds.k2_gather_subobject_data_for_blueprint(hero)
    byname = {str(SDL.get_variable_name(sds.k2_find_subobject_data_from_handle(h))): h for h in handles}
    if 'ShieldKit' not in byname:
        h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=kit.generated_class(), blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add ShieldKit: %s' % fail)
        sds.rename_subobject(h, unreal.Text('ShieldKit')); log.append('hero: added ShieldKit')
    if 'OffHand' not in byname:
        mesh_h = byname.get('Mesh') or byname.get('CharacterMesh0')
        h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=mesh_h, new_class=unreal.StaticMeshComponent, blueprint_context=hero))
        if not fail.is_empty(): raise RuntimeError('add OffHand: %s' % fail)
        sds.rename_subobject(h, unreal.Text('OffHand'))
        c = SDL.get_object(sds.k2_find_subobject_data_from_handle(h))
        c.set_editor_property('component_tags', [unreal.Name('OffHand')]); c.set_editor_property('visible', False)
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); c.set_editor_property('cast_shadow', True)
        try: sds.attach_subobject(mesh_h, h)
        except Exception: pass
        c.set_editor_property('attach_socket_name', unreal.Name(OFFHAND_SOCKET))
        log.append('hero: added OffHand under Mesh at socket %s (hidden, no collision, tag OffHand)' % OFFHAND_SOCKET)
    BEL.compile_blueprint(hero); EAL.save_asset(HERO)
    finish('Next: README shields step 2 (paste BPC_ShieldKit_graph.txt into BPC_ShieldKit, Compile, Save).')

if DRY_RUN:
    finish('DRY RUN only. If nothing above says MISSING, set DRY_RUN = False and run again.' if not missing else 'STOP: MISSING above (import the shields first). Nothing was changed.')
elif missing:
    finish('STOP: MISSING %s. Nothing was changed.' % missing)
else:
    apply()
