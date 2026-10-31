# #266 (adjustedfilm, 2026-10-31): imports laptop2's antidote icon as /Game/CastleDefender/UI/T_Item_Antidote, the
# texture the APOTHECARY panel draws. UI settings like the other T_Item_ icons: no mips, UserInterface2D, sRGB, alpha.
# Run in the editor:  py "<repo>/handoffs/antidote-266/import_antidote_icon_ue.py" --dry-run   (only reports)
#                     py "<repo>/handoffs/antidote-266/import_antidote_icon_ue.py"             (imports + saves)
# Re-running re-imports the same asset. Touches nothing else.
import os, sys
import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, '..', '..', 'assets', 'laptop2', 'WeaponPack', 'PotionAntidote', 'icon', 'T_Item_Potion_Antidote.png'))
DST, NAME = '/Game/CastleDefender/UI', 'T_Item_Antidote'
DRY = '--dry-run' in sys.argv
EAL = unreal.EditorAssetLibrary

print('[antidote icon] source %s (%s)' % (SRC, 'found' if os.path.isfile(SRC) else 'MISSING'))
print('[antidote icon] target %s/%s (%s)' % (DST, NAME, 'exists, will re-import' if EAL.does_asset_exist(DST + '/' + NAME) else 'new'))
if DRY or not os.path.isfile(SRC):
    print('[antidote icon] dry run, nothing changed' if DRY else '[antidote icon] STOP: source PNG missing (git pull?)')
else:
    t = unreal.AssetImportTask()
    t.filename, t.destination_path, t.destination_name = SRC, DST, NAME
    t.automated, t.replace_existing, t.save = True, True, False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = unreal.load_asset(DST + '/' + NAME)
    tex.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property('srgb', True)
    tex.set_editor_property('never_stream', True)
    EAL.save_asset(DST + '/' + NAME)
    print('[antidote icon] imported and saved %s/%s' % (DST, NAME))
