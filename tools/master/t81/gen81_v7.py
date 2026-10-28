import sys; sys.path.insert(0, '.')
from kit import *
G = Graph()
ACT, COMP, SKM, CHAR = CLS('Actor'), CLS('ActorComponent'), CLS('SkeletalMeshComponent'), CLS('Character')
BLOB = BPC('/Game/CastleDefender/Gameplay/Tentacle/Jelly/BP_JellyBlob', 'BP_JellyBlob')          # fixed below if path differs
BALL = BPC('/Game/CastleDefender/Gameplay/Cannon/BP_Cannonball', 'BP_Cannonball')
GS = CLS('GameplayStatics')
HITRES = '"/Script/CoreUObject.ScriptStruct\'/Script/Engine.HitResult\'"'
# ---------- BeginPlay: Scale0 = root scale; bind OnTakeAnyDamage ----------
G.node('BP', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveBeginPlay")' % COMP}, ex('then', True)], 0, 0)
callfn(G, 'Owner1', COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=0, y=250, self_hidden=True)
callfn(G, 'Root1', ACT, 'K2_GetRootComponent', [ob('ReturnValue', CLS('SceneComponent'), out=True)], pure=True, const=True, x=300, y=250)
G.link('Owner1', 'ReturnValue', 'Root1', 'self')
varget(G, 'RootScale', CLS('SceneComponent'), 'RelativeScale3D', CLS('SceneComponent'), st('RelativeScale3D', STRUCT('Vector')), 600, 250)
G.link('Root1', 'ReturnValue', 'RootScale', 'self')
varset(G, 'SetScale0', None, 'Scale0', None, st('Scale0', STRUCT('Vector'), default='0, 0, 0'), 400, 0, self_ctx=True)
G.link('BP', 'then', 'SetScale0', 'execute'); G.link('RootScale', 'RelativeScale3D', 'SetScale0', 'Scale0')
# bind
G.node('Bind', 'K2Node_AddDelegate', ['DelegateReference=(MemberParent=%s,MemberName="OnTakeAnyDamage")' % ACT],
       [ex(), ex('then', True), selfpin(ACT), {'name': 'Delegate', 'cat': 'delegate', 'mref': '()'}], 800, 0)
G.link('SetScale0', 'then', 'Bind', 'execute'); G.link('Owner1', 'ReturnValue', 'Bind', 'self')
# custom event OnHit(DamagedActor, Damage, DamageType, InstigatedBy, DamageCauser)
G.node('OnHit', 'K2Node_CustomEvent', ['CustomFunctionName="OnTentacleHit"',
    'CustomProperties UserDefinedPin (PinName="DamagedActor",PinType=(PinCategory="object",PinSubCategoryObject=%s),DesiredPinDirection=EGPD_Output)' % ACT,
    'CustomProperties UserDefinedPin (PinName="Damage",PinType=(PinCategory="real",PinSubCategory="float"),DesiredPinDirection=EGPD_Output)',
    'CustomProperties UserDefinedPin (PinName="DamageType",PinType=(PinCategory="object",PinSubCategoryObject=%s),DesiredPinDirection=EGPD_Output)' % CLS('DamageType'),
    'CustomProperties UserDefinedPin (PinName="InstigatedBy",PinType=(PinCategory="object",PinSubCategoryObject=%s),DesiredPinDirection=EGPD_Output)' % CLS('Controller'),
    'CustomProperties UserDefinedPin (PinName="DamageCauser",PinType=(PinCategory="object",PinSubCategoryObject=%s),DesiredPinDirection=EGPD_Output)' % ACT],
    [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '()'}, ex('then', True),
     ob('DamagedActor', ACT, out=True), fl('Damage', out=True), ob('DamageType', CLS('DamageType'), out=True), ob('InstigatedBy', CLS('Controller'), out=True), ob('DamageCauser', ACT, out=True)], 0, 600)
G.link('OnHit', 'OutputDelegate', 'Bind', 'Delegate')
# ignore cannonballs: cast DamageCauser -> BP_Cannonball ; CastFailed = real hit
cast(G, 'IsBall', BALL, 'AsBP Cannonball', 400, 600)
G.link('OnHit', 'then', 'IsBall', 'execute'); G.link('OnHit', 'DamageCauser', 'IsBall', 'Object')
# WobbleT = now
callfn(G, 'Now1', GS, 'GetTimeSeconds', [ob('WorldContextObject', '"/Script/CoreUObject.Class\'/Script/CoreUObject.Object\'"', hidden=True), fl('ReturnValue', out=True, sub='double')], pure=True, x=600, y=900, self_hidden=True)
varset(G, 'SetWobbleT', None, 'WobbleT', None, fl('WobbleT', default='0.0'), 800, 600, self_ctx=True)
G.link('IsBall', 'CastFailed', 'SetWobbleT', 'execute'); G.link('Now1', 'ReturnValue', 'SetWobbleT', 'WobbleT')
# HitCount = HitCount + 1
varget(G, 'GetHits', None, 'HitCount', None, it('HitCount'), 1000, 900, self_ctx=True)
mathfn(G, 'Add1', 'Add_IntInt', [it('A', default='0'), it('B', default='1'), it('ReturnValue', out=True)], 1200, 900)
G.link('GetHits', 'HitCount', 'Add1', 'A')
varset(G, 'SetHits', None, 'HitCount', None, it('HitCount', default='0'), 1200, 600, self_ctx=True)
G.link('SetWobbleT', 'then', 'SetHits', 'execute'); G.link('Add1', 'ReturnValue', 'SetHits', 'HitCount')
# Branch: HitCount >= SpitEvery AND now > NextSpitT
varget(G, 'GetEvery', None, 'SpitEvery', None, it('SpitEvery'), 1400, 1000, self_ctx=True)
mathfn(G, 'GE', 'GreaterEqual_IntInt', [it('A', default='0'), it('B', default='0'), bo('ReturnValue', out=True)], 1600, 950)
G.link('SetHits', 'Output_Get', 'GE', 'A'); G.link('GetEvery', 'SpitEvery', 'GE', 'B')
varget(G, 'GetNext', None, 'NextSpitT', None, fl('NextSpitT'), 1400, 1150, self_ctx=True)
callfn(G, 'Now2', GS, 'GetTimeSeconds', [ob('WorldContextObject', '"/Script/CoreUObject.Class\'/Script/CoreUObject.Object\'"', hidden=True), fl('ReturnValue', out=True, sub='double')], pure=True, x=1400, y=1300, self_hidden=True)
mathfn(G, 'GT', 'Greater_DoubleDouble', [fl('A', default='0.0', sub='double'), fl('B', default='0.0', sub='double'), bo('ReturnValue', out=True)], 1600, 1200)
G.link('Now2', 'ReturnValue', 'GT', 'A'); G.link('GetNext', 'NextSpitT', 'GT', 'B')
mathfn(G, 'And', 'BooleanAND', [bo('A', default='false'), bo('B', default='false'), bo('ReturnValue', out=True)], 1800, 1050)
G.link('GE', 'ReturnValue', 'And', 'A'); G.link('GT', 'ReturnValue', 'And', 'B')
branch(G, 'DoSpit', 1700, 600)
G.link('SetHits', 'then', 'DoSpit', 'execute'); G.link('And', 'ReturnValue', 'DoSpit', 'Condition')
# true: HitCount = 0 ; NextSpitT = now + SpitCooldown ; spawn 2 blobs
varset(G, 'ResetHits', None, 'HitCount', None, it('HitCount', default='0'), 2000, 600, self_ctx=True)
G.link('DoSpit', 'then', 'ResetHits', 'execute')
varget(G, 'GetCd', None, 'SpitCooldown', None, fl('SpitCooldown'), 2000, 1000, self_ctx=True)
mathfn(G, 'AddCd', 'Add_DoubleDouble', [fl('A', default='0.0', sub='double'), fl('B', default='0.0', sub='double'), fl('ReturnValue', out=True, sub='double')], 2200, 950)
G.link('Now2', 'ReturnValue', 'AddCd', 'A'); G.link('GetCd', 'SpitCooldown', 'AddCd', 'B')
varset(G, 'SetNext', None, 'NextSpitT', None, fl('NextSpitT', default='0.0'), 2300, 600, self_ctx=True)
G.link('ResetHits', 'then', 'SetNext', 'execute'); G.link('AddCd', 'ReturnValue', 'SetNext', 'NextSpitT')
prev = 'SetNext'
# spit at the attacker: spawn near player pawn 0 (random ring 300-600 cm, +250 up); blob lobs itself from there
callfn(G, 'Pawn', GS, 'GetPlayerPawn', [ob('WorldContextObject', '"/Script/CoreUObject.Class\'/Script/CoreUObject.Object\'"', hidden=True), it('PlayerIndex', default='0'), ob('ReturnValue', CLS('Pawn'), out=True)], pure=True, x=2300, y=1400, self_hidden=True)
callfn(G, 'LocP', ACT, 'K2_GetActorLocation', [st('ReturnValue', STRUCT('Vector'), out=True)], pure=True, const=True, x=2600, y=1400)
G.link('Pawn', 'ReturnValue', 'LocP', 'self')
mathfn(G, 'UpP', 'Add_VectorVector', [st('A', STRUCT('Vector'), default='0, 0, 0'), st('B', STRUCT('Vector'), default='0.000000,0.000000,250.000000'), st('ReturnValue', STRUCT('Vector'), out=True)], 2900, 1400)
G.link('LocP', 'ReturnValue', 'UpP', 'A')
prev = 'SetNext'
for k in (1, 2):
    x = 4000 + (k - 1) * 900
    mathfn(G, 'Yaw%d' % k, 'RandomFloatInRange', [fl('Min', default='0.0', sub='double'), fl('Max', default='360.0', sub='double'), fl('ReturnValue', out=True, sub='double')], x + 200, 1200)
    mathfn(G, 'Rot%d' % k, 'MakeRotator', [fl('Roll', default='0.0', friendly='"X (Roll)"'), fl('Pitch', default='0.0', friendly='"Y (Pitch)"'), fl('Yaw', default='0.0', friendly='"Z (Yaw)"'), st('ReturnValue', STRUCT('Rotator'), out=True)], x + 400, 1200)
    G.link('Yaw%d' % k, 'ReturnValue', 'Rot%d' % k, 'Yaw')
    mathfn(G, 'Xf%d' % k, 'MakeTransform', [st('Location', STRUCT('Vector'), default='0, 0, 0'), st('Rotation', STRUCT('Rotator'), default='0, 0, 0'), st('Scale', STRUCT('Vector'), default='1.000000,1.000000,1.000000'), st('ReturnValue', STRUCT('Transform'), out=True)], x + 600, 1100)
    mathfn(G, 'Fwd%d' % k, 'GetForwardVector', [st('InRot', STRUCT('Rotator'), default='0, 0, 0'), st('ReturnValue', STRUCT('Vector'), out=True)], x + 200, 1400)
    G.link('Rot%d' % k, 'ReturnValue', 'Fwd%d' % k, 'InRot')
    mathfn(G, 'Dist%d' % k, 'RandomFloatInRange', [fl('Min', default='300.0', sub='double'), fl('Max', default='600.0', sub='double'), fl('ReturnValue', out=True, sub='double')], x + 200, 1550)
    mathfn(G, 'Off%d' % k, 'Multiply_VectorFloat', [st('A', STRUCT('Vector'), default='0, 0, 0'), fl('B', default='0.0', sub='double'), st('ReturnValue', STRUCT('Vector'), out=True)], x + 400, 1450)
    G.link('Fwd%d' % k, 'ReturnValue', 'Off%d' % k, 'A'); G.link('Dist%d' % k, 'ReturnValue', 'Off%d' % k, 'B')
    mathfn(G, 'Loc%d' % k, 'Add_VectorVector', [st('A', STRUCT('Vector'), default='0, 0, 0'), st('B', STRUCT('Vector'), default='0, 0, 0'), st('ReturnValue', STRUCT('Vector'), out=True)], x + 600, 1400)
    G.link('UpP', 'ReturnValue', 'Loc%d' % k, 'A'); G.link('Off%d' % k, 'ReturnValue', 'Loc%d' % k, 'B')
    G.link('Loc%d' % k, 'ReturnValue', 'Xf%d' % k, 'Location'); G.link('Rot%d' % k, 'ReturnValue', 'Xf%d' % k, 'Rotation')
    G.node('Spawn%d' % k, 'K2Node_SpawnActorFromClass', [], [ex(), ex('then', True),
        {'name': 'Class', 'cat': 'class', 'obj': ACT, 'dobj': '/Game/CastleDefender/Gameplay/Tentacle/Jelly/BP_JellyBlob.BP_JellyBlob_C'},
        {'name': 'SpawnTransform', 'cat': 'struct', 'obj': STRUCT('Transform')},
        {'name': 'CollisionHandlingOverride', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.ESpawnActorCollisionHandlingMethod\'"', 'default': 'AlwaysSpawn'},
        {'name': 'TransformScaleMethod', 'cat': 'byte', 'obj': '"/Script/CoreUObject.Enum\'/Script/Engine.ESpawnActorScaleMethod\'"', 'default': 'MultiplyWithRoot', 'hidden': True},
        ob('Owner', ACT), ob('ReturnValue', BLOB, out=True)], x, 600)
    G.link(prev, 'then', 'Spawn%d' % k, 'execute'); G.link('Xf%d' % k, 'ReturnValue', 'Spawn%d' % k, 'SpawnTransform')
    mathfn(G, 'Hatch%d' % k, 'RandomFloatInRange', [fl('Min', default='3.0', sub='double'), fl('Max', default='6.0', sub='double'), fl('ReturnValue', out=True, sub='double')], x + 500, 850)
    varset(G, 'SetArmed%d' % k, BLOB, 'ArmedMax', BLOB, fl('ArmedMax', default='0.0', sub='double'), x + 600, 600)
    G.link('Spawn%d' % k, 'then', 'SetArmed%d' % k, 'execute'); G.link('Spawn%d' % k, 'ReturnValue', 'SetArmed%d' % k, 'self'); G.link('Hatch%d' % k, 'ReturnValue', 'SetArmed%d' % k, 'ArmedMax')
    prev = 'SetArmed%d' % k
# ---------- Tick: wobble ----------
G.node('Tick', 'K2Node_Event', ['EventReference=(MemberParent=%s,MemberName="ReceiveTick")' % COMP, 'bOverrideFunction=True'],
       [{'name': 'OutputDelegate', 'cat': 'delegate', 'out': True, 'mref': '(MemberParent=%s,MemberName="ReceiveTick")' % COMP}, ex('then', True), fl('DeltaSeconds', out=True)], 0, 1800)
callfn(G, 'Now3', GS, 'GetTimeSeconds', [ob('WorldContextObject', '"/Script/CoreUObject.Class\'/Script/CoreUObject.Object\'"', hidden=True), fl('ReturnValue', out=True, sub='double')], pure=True, x=0, y=2100, self_hidden=True)
varget(G, 'GetWobbleT', None, 'WobbleT', None, fl('WobbleT'), 0, 2250, self_ctx=True)
mathfn(G, 'Age', 'Subtract_DoubleDouble', [fl('A', default='0.0', sub='double'), fl('B', default='0.0', sub='double'), fl('ReturnValue', out=True, sub='double')], 250, 2150)
G.link('Now3', 'ReturnValue', 'Age', 'A'); G.link('GetWobbleT', 'WobbleT', 'Age', 'B')
mathfn(G, 'Active', 'Less_DoubleDouble', [fl('A', default='0.0', sub='double'), fl('B', default='0.8', sub='double'), bo('ReturnValue', out=True)], 500, 2150)
G.link('Age', 'ReturnValue', 'Active', 'A')
branch(G, 'IfWobble', 400, 1800)
G.link('Tick', 'then', 'IfWobble', 'execute'); G.link('Active', 'ReturnValue', 'IfWobble', 'Condition')
# s = 0.07 * sin(age*35) * (1 - age/0.8)
mathfn(G, 'A35', 'Multiply_DoubleDouble', [fl('A', default='0.0', sub='double'), fl('B', default='35.0', sub='double'), fl('ReturnValue', out=True, sub='double')], 700, 2300)
G.link('Age', 'ReturnValue', 'A35', 'A')
mathfn(G, 'Sin', 'Sin', [fl('A', default='0.0', sub='double'), fl('ReturnValue', out=True, sub='double')], 900, 2300)
G.link('A35', 'ReturnValue', 'Sin', 'A')
mathfn(G, 'Frac', 'Divide_DoubleDouble', [fl('A', default='0.0', sub='double'), fl('B', default='0.8', sub='double'), fl('ReturnValue', out=True, sub='double')], 700, 2450)
G.link('Age', 'ReturnValue', 'Frac', 'A')
mathfn(G, 'OneMinus', 'Subtract_DoubleDouble', [fl('A', default='1.0', sub='double'), fl('B', default='0.0', sub='double'), fl('ReturnValue', out=True, sub='double')], 900, 2450)
G.link('Frac', 'ReturnValue', 'OneMinus', 'B')
mathfn(G, 'Env', 'Multiply_DoubleDouble', [fl('A', default='0.0', sub='double'), fl('B', default='0.0', sub='double'), fl('ReturnValue', out=True, sub='double')], 1100, 2380)
G.link('Sin', 'ReturnValue', 'Env', 'A'); G.link('OneMinus', 'ReturnValue', 'Env', 'B')
mathfn(G, 'Amp', 'Multiply_DoubleDouble', [fl('A', default='0.0', sub='double'), fl('B', default='0.07', sub='double'), fl('ReturnValue', out=True, sub='double')], 1300, 2380)
G.link('Env', 'ReturnValue', 'Amp', 'A')
# scale = Scale0 * (1+s, 1+s, 1-s)
mathfn(G, 'OnePlus', 'Add_DoubleDouble', [fl('A', default='1.0', sub='double'), fl('B', default='0.0', sub='double'), fl('ReturnValue', out=True, sub='double')], 1500, 2300)
G.link('Amp', 'ReturnValue', 'OnePlus', 'B')
mathfn(G, 'OneMinusS', 'Subtract_DoubleDouble', [fl('A', default='1.0', sub='double'), fl('B', default='0.0', sub='double'), fl('ReturnValue', out=True, sub='double')], 1500, 2450)
G.link('Amp', 'ReturnValue', 'OneMinusS', 'B')
mathfn(G, 'MkVec', 'MakeVector', [fl('X', default='0.0', sub='double'), fl('Y', default='0.0', sub='double'), fl('Z', default='0.0', sub='double'), st('ReturnValue', STRUCT('Vector'), out=True)], 1700, 2350)
G.link('OnePlus', 'ReturnValue', 'MkVec', 'X'); G.link('OnePlus', 'ReturnValue', 'MkVec', 'Y'); G.link('OneMinusS', 'ReturnValue', 'MkVec', 'Z')
varget(G, 'GetScale0', None, 'Scale0', None, st('Scale0', STRUCT('Vector')), 1700, 2550, self_ctx=True)
mathfn(G, 'VecMul', 'Multiply_VectorVector', [st('A', STRUCT('Vector'), default='0, 0, 0'), st('B', STRUCT('Vector'), default='0, 0, 0'), st('ReturnValue', STRUCT('Vector'), out=True)], 1900, 2400)
G.link('GetScale0', 'Scale0', 'VecMul', 'A'); G.link('MkVec', 'ReturnValue', 'VecMul', 'B')
callfn(G, 'Owner4', COMP, 'GetOwner', [ob('ReturnValue', ACT, out=True)], pure=True, const=True, x=1700, y=2000, self_hidden=True)
callfn(G, 'Root2', ACT, 'K2_GetRootComponent', [ob('ReturnValue', CLS('SceneComponent'), out=True)], pure=True, const=True, x=1900, y=2000)
G.link('Owner4', 'ReturnValue', 'Root2', 'self')
callfn(G, 'SetScale', CLS('SceneComponent'), 'SetRelativeScale3D', [st('NewScale3D', STRUCT('Vector'), default='0, 0, 0')], x=2200, y=1800)
G.link('IfWobble', 'then', 'SetScale', 'execute'); G.link('Root2', 'ReturnValue', 'SetScale', 'self'); G.link('VecMul', 'ReturnValue', 'SetScale', 'NewScale3D')
# else: restore Scale0 once (cheap: every tick when idle is wasteful; use WobbleT > 0 check? keep simple: restore only while age < 1.0)
mathfn(G, 'Restore', 'Less_DoubleDouble', [fl('A', default='0.0', sub='double'), fl('B', default='1.0', sub='double'), bo('ReturnValue', out=True)], 500, 2650)
G.link('Age', 'ReturnValue', 'Restore', 'A')
branch(G, 'IfRestore', 2200, 2100)
G.link('IfWobble', 'else', 'IfRestore', 'execute'); G.link('Restore', 'ReturnValue', 'IfRestore', 'Condition')
callfn(G, 'SetScaleBack', CLS('SceneComponent'), 'SetRelativeScale3D', [st('NewScale3D', STRUCT('Vector'), default='0, 0, 0')], x=2500, y=2100)
G.link('IfRestore', 'then', 'SetScaleBack', 'execute'); G.link('Root2', 'ReturnValue', 'SetScaleBack', 'self'); G.link('GetScale0', 'Scale0', 'SetScaleBack', 'NewScale3D')
open('BPC_TentacleSpit_graph_v7.txt', 'w').write(G.render())
print('nodes', len(G.nodes), 'links', len(G.links))
