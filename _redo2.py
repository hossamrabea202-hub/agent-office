import unreal, sys
sys.argv=['x','--apply']; exec(open(r'C:/Users/hossa/Documents/agent-office/_snap.py').read(), {'__name__':'__main__'})
M=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
for n,v in (('MI_TentacleJellyShell_5',2.5),('MI_TentacleJellyShell_4',3.75)):
    p='/Game/CastleDefender/VFX/JellyBubble/'+n; mi=unreal.load_asset(p)
    print(n,'TentScale',M.get_material_instance_scalar_parameter_value(mi,'TentScale'),'->',v)
    M.set_material_instance_scalar_parameter_value(mi,'TentScale',v); M.update_material_instance(mi); EAL.save_asset(p)
print('save', unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
