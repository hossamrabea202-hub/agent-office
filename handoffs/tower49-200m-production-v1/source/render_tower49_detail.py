import os
template=os.path.join(os.path.dirname(__file__),'render_tower49_final.py')
with open(template,encoding='utf-8') as stream:
    setup=stream.read().split("render('02_stair_closeup'")[0]
exec(compile(setup,template,'exec'))
render('04_stair_detail',(25,-10,32),(12,2,22.5),11,(1500,1100))

