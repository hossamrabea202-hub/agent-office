# #58 cannon break stages, step 2 (i5 core, 2026-11-01). UE 5.8 Python.
#   py ".../import_break58_ue.py" --dry-run   report BPC_CannonBreak.StageMeshes and the FBX files
#   py ".../import_break58_ue.py"             import out/SM_FieldCannon_HD_Break1-3.fbx next to the cannon (no new materials:
#                                             the cannon's Metal / Wood are assigned by slot name), fill StageMeshes
#                                             (backup BPC_CannonBreak_BACKUP58 first), compile, save
import os, sys, unreal
DRY = '--dry-run' in sys.argv
EAL, BEL = unreal.EditorAssetLibrary, unreal.BlueprintEditorLibrary
OUT = 'C:/Users/hossam.rabea/agent-office/handoffs/cannon-break-58/i5/out'
DST = '/Game/CastleDefender/AssetPacks/Fab/Old_Field_Cannon/Break'
SRC = '/Game/CastleDefender/AssetPacks/Fab/Old_Field_Cannon'
BPC = '/Game/CastleDefender/Gameplay/Cannon/BPC_CannonBreak'
bp = unreal.load_asset(BPC)
cdo = unreal.get_default_object(BEL.generated_class(bp))
log = ['#58 import' + (' (DRY RUN)' if DRY else ''), 'StageMeshes now: %s' % [m.get_name() if m else None for m in cdo.get_editor_property('StageMeshes')]]
fbx = ['%s/SM_FieldCannon_HD_Break%d.fbx' % (OUT, i) for i in (1, 2, 3)]
log += ['%s %s' % (os.path.basename(f), 'ok' if os.path.exists(f) else 'MISSING') for f in fbx]
if not DRY:
    if not EAL.does_asset_exist(BPC + '_BACKUP58'): EAL.duplicate_asset(BPC, BPC + '_BACKUP58'); EAL.save_asset(BPC + '_BACKUP58')
    mats = {'Metal': unreal.load_asset(SRC + '/Metal'), 'Wood': unreal.load_asset(SRC + '/Wood')}
    tasks = []
    for f in fbx:
        if EAL.does_asset_exist('%s/%s' % (DST, os.path.basename(f)[:-4])): continue   # already imported (re-run after a crash)
        t = unreal.AssetImportTask(); t.filename = f; t.destination_path = DST; t.automated = True; t.save = False; t.replace_existing = True
        o = unreal.FbxImportUI(); o.import_materials = False; o.import_textures = False; o.import_as_skeletal = False
        o.static_mesh_import_data.combine_meshes = True; o.static_mesh_import_data.auto_generate_collision = True
        t.options = o; tasks.append(t)
    if tasks: unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    meshes = []
    for i in (1, 2, 3):
        p = '%s/SM_FieldCannon_HD_Break%d' % (DST, i)
        m = unreal.load_asset(p)
        sm = list(m.static_materials)
        for k, s in enumerate(sm):
            nm = str(s.material_slot_name)
            mi = next((v for key, v in mats.items() if key.lower() in nm.lower()), None)
            if mi: m.set_material(k, mi)
        EAL.save_asset(p); meshes.append(m)
        log.append('%s: slots %s' % (m.get_name(), [str(s.material_slot_name) for s in m.static_materials]))
    cdo.set_editor_property('StageMeshes', meshes)
    # no compile here: compiling right after the import crashed UE 5.8 on i5 (UObjectAnnotation assert, 2026-11-01);
    # a default-value change needs no recompile, the package is saved as is
    bp.modify(); EAL.save_asset(BPC, only_if_is_dirty=False)
    log.append('StageMeshes = %s' % [m.get_name() for m in cdo.get_editor_property('StageMeshes')])
print('\n'.join(log))
