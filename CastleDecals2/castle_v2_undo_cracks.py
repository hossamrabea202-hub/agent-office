import json, unreal
old = json.load(open(r'C:\Users\hossa\Documents\agent-office\CastleDecals2\_crackamount_before.json'))
for p, v in old.items():
    mi = unreal.load_asset(p); unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, 'CrackAmount', v); unreal.EditorAssetLibrary.save_asset(p)
print('restored', len(old))
