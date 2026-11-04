# #472 (i5): the crowd meshes have ONE LOD: 85 zombies draw 7447 verts each at any distance, in every shadow pass (soldiers 37575, brutes 33724). Adds 3 generated LODs with the engine's reducer.
# Run the FPS sweep first (wave_sweep_ue.py), so there is a before number. Editor idle, not in Play.
#   py crowd_lods_ue.py --dry-run | --apply        (--only SK_Zombie,SK_FleshBrute to limit; --test <folder>: i5 works on copies there)
# Revert: --apply copies each .uasset to Saved/bak472/ first. Close the editor, copy back over Content/... (drop .lods), reopen.
import os, shutil, sys, unreal
A = sys.argv[1:]
MESHES = ['/Game/CastleDefender/Characters/Enemies/Zombie/SK_Zombie', '/Game/CastleDefender/Characters/Enemies/FleshBrute/SK_FleshBrute', '/Game/ShadowKight/Mesh/ShadowknightUE_SK']
if '--only' in A: MESHES = [m for m in MESHES if m.split('/')[-1] in A[A.index('--only') + 1].split(',')]
if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(): raise SystemExit('Play is running: stop it first')
SS, E = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem), unreal.EditorAssetLibrary
TEST = A[A.index('--test') + 1] if '--test' in A else None
for p in MESHES:
    if TEST:
        d = TEST + '/' + p.split('/')[-1]
        if not E.does_asset_exist(d): E.duplicate_asset(p, d)
        p = d
    sk = unreal.load_asset(p); n = SS.get_lod_count(sk); verts = [SS.get_num_verts(sk, i) for i in range(n)]
    if n > 1: print('there ', p, n, 'LODs', verts); continue
    if '--apply' not in A: print('WOULD add 3 LODs to', p, 'now', verts); continue
    if not TEST:
        src = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_content_dir()) + p[len('/Game/'):] + '.uasset'
        dst = unreal.SystemLibrary.convert_to_absolute_path(unreal.Paths.project_saved_dir()) + 'bak472/' + os.path.basename(src) + '.lods'
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst): shutil.copy2(src, dst); print('backup', dst)
    ok = SS.regenerate_lod(sk, 4, True, False); n = SS.get_lod_count(sk)
    print('LODs', ok, n, [SS.get_num_verts(sk, i) for i in range(n)], 'sections', [SS.get_num_sections(sk, i) for i in range(n)], p.split('/')[-1])
    if ok and n == 4 and not TEST: print('saved', E.save_asset(p, only_if_is_dirty=False))
