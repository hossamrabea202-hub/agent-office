# #501 (i5 for i9): fewer draw calls and less GPU work for the castle, same look.
# Measured on i9 11-04 16:40: render thread 46 ms, GPU 45 ms = the frame. i5's count of the live level: 3,800 mesh components; the 10,100 kit stones are
# already 120 instanced components with Nanite (fine). The separate draws are mostly flat grime / soot cards (1,135 engine Planes, most with one material)
# and ~220 paving cubes; the SiegeKit barricades are 13.5 M triangles without Nanite.
#   py castle_draws_ue.py --report                 groups and counts, changes nothing (default)
#   py castle_draws_ue.py --merge --dry-run        which groups would be merged into how many meshes (opaque / masked only; --include-translucent adds the
#                                                  see-through grime cards, which can sort wrongly inside one mesh: look before you save)
#   py castle_draws_ue.py --merge --apply          merges each group (same mesh + material + folder + 20 m cell, Static, visible) into one new mesh under
#                                                  /Game/CastleDefender/Merged501/, spawns it, HIDES the originals (kept, tagged PreMerge501) - nothing deleted
#   py castle_draws_ue.py --nanite --apply         Nanite on the SiegeKit meshes (assets saved; backup copies in Saved/bak501/)
#   py castle_draws_ue.py --revert                 deletes the merged actors (tag Merged501) and shows the originals again
# Then save the level. Editor idle, not in Play.
import os, re, shutil, sys, unreal
from collections import defaultdict
A = sys.argv[1:]
APPLY = '--apply' in A
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SMES = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
CARD_MESHES = {'Plane', 'Cube'}       # engine basic shapes used as grime cards / paving; merging them keeps the exact look
CELL = 2000.0                         # cm: merged pieces stay small enough for per-piece culling
MIN_GROUP = 4
OUT = '/Game/CastleDefender/Merged501'
NANITE_FOLDERS = ('/Game/CastleDefender/Environment/Boundaries/SiegeKit',)

INCLUDE_SEE_THROUGH = '--include-translucent' in A   # translucent / modulate cards can sort wrongly inside one merged mesh: off unless checked
def see_through(mi):
    if not mi: return False
    base = mi.get_base_material() if hasattr(mi, 'get_base_material') else mi
    return base.get_editor_property('blend_mode') not in (unreal.BlendMode.BLEND_OPAQUE, unreal.BlendMode.BLEND_MASKED)

def single_mesh(a):
    cs = [c for c in a.get_components_by_class(unreal.StaticMeshComponent)]
    return cs[0] if len(cs) == 1 and not isinstance(cs[0], unreal.InstancedStaticMeshComponent) else None

def groups():
    G = defaultdict(list)
    for a in EAS.get_all_level_actors():
        if a.actor_has_tag('PreMerge501') or a.actor_has_tag('Merged501'): continue
        c = single_mesh(a)
        if not c: continue
        m = c.get_editor_property('static_mesh')
        if not m or m.get_name() not in CARD_MESHES: continue
        if c.get_editor_property('mobility') != unreal.ComponentMobility.STATIC: continue
        if a.is_hidden_ed() or c.get_editor_property('hidden_in_game') or not c.is_visible(): continue
        if not (INCLUDE_SEE_THROUGH or all(see_through(c.get_material(i)) is False for i in range(c.get_num_materials()))): continue
        mats = tuple((c.get_material(i).get_path_name() if c.get_material(i) else '') for i in range(c.get_num_materials()))
        p = a.get_actor_location()
        key = (m.get_name(), mats, str(a.get_folder_path()), int(p.x // CELL), int(p.y // CELL), c.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION)
        G[key].append(a)
    return {k: v for k, v in G.items() if len(v) >= MIN_GROUP}

if '--revert' in A:
    gone = shown = 0
    for a in EAS.get_all_level_actors():
        if a.actor_has_tag('Merged501'): EAS.destroy_actor(a); gone += 1
        elif a.actor_has_tag('PreMerge501'):
            a.set_actor_hidden_in_game(False); a.set_actor_enable_collision(True)
            a.tags = [t for t in a.tags if str(t) != 'PreMerge501']; shown += 1
    print('revert: removed %d merged actors, showed %d originals. Save the level.' % (gone, shown)); raise SystemExit

if '--merge' in A:
    G = groups(); n_src = sum(len(v) for v in G.values())
    print('merge: %d groups, %d actors -> %d meshes (saves ~%d draws per pass)' % (len(G), n_src, len(G), n_src - len(G)))
    for k, v in sorted(G.items(), key=lambda kv: -len(kv[1]))[:15]:
        print('   %4d  %s | %s | %s | cell %d,%d | collision %s' % (len(v), k[0], os.path.basename(k[1][0]) if k[1] else '-', k[2][-30:], k[3], k[4], k[5]))
    if not APPLY: print('dry run, nothing changed'); raise SystemExit
    done = 0
    for i, (k, v) in enumerate(sorted(G.items(), key=lambda kv: -len(kv[1]))):
        o = unreal.MergeStaticMeshActorsOptions()
        o.set_editor_property('destroy_source_actors', False)
        o.set_editor_property('spawn_merged_actor', True)
        safe = re.sub(r'[^A-Za-z0-9_]', '_', '%s_%s_%d_%d' % (k[0], os.path.basename(k[1][0]).split('.')[0] if k[1] else 'none', k[3], k[4]))
        o.set_editor_property('base_package_name', '%s/SM_M501_%03d_%s' % (OUT, i, safe[:60]))
        o.set_editor_property('new_actor_label', 'M501_%03d_%s' % (i, safe[:40]))
        ms = o.get_editor_property('mesh_merging_settings')
        ms.set_editor_property('merge_materials', False)          # keep the original materials: identical look
        ms.set_editor_property('merge_physics_data', k[5])        # keep collision where the cards had it
        o.set_editor_property('mesh_merging_settings', ms)
        res = SMES.merge_static_mesh_actors(v, o)
        merged = res[1] if isinstance(res, (tuple, list)) else None
        ok = res[0] if isinstance(res, (tuple, list)) else bool(res)
        if not ok or not merged: print('   group %d failed, originals untouched' % i); continue
        merged.tags = list(merged.tags) + [unreal.Name('Merged501')]
        merged.set_folder_path(unreal.Name('Merged501/' + k[2]))
        for a in v:
            a.set_actor_hidden_in_game(True); a.set_actor_enable_collision(False)
            a.tags = list(a.tags) + [unreal.Name('PreMerge501')]
        done += 1
    print('merged %d of %d groups. Play-check, then save the level (and the new meshes in %s).' % (done, len(G), OUT)); raise SystemExit

if '--nanite' in A:
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    for folder in NANITE_FOLDERS:
        for ad in reg.get_assets_by_path(folder, recursive=True):
            if str(ad.asset_class_path.asset_name) != 'StaticMesh': continue
            m = ad.get_asset(); ns = m.get_editor_property('nanite_settings')
            print('nanite', m.get_name(), 'now', ns.enabled, '| tris', m.get_num_triangles(0))
            if ns.enabled or not APPLY: continue
            src = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_content_dir()) + m.get_path_name().split('.')[0][len('/Game/'):] + '.uasset'
            dst = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'bak501/' + os.path.basename(src)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not os.path.exists(dst): shutil.copy2(src, dst)
            ns.enabled = True; m.set_editor_property('nanite_settings', ns)
            unreal.EditorAssetLibrary.save_loaded_asset(m); print('   Nanite ON, saved (backup %s)' % dst)
    if not APPLY: print('dry run, nothing changed')
    raise SystemExit

# --report (default)
G = defaultdict(lambda: [0, 0, 0])
for a in EAS.get_all_level_actors():
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_editor_property('static_mesh')
        if not m: continue
        f = '/'.join(m.get_path_name().split('/')[:6])
        if isinstance(c, unreal.InstancedStaticMeshComponent): G[f][1] += c.get_instance_count()
        else: G[f][0] += 1
        G[f][2] += 1
print('%-60s %8s %10s' % ('mesh folder', 'separate', 'instances'))
for f, (s, i, _) in sorted(G.items(), key=lambda kv: -kv[1][0])[:20]: print('%-60s %8d %10d' % (f[-60:], s, i))
