# Reads MPC_SkillTree (Armor etc.) and the armoury save slot; set RESET=True to put Armor back to 0 (silver). Report in master_check.txt.
import unreal, traceback
RESET = False
L = r'C:\Unreal Backups\Castle Defender\Tools\master_check.txt'
out = []
try:
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    mpcs = [a for a in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'MaterialParameterCollection')) if 'SkillTree' in str(a.asset_name)]
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for a in mpcs:
        mpc = unreal.load_asset(str(a.package_name))
        out.append('MPC %s' % a.package_name)
        for sp in mpc.get_editor_property('scalar_parameters'):
            n = str(sp.get_editor_property('parameter_name'))
            dv = sp.get_editor_property('default_value')
            cur = unreal.MaterialLibrary.get_scalar_parameter_value(w, mpc, n)
            out.append('  %s default=%s current=%s' % (n, dv, cur))
            if RESET and n.startswith('Armor'):
                unreal.MaterialLibrary.set_scalar_parameter_value(w, mpc, n, 0.0)
                out.append('   -> reset to 0')
        for vp in mpc.get_editor_property('vector_parameters'):
            n = str(vp.get_editor_property('parameter_name'))
            out.append('  %s default=%s current=%s' % (n, vp.get_editor_property('default_value'), unreal.MaterialLibrary.get_vector_parameter_value(w, mpc, n)))
    import os, glob
    for f in glob.glob(r'C:\Unreal Backups\Castle Defender\Saved\SaveGames\*.sav'):
        out.append('SAVE %s %d bytes %s' % (os.path.basename(f), os.path.getsize(f), unreal.GameplayStatics.does_save_game_exist(os.path.basename(f)[:-4], 0)))
except Exception:
    out.append(traceback.format_exc())
open(L, 'w').write('\n'.join(out))
