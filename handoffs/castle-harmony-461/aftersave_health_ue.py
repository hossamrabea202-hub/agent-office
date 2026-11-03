# After-save health check (i5, 2026-11-03, roadmap #472 Track L). READ-ONLY: saves nothing, changes nothing. Aborts in PIE.
#   py aftersave_health_ue.py     -> prints a short table + aftersave_health.json next to this file; compares with the last run
# It looks for the regressions that hit us on 11-03 (chat 1228):
#   BP_STATUS    key Blueprints that do not compile
#   SET_COPY     BPC_ObsidianSet class data empty (F3 was the hero's copy saved empty: also check set 3/4 in Play)
#   NO_MESH      visible mesh component without a mesh
#   DEFAULT_MAT  visible component (with instances) on WorldGridMaterial / no material
#   STRETCH      baked / AAA mesh at a non-uniform actor scale (stones stretched, #469)
#   MAT_OVERRIDE baked / AAA mesh whose component material differs from the mesh slot (#301: a stale override hid a new look)
#   HIDDEN_BLOCK hidden piece with collision on: invisible wall for pawns and nav (F10 type)
# NOT covered: gameplay actors that point at hidden pieces (F8 type); Python cannot walk arbitrary BP references. Play test still needed.
# Log errors: node handoffs/aaa-472/log_health.js <CastleDefender.log>
import json, os, unreal
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
    print('PIE RUNNING: abort'); raise SystemExit
HERE = next(h for h in ('C:/Users/hossam.rabea/agent-office/handoffs/castle-harmony-461/', 'C:/Users/hossa/Documents/agent-office/handoffs/castle-harmony-461/') if os.path.isdir(h))
OUT = HERE + 'aftersave_health.json'
G = '/Game/CastleDefender/Gameplay/'
KEY_BPS = ('Castle/BPC_ObsidianSet', 'Castle/BPC_VesnaTrade', 'Castle/BPC_WeaponKit', 'Castle/BPC_ShieldKit', 'Castle/BPC_Muster', 'Castle/BP_SkillTreeHUD',
           'Castle/BP_ZombieHUD', 'Castle/BP_NoticeHUD', 'Tentacle/BPC_TentacleSpit')
BAD = ('BS_ERROR', 'BS_DIRTY', 'BS_UNKNOWN')
R = {k: [] for k in ('BP_STATUS', 'SET_COPY', 'NO_MESH', 'DEFAULT_MAT', 'STRETCH', 'MAT_OVERRIDE', 'HIDDEN_BLOCK')}
notes = []

for p in KEY_BPS:
    bp = unreal.load_asset(G + p)
    if not bp: R['BP_STATUS'].append(p + ': MISSING'); continue
    try:
        s = str(bp.get_editor_property('status')).upper()
        if any(b in s for b in BAD): R['BP_STATUS'].append('%s: %s' % (p, s))
    except Exception as e:
        notes.append('BP status not readable (%s): %s' % (p, e)); break

try:
    cdo = unreal.get_default_object(unreal.load_asset(G + 'Castle/BPC_ObsidianSet').generated_class())
    for n in ('AvailMask', 'PieceId', 'PieceBone', 'PieceOffset'):
        v = cdo.get_editor_property(n)
        if not v: R['SET_COPY'].append('BPC_ObsidianSet.%s is empty on the class' % n)
except Exception as e:
    notes.append('set data not readable: %s' % e)

def baked(m): return '_AAA' in m.get_name() or 'Baked' in m.get_name()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
for a in actors:
    lbl = a.get_actor_label(); ah = a.is_hidden_ed() or a.get_editor_property('hidden')
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_editor_property('static_mesh'); hidden = ah or not c.get_editor_property('visible') or c.get_editor_property('hidden_in_game')
        where = '%s.%s' % (lbl, c.get_name())
        if hidden:
            if m and c.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION: R['HIDDEN_BLOCK'].append(where + ' (%s)' % m.get_name())
            continue
        if isinstance(c, unreal.InstancedStaticMeshComponent) and c.get_instance_count() == 0: continue   # draws nothing (Castle_WallWalk_EMPTY)
        if not m: R['NO_MESH'].append(where); continue
        mats = [c.get_material(i) for i in range(c.get_num_materials())]
        if any(x is None or x.get_name() == 'WorldGridMaterial' for x in mats): R['DEFAULT_MAT'].append(where + ' (%s)' % m.get_name())
        if baked(m):
            s = a.get_actor_scale3d()
            if max(s.x, s.y, s.z) / max(min(s.x, s.y, s.z), 1e-3) > 1.02: R['STRETCH'].append('%s (%s) scale %.2f %.2f %.2f' % (where, m.get_name(), s.x, s.y, s.z))
            for i, x in enumerate(mats):
                y = m.get_material(i)
                if x and y and x != y: R['MAT_OVERRIDE'].append('%s slot %d: %s over mesh %s' % (where, i, x.get_name(), y.get_name()))

old = json.load(open(OUT)) if os.path.exists(OUT) else None
print('AFTER-SAVE HEALTH: %d actors on %s' % (len(actors), unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_name()))
for k, v in R.items():
    was = len(old[k]) if old and k in old else None
    new = [x for x in v if old and x not in old.get(k, [])]
    print('%-13s %4d%s' % (k, len(v), '' if was is None else '  (last run %d, %d new)' % (was, len(new))))
    for x in (new if old else v)[:12]: print('    ', x)
for n in notes: print('NOTE', n)
json.dump(R, open(OUT, 'w'), indent=1)
