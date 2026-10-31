# #44 Zombie towers, editor setup (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
#   py "<repo>/handoffs/zombie-towers-44/setup_towers44_ue.py" --dry-run     only reports
#   py "<repo>/handoffs/zombie-towers-44/setup_towers44_ue.py"               makes BP_ZombieTower + BP_TowerDirector
#   py ".../setup_towers44_ue.py" --place [--dry-run]                       after the BPVar + graph pastes: places one TowerDirector
# BP_ZombieTower: Base (box 3 x 3 x 2.4 m, BlockAllDynamic: what bolts, swords and cannonballs hit) + 15 SkeletalMeshComponents
#   Tier00..Tier14 (no collision, hidden; the graph gives each the look of the zombie it absorbs and stacks them 5/4/3/2/1).
import os, sys, unreal

A = sys.argv[1:]
DRY, PLACE = '--dry-run' in A, '--place' in A
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\zombie-towers-44'
DST = '/Game/CastleDefender/Gameplay/Siege'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
SDL = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#44 zombie towers setup' + (' (DRY RUN, nothing written)' if DRY else '')]


def make_bp(name):
    path = DST + '/' + name
    if EAL.does_asset_exist(path): log.append('reusing ' + path); return unreal.load_asset(path)
    log.append('create ' + path)
    if DRY: return None
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
    return AT.create_asset(name, DST, unreal.Blueprint, f)


if PLACE:
    if [a for a in EAS.get_all_level_actors() if a.get_actor_label() == 'TowerDirector']: log.append('TowerDirector already placed')
    else:
        log.append('place TowerDirector at the origin')
        if not DRY:
            cls = unreal.load_class(None, DST + '/BP_TowerDirector.BP_TowerDirector_C')
            act = EAS.spawn_actor_from_class(cls, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)); act.set_actor_label('TowerDirector')
            unreal.EditorLevelLibrary.save_current_level()
else:
    tw = make_bp('BP_ZombieTower')
    if tw:
        hs = SDS.k2_gather_subobject_data_for_blueprint(tw)
        have = {str(SDL.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))) for h in hs}

        def add(name, cls):
            if name in have: return None
            h, fail = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=hs[0], new_class=cls, blueprint_context=tw))
            if not SDL.is_handle_valid(h): raise RuntimeError('%s: %s' % (name, fail))
            SDS.rename_subobject(h, unreal.Text(name)); log.append('  + ' + name)
            return SDL.get_object(SDS.k2_find_subobject_data_from_handle(h))
        bx = add('Base', unreal.BoxComponent)
        if bx:
            bx.set_editor_property('box_extent', unreal.Vector(150, 150, 120)); bx.set_editor_property('relative_location', unreal.Vector(0, 0, 120))
            bx.set_collision_profile_name('BlockAllDynamic'); bx.set_editor_property('component_tags', [unreal.Name('TowerBase')])
        for i in range(15):
            sk = add('Tier%02d' % i, unreal.SkeletalMeshComponent)
            if sk:
                sk.set_collision_profile_name('NoCollision'); sk.set_editor_property('visible', False)
                sk.set_editor_property('component_tags', [unreal.Name('TowerTier')])
        BEL.compile_blueprint(tw); EAL.save_asset(DST + '/BP_ZombieTower')
    td = make_bp('BP_TowerDirector')
    if td: BEL.compile_blueprint(td); EAL.save_asset(DST + '/BP_TowerDirector')
    log.append('Next: README steps 2-4 (BPVar lines, two graph pastes), then --place')
out = '\n'.join(log)
if not DRY: open(os.path.join(HERE, 'setup_towers44.txt'), 'a').write(out + '\n')
unreal.log(out)
