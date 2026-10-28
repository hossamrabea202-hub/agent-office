import os
template=os.path.join(os.path.dirname(__file__),'render_tower49_final.py')
with open(template,encoding='utf-8') as stream:setup=stream.read().split("render('02_stair_closeup'")[0]
exec(compile(setup,template,'exec'))
render('01_full_tower',(260,-350,170),(0,0,98),218,(1000,2000))
render('03_crown',(42,-54,222),(0,0,194),39,(1600,1200))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'source','Tower49_200m_Presentation.blend'))
print('ROOF_FINAL_RENDERS_DONE',flush=True)

