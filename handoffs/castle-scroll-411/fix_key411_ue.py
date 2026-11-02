# #411 fix 2 (i5, 2026-11-02, from i9's Play test): C was also the Commander key (both screens opened). The scroll moves to
# K (Keep): the key node csKeyC20's Key pin -> K, and T_HUD_CastleKey is re-imported from build/T_HUD_CastleKey.png (badge K).
# Compiles + saves BPC_CastleScroll and the texture.   py ".../fix_key411_ue.py" [--dry-run]
import os, sys, unreal
try: HERE = os.path.dirname(os.path.abspath(__file__))
except NameError: HERE = os.path.join(os.path.expanduser('~'), 'agent-office', 'handoffs', 'castle-scroll-411')
DRY = '--dry-run' in sys.argv
BEL, PL, EAL = unreal.BlueprintEditorLibrary, unreal.BlueprintGraphPinLibrary, unreal.EditorAssetLibrary
P = '/Game/CastleDefender/Gameplay/Castle/BPC_CastleScroll'
bp = unreal.load_asset(P)
n = unreal.find_object(None, P + '.BPC_CastleScroll:EventGraph.csKeyC20')
pin = BEL.find_input_pin(n, 'Key') if n else None
print('key node', bool(n), 'current', PL.get_pin_value(pin) if pin else None)
if not DRY and pin and '--icon-only' not in sys.argv:
    PL.set_pin_value(pin, 'K')
    t = unreal.AssetImportTask(); t.filename = os.path.join(HERE, 'build', 'T_HUD_CastleKey.png'); print('icon from', t.filename, os.path.exists(t.filename))
    t.destination_path = '/Game/CastleDefender/UI/HUD'; t.automated = True; t.replace_existing = True; t.save = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = unreal.load_asset('/Game/CastleDefender/UI/HUD/T_HUD_CastleKey')
    tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    EAL.save_asset('/Game/CastleDefender/UI/HUD/T_HUD_CastleKey')
    BEL.compile_blueprint(bp); EAL.save_asset(P, only_if_is_dirty=False)
    print('key now', PL.get_pin_value(pin), '; icon re-imported (K badge); compiled + saved')
if not DRY and '--icon-only' in sys.argv:
    t = unreal.AssetImportTask(); t.filename = os.path.join(HERE, 'build', 'T_HUD_CastleKey.png'); print('icon from', t.filename, os.path.exists(t.filename))
    t.destination_path = '/Game/CastleDefender/UI/HUD'; t.automated = True; t.replace_existing = True; t.save = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = unreal.load_asset('/Game/CastleDefender/UI/HUD/T_HUD_CastleKey')
    tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    EAL.save_asset('/Game/CastleDefender/UI/HUD/T_HUD_CastleKey'); print('icon re-imported + saved')
