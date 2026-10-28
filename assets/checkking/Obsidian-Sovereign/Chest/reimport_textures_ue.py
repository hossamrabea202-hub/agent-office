# Obsidian Sovereign chest v2 textures (#64): re-import ONLY the 3 textures over the existing ones.
# Run in the editor:  py "<repo>/assets/checkking/Obsidian-Sovereign/Chest/reimport_textures_ue.py"
# Touches nothing else: not SM_/SK_ObsidianSovereign_Chest (fitted + skinned by the Vice), not the materials.
# Same UV layout as the shipped bake (checked: max UV difference 0.0), so MI_ObsidianSovereign_Chest picks them up as is.
import os
import unreal

SRC = os.path.dirname(os.path.abspath(__file__))
DST = '/Game/CastleDefender/Characters/Hero/Armor/ObsidianSovereign/Chest'
EAL = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

def task(path, dest):
    t = unreal.AssetImportTask()
    t.filename = path; t.destination_path = dest; t.automated = True; t.save = True; t.replace_existing = True
    return t

tex = {
    'T_ObsidianSovereign_Chest_BaseColor': (True, unreal.TextureCompressionSettings.TC_DEFAULT),
    'T_ObsidianSovereign_Chest_ORM': (False, unreal.TextureCompressionSettings.TC_MASKS),
    'T_ObsidianSovereign_Chest_Normal_DirectX': (False, unreal.TextureCompressionSettings.TC_NORMALMAP),
}
tools.import_asset_tasks([task(os.path.join(SRC, 'textures', n + '.png'), DST) for n in tex])
for n, (srgb, comp) in tex.items():
    t = unreal.load_asset(f'{DST}/{n}')
    t.set_editor_property('srgb', srgb); t.set_editor_property('compression_settings', comp)
    if 'Normal' in n: t.set_editor_property('flip_green_channel', False)
    EAL.save_loaded_asset(t)
    unreal.log(f'#64 re-imported {n}')
