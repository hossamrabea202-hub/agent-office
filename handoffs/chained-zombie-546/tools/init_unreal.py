# GUI lab: install into a fresh folder, Simulate on the empty Entry map, drive the actor by real ApplyDamage, log numbers, capture stills, quit.
import unreal, os, json, runpy, traceback, sys
ROOT = os.environ['CH_ROOT']; OUT = 'C:/Users/hossam.rabea/ckw/ztools/ch_sim/out'; os.makedirs(OUT, exist_ok=True)
log = open(OUT + '/sim_%s.txt' % ROOT.split('/')[-1], 'w')
def P(*a):
    s = ' '.join(str(x) for x in a); log.write(s + '\n'); log.flush(); print('CHSIM', s)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); ES = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
st = {'stage': 0, 't': 0.0, 'a': None}
CAP = os.environ.get('CH_CAP', '1') == '1'
def world(): return UES.get_game_world()
def report(tag):
    a = st['a']; w = world(); now = unreal.GameplayStatics.get_time_seconds(w); g = lambda k: a.get_editor_property(k)
    c = {x.get_name(): x for x in a.get_components_by_class(unreal.StaticMeshComponent)}; lp = [c['L%02d' % i].get_world_location() for i in range(24)]
    gap = [(lp[i + 1] - lp[i]).length() for i in (7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 19, 20, 21, 22)]
    m = a.get_components_by_class(unreal.SkeletalMeshComponent)[0]; ai = m.get_anim_instance(); cur = None
    try: cur = ai.get_current_active_montage().get_name() if ai and ai.get_current_active_montage() else None
    except Exception as e: cur = 'err %s' % e
    wr = m.get_socket_location('LeftHand'); cf = c['Cuff0'].get_world_location()
    P(tag, 't %.2f' % now, 'State', g('State'), 'side', g('FreeSide'), 'montage', cur, 'MeltT %.3f' % g('MeltTv'), 'gap cm %.1f..%.1f' % (min(gap), max(gap)), 'L0', [round(lp[0].x), round(lp[0].y), round(lp[0].z)], 'L6', [round(lp[6].x), round(lp[6].y), round(lp[6].z)], 'L13', [round(lp[13].x), round(lp[13].y), round(lp[13].z)], 'wristL', [round(wr.x), round(wr.y), round(wr.z)], 'cuff0', [round(cf.x), round(cf.y), round(cf.z)], 'modes', list(g('ModeA')), 'Anch0', [round(v) for v in (lambda q: (q.x, q.y, q.z))(g('Anch')[0])] if len(g('Anch')) else 'EMPTY', 'links', len(g('LinksArr')), 'ticks', a.is_actor_tick_enabled() if hasattr(a, 'is_actor_tick_enabled') else '?', 'SegE', str(g('SegE')).split('{')[-1][:40], 'Now %.2f' % g('Now'))
def shot(name):
    if not CAP: return
    w = world(); cap = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.SceneCapture2D)[0]
    rt = unreal.RenderingLibrary.create_render_target2d(w, 800, 450, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    cc = cap.capture_component2d; cc.set_editor_property('texture_target', rt); cc.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR); cc.set_editor_property('capture_every_frame', False); cc.set_editor_property('fov_angle', 42.0)
    pp = cc.get_editor_property('post_process_settings'); pp.set_editor_property('override_auto_exposure_method', True); pp.set_editor_property('auto_exposure_method', unreal.AutoExposureMethod.AEM_MANUAL); pp.set_editor_property('override_auto_exposure_apply_physical_camera_exposure', True); pp.set_editor_property('auto_exposure_apply_physical_camera_exposure', False); pp.set_editor_property('override_auto_exposure_bias', True); pp.set_editor_property('auto_exposure_bias', 0.0); cc.set_editor_property('post_process_settings', pp); cc.set_editor_property('post_process_blend_weight', 1.0)
    cc.capture_scene(); unreal.RenderingLibrary.export_render_target(w, rt, OUT, '%s_%s.png' % (ROOT.split('/')[-1], name)); P('shot', name)
PLAN = [(2.0, 'R', 'thrash'), (3.0, 'S', 'thrash_a'), (4.3, 'R', 'thrash2'), (4.5, 'S', 'thrash_b'), (5.0, 'D', 'SLICE'), (5.3, 'R', 'cut_0.3'), (5.4, 'S', 'cut_a'), (6.2, 'R', 'cut_1.2'), (7.5, 'R', 'free'), (7.6, 'S', 'free_a'), (9.5, 'S', 'free_b'), (10.0, 'D', 'KILL'), (10.3, 'R', 'kill_0.3'),
        (11.5, 'S', 'melt_15'), (12.0, 'R', 'melt_a'), (13.5, 'S', 'melt_40'), (14.0, 'R', 'melt_b'), (15.2, 'S', 'melt_60'), (16.5, 'S', 'melt_75'), (17.0, 'R', 'melt_c'), (17.9, 'S', 'melt_90'), (19.5, 'R', 'done'), (20.0, 'S', 'after'), (21.0, 'D', 'EXTRA_HIT'), (21.5, 'R', 'end')]
def tick(dt):
    try:
        s = st['stage']
        if s == 0:
            st['t'] += dt
            if st['t'] < 3: return
            st['stage'] = 1; st['t'] = 0
            cls = unreal.load_asset(ROOT + '/BP_ChainedZombie').generated_class()
            ES.spawn_actor_from_class(cls, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 180))
            def box(loc, sc):
                b = ES.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc)); b.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube')); b.set_actor_scale3d(unreal.Vector(*sc))
            box((0, 0, -25), (12, 12, 0.5)); box((70, 0, 200), (0.4, 8, 4))        # floor; the wall behind him (actor at yaw 180, wall at +50)
            l = ES.spawn_actor_from_class(unreal.PointLight, unreal.Vector(-200, -60, 300)); l.point_light_component.set_editor_property('intensity', 40.0); l.point_light_component.set_editor_property('attenuation_radius', 1500.0)
            sky = ES.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 800)); sky.light_component.set_editor_property('intensity', 0.03)
            cam = unreal.Vector(-430, -200, 150); ES.spawn_actor_from_class(unreal.SceneCapture2D, cam, unreal.MathLibrary.find_look_at_rotation(cam, unreal.Vector(0, 0, 105)))
            LES.editor_play_simulate(); P('simulate requested'); return
        if s == 1:
            if not world(): return
            for x in unreal.GameplayStatics.get_all_actors_of_class(world(), unreal.Pawn):
                if 'ChainedZombie' in x.get_class().get_name(): st['a'] = x
            if not st['a']: return
            st['stage'] = 2; st['t'] = 0; P('actor in world', st['a'].get_name()); return
        if s == 2:
            st['t'] = unreal.GameplayStatics.get_time_seconds(world())
            while PLAN and st['t'] >= PLAN[0][0]:
                _, k, n = PLAN.pop(0)
                if k == 'R': report(n)
                elif k == 'S': shot(n)
                elif k == 'D': P('damage', n, unreal.GameplayStatics.apply_damage(st['a'], 35.0, None, None, unreal.DamageType))
            if not PLAN:
                st['stage'] = 3; st['t'] = 0; LES.editor_request_end_play(); P('END OK')
            return
        if s == 3:
            st['t'] += dt
            if st['t'] > 4 or not world(): st['stage'] = 4; unreal.SystemLibrary.quit_editor()
    except Exception:
        P('EXC', traceback.format_exc()); st['stage'] = 4; unreal.SystemLibrary.quit_editor()
unreal.register_slate_post_tick_callback(tick)
