# #541 sound: import the WAVs, put sound notifies on the tentacle clips, add the splat to BP_JellyBlob's landing. Editor idle, not in Play.
#   py sfx541_ue.py --dry-run | (no flag: install) | --revert          Needs #534, #535, #538 (all applied).
# Notifies follow the head (socket seg_13). Everything uses one attenuation: full volume to 60 m, gone by 600 m.
import os, sys, unreal
HERE = os.path.dirname(os.path.abspath(__file__)); A = sys.argv[1:] + os.environ.get('ST_ARGS', '').split(); DRY, REV = '--dry-run' in A, '--revert' in A
D_ = '/Game/CastleDefender/Environment/Tentacles/Rig/Style530/'; S_ = D_ + 'Sound'; TRACK = 'SFX541'
SOUNDS = ['SW_TentacleRumble', 'SW_TentacleBurst', 'SW_TentacleRoar', 'SW_TentacleGroan', 'SW_TentacleSpit', 'SW_BlobSplat']
NOTIFY = {'AS_Tentacle_Strike': [(3.2, 'SW_TentacleGroan', 1.0, 1.25)], 'AS_Tentacle_Spit': [(0.02, 'SW_TentacleGroan', 0.7, 1.4), (0.42, 'SW_TentacleSpit', 1.0, 1.0)],
          'AS_Tentacle_Catapult': [(0.3, 'SW_TentacleGroan', 1.0, 0.9), (2.42, 'SW_TentacleRoar', 1.0, 1.1)], 'AS_Tentacle_Enraged': [(1.0, 'SW_TentacleRoar', 0.8, 1.15), (5.7, 'SW_TentacleGroan', 1.0, 1.1)],
          'AS_Tentacle_EnragedHurt': [(1.7, 'SW_TentacleGroan', 1.0, 0.85), (5.1, 'SW_TentacleGroan', 0.8, 0.75)], 'AS_Tentacle_Wounded': [(3.3, 'SW_TentacleGroan', 0.55, 0.7), (15.0, 'SW_TentacleGroan', 0.45, 0.62)]}
EAL, AT, AL = unreal.EditorAssetLibrary, unreal.AssetToolsHelpers.get_asset_tools(), unreal.AnimationLibrary
BEL, PL, GE = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.BlueprintGraphEditor
YB = 15000; BLOB = '/Game/CastleDefender/Gameplay/Tentacle/Jelly/BP_JellyBlob'
def say(*a): print('SFX541', ' '.join(str(x) for x in a))
bp = unreal.load_asset(BLOB); ge = GE.get_graph_editor(BEL.find_event_graph(bp)); n = {x.get_name(): x for x in ge.list_all_nodes()}
if 'CX_26' not in n: raise SystemExit('SFX541 CX_26 missing; BP_JellyBlob changed, send i5 a fresh export')
mine = [x for x in ge.list_all_nodes() if BEL.get_node_pos(x).y >= YB]
in_cx = list(PL.list_connected_pins(BEL.find_execute_pin(n['CX_26'])))
if REV or DRY:
    for clip in NOTIFY:
        a = unreal.load_asset(D_ + clip)
        if a is None: say('no clip', clip); continue
        if DRY: say('would add', len(NOTIFY[clip]), 'notifies on', clip)
        else: AL.remove_animation_notify_events_by_track(a, TRACK); EAL.save_loaded_asset(a); say('notifies removed', clip)
    if REV and mine:
        prev = [PL.get_owning_node(p) for p in PL.list_connected_pins(BEL.find_execute_pin(mine[0]))]; ge.remove_nodes(mine)
        for q in prev: say('relink', PL.try_create_connection(BEL.find_then_pin(q), BEL.find_execute_pin(n['CX_26'])))
        say('compile', BEL.compile_blueprint(bp)); say('saved', EAL.save_asset(BLOB, only_if_is_dirty=False))
    if DRY: say('would import', SOUNDS, 'and add the splat to BP_JellyBlob, already there:', bool(mine))
    say('DONE', 'dry-run' if DRY else 'revert'); raise SystemExit(0)
att_path = S_ + '/ATT_Tentacle541'
for s in SOUNDS:
    f = os.path.join(HERE, 'sound', s + '.wav')
    if not os.path.exists(f): raise SystemExit('SFX541 missing WAV (git pull?): ' + f)
    t = unreal.AssetImportTask(); t.filename = f; t.destination_path = S_; t.destination_name = s; t.automated = True; t.replace_existing = True; t.save = True; AT.import_asset_tasks([t])
    if not EAL.does_asset_exist(S_ + '/' + s): raise SystemExit('SFX541 import failed: ' + s)
if not EAL.does_asset_exist(att_path):
    at = AT.create_asset('ATT_Tentacle541', S_, unreal.SoundAttenuation, unreal.SoundAttenuationFactory())
    st = at.get_editor_property('attenuation'); st.set_editor_property('falloff_distance', 54000.0); ex = st.get_editor_property('attenuation_shape_extents'); ex.x = 6000.0; st.set_editor_property('attenuation_shape_extents', ex); at.set_editor_property('attenuation', st); EAL.save_loaded_asset(at)
att = unreal.load_asset(att_path)
for s in SOUNDS:
    w = unreal.load_asset(S_ + '/' + s); w.set_editor_property('attenuation_settings', att); EAL.save_loaded_asset(w)
for clip, items in NOTIFY.items():
    a = unreal.load_asset(D_ + clip)
    if a is None: say('SKIP no clip', clip); continue
    AL.remove_animation_notify_events_by_track(a, TRACK)
    if not AL.is_valid_anim_notify_track_name(a, TRACK): AL.add_animation_notify_track(a, TRACK)
    for tm, snd, vol, pit in items:
        nt = AL.add_animation_notify_event(a, TRACK, tm, unreal.AnimNotify_PlaySound)
        nt.set_editor_property('sound', unreal.load_asset(S_ + '/' + snd)); nt.set_editor_property('volume_multiplier', vol); nt.set_editor_property('pitch_multiplier', pit); nt.set_editor_property('follow', True); nt.set_editor_property('attach_name', 'seg_13')
    EAL.save_loaded_asset(a); say(clip, 'notifies', [str(x.get_editor_property('notify_name')) for x in AL.get_animation_notify_events(a)].__len__())
if mine: say('splat already wired')
else:
    prev = [PL.get_owning_node(p) for p in in_cx if BEL.get_node_pos(PL.get_owning_node(p)).y >= 12000 and 'IfThenElse' not in PL.get_owning_node(p).get_name()]
    if len(prev) != 1: raise SystemExit('SFX541 expected one landing node before CX_26, found %d; was #535 applied?' % len(prev))
    M = '/Script/Engine.KismetMathLibrary:'; pl = ge.add_call_function_node('/Script/Engine.GameplayStatics:PlaySoundAtLocation'); BEL.set_node_pos(pl, unreal.IntPoint(0, YB)); PL.set_pin_value(BEL.find_input_pin(pl, 'Sound'), unreal.load_asset(S_ + '/SW_BlobSplat').get_path_name())
    lc = ge.add_call_function_node('/Script/Engine.Actor:K2_GetActorLocation'); BEL.set_node_pos(lc, unreal.IntPoint(300, YB)); rp = ge.add_call_function_node(M + 'RandomFloatInRange'); BEL.set_node_pos(rp, unreal.IntPoint(600, YB)); PL.set_pin_value(BEL.find_input_pin(rp, 'Min'), '0.85'); PL.set_pin_value(BEL.find_input_pin(rp, 'Max'), '1.15')
    PL.try_create_connection(BEL.find_output_pin(lc, 'ReturnValue'), BEL.find_input_pin(pl, 'Location')); PL.try_create_connection(BEL.find_output_pin(rp, 'ReturnValue'), BEL.find_input_pin(pl, 'PitchMultiplier'))
    q = prev[0]; PL.break_pin_links(BEL.find_then_pin(q)); say('links', PL.try_create_connection(BEL.find_then_pin(q), BEL.find_execute_pin(pl)), PL.try_create_connection(BEL.find_then_pin(pl), BEL.find_execute_pin(n['CX_26'])))
    BEL.compile_blueprint(bp); say('errors', sorted(x.get_name() for x in ge.list_nodes_with_errors())); say('saved', EAL.save_asset(BLOB, only_if_is_dirty=False))
say('DONE install')
