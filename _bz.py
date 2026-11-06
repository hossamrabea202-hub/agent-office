import unreal
AR=unreal.AssetRegistryHelpers.get_asset_registry(); EAL=unreal.EditorAssetLibrary
o=[]
o.append('VFX/Berserk: %s'%EAL.list_assets('/Game/CastleDefender/VFX/Berserk',recursive=True))
names=[]
for a in AR.get_assets_by_path('/Game',True):
    n=str(a.asset_name)
    if 'erserk' in n or 'Rage' in n: names.append('%s (%s)'%(a.package_name,a.asset_class_path.asset_name))
o.append('named berserk/rage:\n  '+'\n  '.join(names))
opt=unreal.AssetRegistryDependencyOptions()
for p in [x.split(' ')[0] for x in names]:
    try: o.append('refs of %s: %s'%(p,[str(r) for r in AR.get_referencers(p,opt)]))
    except Exception as e: o.append('ERR %s %s'%(p,e))
inf=[str(a.package_name) for a in AR.get_assets_by_path('/Game',True) if str(a.asset_name)=='BPC_Infection']
o.append('Infection %s refs %s'%(inf,[str(r) for r in AR.get_referencers(inf[0],opt)] if inf else None))
if inf:
    d=unreal.get_default_object(unreal.load_asset(inf[0]).generated_class())
    o.append('MaxHP default %s'%d.get_editor_property('MaxHP'))
print('\n'.join(o))
