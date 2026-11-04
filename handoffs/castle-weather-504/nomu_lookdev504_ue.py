# #504 offline lookdev (i5): a mock castle wall on the empty Entry map, nothing saved, no Multi-User session needed.
#   py nomu_lookdev504_ue.py build      mock wall (curtain + overhanging cap + 3 merlons with caps + slit tower) in the real
#                                       kit491 stone MI, sun + fill, then the transient #504 materials
#   py nomu_lookdev504_ue.py before     locked-exposure shots  -> shots/ld504_<view>_before.png
#   py nomu_lookdev504_ue.py place      runs the placer (--apply) on the mock
#   py nomu_lookdev504_ue.py after      same shots -> _after.png
#   py nomu_lookdev504_ue.py clear      removes every actor tagged LD504 / CW504
import sys, unreal
HERE = 'C:/Users/hossam.rabea/agent-office/handoffs/castle-weather-504'
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V, R = unreal.Vector, unreal.Rotator
CUBE = '/Engine/BasicShapes/Cube'          # 100 cm, pivot at the centre
STONE = '/Game/CastleDefender/Environment/Castle/StoneKit491/MI_CastleAshlar_Kit491'
O = V(0, 0, 0)
step = [a for a in sys.argv[1:] if not a.startswith('--')][0]


def box(label, c, size, mat=STONE):
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, O + c, R(0, 0, 0))
    m = a.static_mesh_component; m.set_static_mesh(unreal.load_asset(CUBE)); m.set_material(0, unreal.load_asset(mat))
    a.set_actor_scale3d(V(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0)); a.set_actor_label('Castle_LD504_' + label)
    a.tags = [unreal.Name('LD504')]; return a


VIEWS = {'front': (V(1100, -1500, 350), V(0, 0, 300)), 'close': (V(250, -520, 420), V(-80, 0, 380)),
         'merlon': (V(-200, -600, 700), V(-350, 0, 560)), 'back': (V(300, 1400, 300), V(300, 0, 200)),
         'slit': (V(880, -420, 260), V(810, 0, 260))}


def exec_file(path, argv):
    old = sys.argv; sys.argv = [path] + argv
    try: exec(compile(open(path, encoding='utf-8').read(), path, 'exec'), {'__name__': '__main__', '__file__': path})
    finally: sys.argv = old


if step == 'build':
    # curtain 800 wide, 80 thick, 450 high; a string course at 250 that projects 12 cm; parapet + 3 merlons with caps
    box('Curtain_Low', V(0, 0, 125), (800, 80, 250))
    box('StringCourse', V(0, -6, 260), (820, 104, 20))
    box('Curtain_High', V(0, 0, 370), (800, 80, 200))
    box('Parapet_Cap', V(0, -5, 480), (820, 100, 20))
    for i, x in enumerate((-300, 0, 300)):
        box('Merlon%d' % i, V(x, 0, 570), (150, 80, 160))
        box('Merlon%d_Cap' % i, V(x, -4, 660), (170, 98, 18))
    # tower with an arrow slit: one mesh can't have a hole, so 3 boxes around a 20x110 slit (left, right, below/above)
    box('Tower_L', V(700, 0, 300), (190, 120, 600)); box('Tower_R', V(920, 0, 300), (190, 120, 600))
    box('Tower_Below', V(810, 0, 150), (30, 120, 300)); box('Tower_Above', V(810, 0, 520), (30, 120, 160))
    box('Ground', V(300, 0, -5), (4000, 4000, 10), '/Engine/EngineMaterials/DefaultMaterial')
    s = EAS.spawn_actor_from_class(unreal.DirectionalLight, V(0, 0, 2000), R(roll=0, pitch=-35, yaw=60))
    s.light_component.set_intensity(6.0); s.tags = [unreal.Name('LD504')]
    f = EAS.spawn_actor_from_class(unreal.DirectionalLight, V(0, 0, 2000), R(roll=0, pitch=-15, yaw=-120))
    f.light_component.set_intensity(1.2); f.light_component.set_cast_shadows(False); f.tags = [unreal.Name('LD504')]
    exec_file(HERE + '/build_weather504_ue.py', ['--temp'])
    print('mock built')
elif step in ('before', 'after'):
    sys.path.insert(0, 'C:/Users/hossam.rabea/agent-office/handoffs/contact-decals-425'); import importlib, lookdev_cap; importlib.reload(lookdev_cap)
    for k, (cam, tgt) in VIEWS.items():
        lookdev_cap.shot('%s/shots/ld504_%s_%s.png' % (HERE, k, step), cam, tgt, 0.5, 50.0)
elif step == 'place':
    exec_file(HERE + '/place_weather504_ue.py', ['--apply', '--temp'])
elif step == 'clear':
    gone = [x for x in EAS.get_all_level_actors() if set(str(t) for t in x.tags) & {'LD504', 'CW504'}]
    for x in gone: EAS.destroy_actor(x)
    print('cleared', len(gone))
