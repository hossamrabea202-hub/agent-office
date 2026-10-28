"""Interior torches for the two new front towers: copies the castle's wall-torch set at (700,153.6) (WallTorch_Iron_16,
TorchMount_35, Castle_Torch_01_Flame, Castle_Torch_01_Light, TorchSoot_09) onto the inner drum wall, facing inward."""
import unreal, os, math
D = r'C:\Unreal Backups\Castle Defender\Tools\Tower9_R2'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SRC = ('WallTorch_Iron_16', 'TorchMount_35', 'Castle_Torch_01_Flame', 'Castle_Torch_01_Light', 'TorchSoot_09')
P0 = unreal.Vector(700.0, 153.6, 0.0)          # wall face under the source torch (wall normal +Y)
TORCH_Z = 905.0                                  # source torch mesh z 290.2 -> 905 (floor 680)
acts = eas.get_all_level_actors()
src = {a.get_actor_label(): a for a in acts if a.get_actor_label() in SRC}
drums = {a.get_actor_label(): a for a in acts if a.get_actor_label() in ('Tower9_A_Drum', 'Tower9_B_Drum')}
for a in acts:
    if a.get_actor_label().startswith('Tower9_Torch'): eas.destroy_actor(a)
out = ['src %s' % sorted(src)]
dz = TORCH_Z - src['WallTorch_Iron_16'].get_actor_location().z
for key, (cx, cy, tyaw) in (('A', (50.0, 50.0, 0.0)), ('B', (50.0, 3450.0, -90.0))):
    drum = drums['Tower9_%s_Drum' % key]
    for i, ang_local in enumerate((45.0, 150.0)):
        th = math.radians(ang_local + tyaw)
        # inner wall radius: trace outward from the centre against the drum only
        s = unreal.Vector(cx, cy, TORCH_Z); e = unreal.Vector(cx + 700 * math.cos(th), cy + 700 * math.sin(th), TORCH_Z)
        hits = unreal.SystemLibrary.line_trace_multi(drum, s, e, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, False)
        r_in = None
        for h in hits or []:
            t = h.to_tuple()
            if t[9] == drum:
                r_in = math.hypot(t[4].x - cx, t[4].y - cy); break
        if r_in is None:
            out.append('%s torch %d: no wall hit' % (key, i)); continue
        W = unreal.Vector(cx + r_in * math.cos(th), cy + r_in * math.sin(th), 0.0)
        yaw_rot = math.degrees(th) + 90.0           # source normal +Y (90 deg) -> inward normal (th + 180)
        c, sn = math.cos(math.radians(yaw_rot)), math.sin(math.radians(yaw_rot))
        for lab in SRC:
            a = src[lab]; o = a.get_actor_location()
            rx, ry = o.x - P0.x, o.y - P0.y
            n = eas.duplicate_actor(a)
            z = o.z + dz
            if lab == 'TorchSoot_09':
                z -= 70.0                              # keep the soot card under the 1050 roof-deck soffit
                sc = a.get_actor_scale3d(); n.set_actor_scale3d(unreal.Vector(sc.x * 0.6, sc.y * 0.8, sc.z))
            n.set_actor_location(unreal.Vector(W.x + rx * c - ry * sn, W.y + rx * sn + ry * c, z), False, False)
            n.set_actor_rotation(unreal.MathLibrary.compose_rotators(a.get_actor_rotation(), unreal.Rotator(0, 0, yaw_rot)), False)
            n.set_actor_label('Tower9_Torch_%s%d_%s' % (key, i, lab.split('_')[0] if lab != 'Castle_Torch_01_Flame' else 'Flame'))
            if lab == 'Castle_Torch_01_Light': n.set_actor_label('Tower9_Torch_%s%d_Light' % (key, i))
            n.set_folder_path('Castle/Tower9_%s' % key)
        out.append('%s torch %d at angle %.0f r_in %.1f W (%.0f,%.0f)' % (key, i, ang_local, r_in, W.x, W.y))
out.append('save %s' % unreal.EditorLoadingAndSavingUtils.save_current_level())
open(os.path.join(D, 'torches.txt'), 'w').write('\n'.join(out))
