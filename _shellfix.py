import unreal, sys
# Tentacle jelly shell: no sideways stretch on the thick root. New master copy + swapped PS code; MIs re-parented.
# --revert puts the MIs back on M_TentacleJellyShell.
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
D='/Game/CastleDefender/VFX/JellyBubble'; OLD=D+'/M_TentacleJellyShell'; NEW=D+'/M_TentacleJellyShell_NoStretch'
rev='--revert' in sys.argv
if not rev:
    if not EAL.does_asset_exist(NEW): EAL.duplicate_asset(OLD, NEW)
    m=unreal.load_asset(NEW)
    code=open(r'C:/Users/hossa/Documents/agent-office/shell_ps_nostretch.hlsl').read()
    hit=0
    for e in m.get_editor_property('expressions') if False else []: pass
    st=[MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_BASE_COLOR)]; seen=[]
    while st:
        e=st.pop()
        if e is None or e in seen: continue
        seen.append(e); st+=[i for i in MEL.get_inputs_for_material_expression(m,e) if i]
        if isinstance(e, unreal.MaterialExpressionCustom) and 'JellyShellPS' in e.get_editor_property('code'):
            e.set_editor_property('code', code); hit+=1
    MEL.recompile_material(m); EAL.save_asset(NEW); print('PS swapped', hit)
par=unreal.load_asset(OLD if rev else NEW); n=0
for a in EAL.list_assets(D, recursive=False):
    o=unreal.load_asset(a)
    if isinstance(o, unreal.MaterialInstanceConstant) and 'TentacleJellyShell' in o.get_name():
        p=o.get_editor_property('parent').get_path_name().split('.')[0]
        if p in (OLD, NEW): MEL.set_material_instance_parent(o, par); EAL.save_asset(a.split('.')[0]); n+=1
print('MIs re-parented', n, 'to', par.get_name())
