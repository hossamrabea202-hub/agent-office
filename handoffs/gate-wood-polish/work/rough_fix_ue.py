import unreal
src = open('C:/Users/hossam.rabea/ckw/wood/apply_gate_polish_ue.py').read().split("\nif '--revert' in sys.argv:")[0]
g = {'__name__': 'gp', '__file__': 'C:/Users/hossam.rabea/ckw/wood/apply_gate_polish_ue.py'}; exec(src, g)
mat, node = g['gate_custom_node']()
code = node.get_editor_property('code')
pairs = [('float3 ironC=float3(0.046,0.044,0.042)*(0.8+0.4*grit);', 'float3 ironC=float3(0.037,0.036,0.034)*(0.85+0.3*grit);'),
         ('lerp(lerp(0.72+0.10*grit,0.85,rust),0.35,bare)', 'lerp(lerp(0.78+0.10*grit,0.85,rust),0.35,bare)')]
n = 0
for a, b in pairs:
    if a in code: code = code.replace(a, b); n += 1
node.set_editor_property('code', code); g['MEL'].recompile_material(mat); g['EAL'].save_loaded_asset(mat)
print('oxide tuned, changes', n, '| patched block present:', g['IRON_NEW'] in code)
