# MASTER ONLY (UE 5.3). Two steps in one script, both idempotent:
#  A. Creates /Game/CastleDefender/Realm/BP_RealmGate (parent Actor) with one component, 'Prompt' (TextRenderComponent,
#     "E  Open", 1.2 m up, hidden until the player is in range), added with SubobjectDataSubsystem.
#  B. If the BP already has its variables + graph pasted (README steps 2-3) and the level has laptop2's Realm_Gate_*
#     actors (#169 stage 1), it spawns 'Realm_Gate_BP' at Realm_Gate_Trigger and wires LeafL / LeafR / Bar, their base yaw
#     and the bar's rest location. Run it once before pasting (A) and once after (B). Save the level afterwards.
#   py "<repo>/handoffs/tga-realmgate-bp/create_realmgate_bp_ue.py"
import unreal
DST, NAME = '/Game/CastleDefender/Realm', 'BP_RealmGate'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
path = DST + '/' + NAME
if not EAL.does_asset_exist(path):
    f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, DST, unreal.Blueprint, f)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    root = sds.k2_gather_subobject_data_for_blueprint(bp)[0]
    h, reason = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.TextRenderComponent, blueprint_context=bp))
    if not unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(h): raise RuntimeError('Adding Prompt failed: %s' % reason)
    sds.rename_subobject(h, unreal.Text('Prompt'))
    tr = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(sds.k2_find_subobject_data_from_handle(h))
    tr.set_editor_property('text', unreal.Text('E  Open')); tr.set_editor_property('world_size', 34.0)
    try: tr.set_editor_property('horizontal_alignment', unreal.HorizTextAligment.EHTA_CENTER)   # engine enum spelling
    except Exception: pass
    tr.set_editor_property('text_render_color', unreal.Color(150, 220, 255, 255))
    tr.set_editor_property('relative_location', unreal.Vector(0, 0, 120)); tr.set_editor_property('visible', False)
    BEL.compile_blueprint(bp); EAL.save_loaded_asset(bp)
    unreal.log('Created %s with a Prompt component. Paste BP_RealmGate_vars.txt (line by line) + the EventGraph, compile, then run this script again.' % path)
else:
    bp = unreal.load_asset(path); cls = bp.generated_class()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); acts = {a.get_actor_label(): a for a in eas.get_all_level_actors()}
    need = ('Realm_Gate_LeafL', 'Realm_Gate_LeafR', 'Realm_Gate_Bar', 'Realm_Gate_Trigger')
    missing = [n for n in need if n not in acts]
    if missing: raise RuntimeError('Level is missing %s: run laptop2 place_realm_ue.py (#169 stage 1) first' % missing)
    if 'Realm_Gate_BP' in acts: eas.destroy_actor(acts['Realm_Gate_BP'])
    g = eas.spawn_actor_from_class(cls, acts['Realm_Gate_Trigger'].get_actor_location(), unreal.Rotator(0, 0, 0))
    g.set_actor_label('Realm_Gate_BP'); g.set_folder_path('Gameplay/Realm')
    def put(name, value):
        for p in (name, ''.join('_' + c.lower() if c.isupper() else c for c in name).lstrip('_')):
            try: g.set_editor_property(p, value); return
            except Exception: pass
        raise RuntimeError('BP_RealmGate has no variable %s: paste BP_RealmGate_vars.txt first' % name)
    L, R, B = acts['Realm_Gate_LeafL'], acts['Realm_Gate_LeafR'], acts['Realm_Gate_Bar']
    put('LeafL', L); put('LeafR', R); put('Bar', B)
    put('BaseYawL', L.get_actor_rotation().yaw); put('BaseYawR', R.get_actor_rotation().yaw); put('BarBase', B.get_actor_location())
    unreal.log('Realm_Gate_BP placed at Realm_Gate_Trigger and wired to the leaves + bar. If the leaves swing the wrong way, set SwingSign = -1 on it. Save the level.')
