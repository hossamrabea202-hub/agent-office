# #297 part 4: stand-in miners in the mine dungeon (adjustedfilm, 2026-10-31). UE 5.3 Python, safe to re-run.
# Owner #297: "...underground dungeons where we see the mine and the tunnels and workers". Characters stay stand-ins until
# the MetaHuman pass (owner rule), so a miner = the soldier's own body setup (from the Master's soldier_components.txt):
#   Body   SkeletalMesh SKM_Quinn_Simple, hidden, single-node anim (a looping swing / idle), always ticks its pose
#   Knight SkeletalMesh ShadowknightUE_SK + ABP_KnightFollow, child of Body (it retargets from its attached parent,
#          exactly like the soldiers)
#   Pick / Helmet / Satchel  TGA's #247 MinerGear on Body sockets hand_r / head / spine_03 (README offsets)
#   Candle PointLight on the helmet, warm 120 lm, 250 cm (KB rule 6: a real light behind the emissive flame)
# No AI, no collision except the capsule-free mesh: they work, they don't fight.
#   py "<repo>/handoffs/cave-296-297/mine_workers297_ue.py" --dry-run
#   py "<repo>/handoffs/cave-296-297/mine_workers297_ue.py"           makes BP_MineWorker, places 3 (tag Mine297)
# Needs place_mine297_ue.py run first (it finds the dungeon by the Mine297_Chamber_00 actor). Undo: place_mine297 --remove.
import os, sys, unreal

DRY = '--dry-run' in sys.argv
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = r'C:\Users\hossa\Documents\agent-office\handoffs\cave-296-297'
BPP = '/Game/CastleDefender/Characters/NPC/BP_MineWorker'
Q = '/Game/CastleDefender/Characters/Mannequins/Mannequins/Meshes/SKM_Quinn_Simple'
KN, KABP = '/Game/ShadowKight/Mesh/ShadowknightUE_SK', '/Game/CastleDefender/Characters/Knight/ABP_KnightFollow'
GEAR = '/Game/CastleDefender/Characters/NPC/MinerGear'
SWING = '/Game/CastleDefender/Gameplay/Castle/Combat/AM_Slash1'           # overhead-ish swing: the pick stroke stand-in
IDLE = '/Game/CastleDefender/Characters/Mannequins/Mannequins/Animations/Quinn/MF_Idle'
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
log = ['#297 part 4 mine workers' + (' (DRY RUN, nothing written)' if DRY else '')]


def seq_of(path):
    """the AnimSequence inside a montage (single-node mode plays sequences most reliably); else the asset itself"""
    a = unreal.load_asset(path)
    if isinstance(a, unreal.AnimMontage):
        try:
            seg = a.get_editor_property('slot_anim_tracks')[0].get_editor_property('anim_track').get_editor_property('anim_segments')[0]
            s = seg.get_editor_property('anim_reference')
            if s: return s
        except Exception as e: log.append('  montage %s: inner sequence not readable (%s), playing the montage' % (path.split('/')[-1], e))
    return a


missing = [p for p in (Q, KN, KABP, SWING, IDLE) if not EAL.does_asset_exist(p)]
if missing: raise SystemExit('missing ' + ', '.join(missing))
gear = {n: GEAR + '/' + n for n in ('SM_MinerPick', 'SM_MinerHelmet', 'SM_MinerSatchel')}
have_gear = all(EAL.does_asset_exist(p) for p in gear.values())
log.append('MinerGear %s' % ('found' if have_gear else 'NOT imported yet (run assets/tga/MinerGear/import_minergear_ue.py, then re-run this)'))
ch = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == 'Mine297_Chamber_00']
if not ch: raise SystemExit('run place_mine297_ue.py first (no Mine297_Chamber_00)')
O = ch[0].get_actor_location()
swing, idle = seq_of(SWING), seq_of(IDLE)
log.append('swing anim %s, idle anim %s' % (swing.get_name(), idle.get_name()))


def comps(bp):
    return {str(LIB.get_variable_name(SDS.k2_find_subobject_data_from_handle(h))): h for h in SDS.k2_gather_subobject_data_for_blueprint(bp)}


def add(bp, cls, name, parent):
    have = comps(bp)
    if name in have: return LIB.get_object(SDS.k2_find_subobject_data_from_handle(have[name]))
    h, why = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=parent, new_class=cls, blueprint_context=bp))
    if not LIB.is_handle_valid(h): raise RuntimeError('%s: %s' % (name, why))
    SDS.rename_subobject(h, unreal.Text(name)); return LIB.get_object(SDS.k2_find_subobject_data_from_handle(h))


if not DRY:
    bp = unreal.load_asset(BPP) if EAL.does_asset_exist(BPP) else None
    if not bp:
        f = unreal.BlueprintFactory(); f.set_editor_property('parent_class', unreal.Actor)
        bp = AT.create_asset('BP_MineWorker', BPP.rsplit('/', 1)[0], unreal.Blueprint, f); log.append('create ' + BPP)
    root = SDS.k2_gather_subobject_data_for_blueprint(bp)[0]
    body = add(bp, unreal.SkeletalMeshComponent, 'Body', root)
    body.set_editor_property('skeletal_mesh', unreal.load_asset(Q))
    body.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    pd = unreal.SingleAnimationPlayData(); pd.set_editor_property('anim_to_play', swing); pd.set_editor_property('saved_looping', True)
    pd.set_editor_property('saved_playing', True); pd.set_editor_property('saved_play_rate', 0.7)
    body.set_editor_property('animation_data', pd)
    body.set_editor_property('hidden_in_game', True); body.set_editor_property('visible', False)
    body.set_editor_property('visibility_based_anim_tick_option', unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    body.set_collision_profile_name('NoCollision')
    bh = comps(bp)['Body']
    knight = add(bp, unreal.SkeletalMeshComponent, 'Knight', bh)
    knight.set_editor_property('skeletal_mesh', unreal.load_asset(KN))
    knight.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_BLUEPRINT)
    knight.set_editor_property('anim_class', unreal.load_class(None, KABP + '.ABP_KnightFollow_C'))
    knight.set_collision_profile_name('NoCollision')
    if have_gear:
        for n, sock in (('SM_MinerPick', 'hand_r'), ('SM_MinerHelmet', 'head'), ('SM_MinerSatchel', 'spine_03')):
            c = add(bp, unreal.StaticMeshComponent, n[2:], bh)
            c.set_editor_property('static_mesh', unreal.load_asset(gear[n])); c.set_collision_profile_name('NoCollision')
            c.set_editor_property('attach_socket_name', sock)
            if n == 'SM_MinerHelmet': c.set_editor_property('relative_location', unreal.Vector(0, 0, 9))
        cand = add(bp, unreal.PointLightComponent, 'Candle', comps(bp)['MinerHelmet'])
        cand.set_editor_property('intensity_units', unreal.LightUnits.LUMENS); cand.set_editor_property('intensity', 120.0)
        cand.set_editor_property('light_color', unreal.Color(r=255, g=158, b=77, a=255)); cand.set_editor_property('attenuation_radius', 250.0)
        cand.set_editor_property('source_radius', 1.0); cand.set_editor_property('relative_location', unreal.Vector(0, -12, 8))
    BEL.compile_blueprint(bp); EAL.save_asset(BPP)
    log.append('BP_MineWorker: Body (hidden, swing loop), Knight, %s' % ('gear + candle' if have_gear else 'no gear yet'))

# 3 miners (dungeon-relative cm, yaw): two at the ore veins (facing them), one resting by the cart
SPOTS = [((650, 385, 0), 90, swing, 0.0), ((375, 382, 0), 100, swing, 0.45), ((850, -150, 0), 0, idle, 0.0)]
for i, (p, yaw, anim, start) in enumerate(SPOTS):
    loc = O + unreal.Vector(*p)
    log.append('  Mine297_Worker_%d %s yaw %d (%s)' % (i, loc, yaw, anim.get_name()))
    if DRY: continue
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == 'Mine297_Worker_%d' % i: EAS.destroy_actor(a)
    w = EAS.spawn_actor_from_class(unreal.load_class(None, BPP + '.BP_MineWorker_C'), loc, unreal.Rotator(0, 0, yaw))
    w.set_actor_label('Mine297_Worker_%d' % i); w.tags = [unreal.Name('Mine297')]
    b = [c for c in w.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name().startswith('Body')]
    if b:
        pd = unreal.SingleAnimationPlayData(); pd.set_editor_property('anim_to_play', anim); pd.set_editor_property('saved_looping', True)
        pd.set_editor_property('saved_playing', True); pd.set_editor_property('saved_play_rate', 0.62 + 0.08 * i); pd.set_editor_property('saved_position', start)
        b[0].set_editor_property('animation_data', pd)       # each miner its own rhythm, so they don't swing in step
if not DRY: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()

out = '\n'.join(log)
if not DRY: open(os.path.join(HERE, 'mine_workers297.txt'), 'w').write(out)
unreal.log(out); print(out)
