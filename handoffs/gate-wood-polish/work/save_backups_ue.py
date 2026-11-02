import unreal
EAL = unreal.EditorAssetLibrary
for p in ('/Game/CastleDefender/Props/GateBreach/MI_GateBreach_Scratched_L_BACKUP_polish', '/Game/CastleDefender/Props/GateBreach/M_GateBreach_Scratched_BACKUP_polish'):
    print(p, 'exists', EAL.does_asset_exist(p), 'saved', EAL.save_asset(p, only_if_is_dirty=False) if EAL.does_asset_exist(p) else None)
