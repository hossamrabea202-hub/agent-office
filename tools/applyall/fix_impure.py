# fix_impure.py (Master, 2026-10-30). Run on a graph or merged t3d BEFORE handing it back:
#   python tools/applyall/fix_impure.py in.t3d out.t3d [NodeNamePrefix]
# UE 5.3 imports these as IMPURE no matter what the text says, and an impure node with no exec wire is pruned at compile:
#   GetActorOfClass, GetAllActorsOfClass, DoesSaveGameExist, LoadGameFromSlot, CreateSaveGameObject, SaveGameToSlot,
#   and every K2Node_DynamicCast (bIsPureCast=True is ignored on paste).
# The script gives each one exec pins and splices it into the exec chain right before its first impure consumer
# (a cast used by two consumers is split into one cast per consumer; CastFailed goes on to the same node).
# It also fills an empty GetActorOfClass ActorClass from its typed ReturnValue.
import re, sys, uuid
src, dst = sys.argv[1], sys.argv[2]
PFX = sys.argv[3] if len(sys.argv)>3 else ''
t = open(src, encoding='utf-8').read()
blocks = re.findall(r'Begin Object .*?\nEnd Object\n?', t, re.S)
def name(b): return re.search(r'Name="([^"]+)"', b).group(1)
B = {name(b): b for b in blocks}
order = [name(b) for b in blocks]
def pins(b): return re.findall(r'   CustomProperties Pin \((.*)\)\n', b)
def pin_field(p, f):
    m = re.search(f + r'="?([^",]*)"?', p); return m.group(1) if m else None
def pin_links(p):
    m = re.search(r'LinkedTo=\(([^)]*)\)', p)
    return [x.strip().split(' ') for x in m.group(1).split(',') if x.strip()] if m else []
def find_pin(nn, pname):
    for p in pins(B[nn]):
        if pin_field(p, 'PinName') == pname: return p
def set_links(nn, pname, links):
    b = B[nn]; p = find_pin(nn, pname)
    lt = 'LinkedTo=(' + ''.join('%s %s,' % (a, c) for a, c in links) + ')' if links else ''
    if 'LinkedTo=(' in p: np = re.sub(r'LinkedTo=\([^)]*\),?', lt + (',' if lt else ''), p)
    else: np = p.replace(',PersistentGuid', ',' + lt + ',PersistentGuid') if lt else p
    B[nn] = b.replace(p, np)
def pinid(nn, pname): return pin_field(find_pin(nn, pname), 'PinId')
G = lambda: uuid.uuid4().hex.upper()
EXEC_T = 'PinType.PinCategory="exec",PinType.PinSubCategory="",PinType.PinSubCategoryObject=None,PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,'
TAIL = 'PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,'
log = []
# split casts used by several consumers into one cast per consumer
for nn in list(order):
    if not nn.startswith(PFX) or 'K2Node_DynamicCast' not in B[nn].split('\n',1)[0]: continue
    outp=[p for p in pins(B[nn]) if pin_field(p,'Direction')=='EGPD_Output' and pin_field(p,'PinName').startswith('As')]
    if not outp: continue
    cons=pin_links(outp[0])
    if len(cons)<2: continue
    asname=pin_field(outp[0],'PinName'); objsrc=pin_links(find_pin(nn,'Object'))
    for i,(ca,cp) in enumerate(cons[1:],1):
        nb=B[nn]; newn=nn+'_c%d'%i
        nb=nb.replace('Name="%s"'%nn,'Name="%s"'%newn,1)
        for p in pins(B[nn]):
            nb=nb.replace('PinId=%s'%pin_field(p,'PinId'),'PinId=%s'%G())
        nb=re.sub(r'NodeGuid=[0-9A-F]+','NodeGuid='+G(),nb)
        B[newn]=nb; order.insert(order.index(nn)+1,newn)
        set_links(newn,asname,[(ca,cp)])
        oid=pinid(newn,'Object'); set_links(newn,'Object',objsrc)
        for a,c in objsrc:
            for p in pins(B[a]):
                if pin_field(p,'PinId')==c: set_links(a,pin_field(p,'PinName'),pin_links(p)+[(newn,oid)])
        # repoint consumer
        for p in pins(B[ca]):
            if pin_field(p,'PinId')==cp: set_links(ca,pin_field(p,'PinName'),[(x,y) if x!=nn else (newn,pinid(newn,asname)) for x,y in pin_links(p)])
    set_links(nn,asname,[cons[0]])
    log.append('%s split into %d'%(nn,len(cons)))
for nn in list(order):
    b = B[nn]
    if not nn.startswith(PFX): continue
    isgaoc=any(('MemberName="%s"'%f) in b for f in ('GetActorOfClass','DoesSaveGameExist','LoadGameFromSlot','CreateSaveGameObject','SaveGameToSlot','GetAllActorsOfClass')); iscast='K2Node_DynamicCast' in b.split('\n',1)[0]
    if not (isgaoc or iscast): continue
    pure=('bIsPureFunc=True' in b) or ('bIsPureCast=True' in b) or find_pin(nn,'execute') is None
    if iscast: b=b.replace('   bIsPureCast=True\n','')
    if not pure and pin_links(find_pin(nn,'execute')): continue
    rv = find_pin(nn, 'ReturnValue') or ''
    cls = None if iscast else re.search(r"PinSubCategoryObject=\"/Script/Engine.BlueprintGeneratedClass'([^']+)'", rv)
    b = b.replace('   bIsPureFunc=True\n', '')
    if cls:
        ac = find_pin(nn, 'ActorClass')
        if 'DefaultObject=' not in ac:
            b = b.replace(ac, ac.replace(',PersistentGuid', ',DefaultObject="%s",PersistentGuid' % cls.group(1), 1) if ',PersistentGuid' in ac else ac)
    if pure:
      ein, eout = G(), G()
      first = re.search(r'   CustomProperties Pin \(', b).start()
      b = b[:first] + '   CustomProperties Pin (PinId=%s,PinName="execute",%s%s)\n' % (ein, EXEC_T, TAIL) + '   CustomProperties Pin (PinId=%s,PinName="then",Direction="EGPD_Output",%s%s)\n' % (eout, EXEC_T, TAIL) + b[first:]
      efail = G() if iscast else None
      if iscast: b = b[:first] + '   CustomProperties Pin (PinId=%s,PinName="CastFailed",Direction="EGPD_Output",%s%s)\n' % (efail, EXEC_T, TAIL) + b[first:]
    else:
      ein, eout = pinid(nn,'execute'), pinid(nn,'then'); efail = pinid(nn,'CastFailed') if iscast else None
    B[nn] = b
    # find first impure consumer downstream
    seen = set(); q = [nn]; target = None
    while q and not target:
        cur = q.pop(0)
        for p in pins(B[cur]):
            if pin_field(p, 'Direction') == 'EGPD_Output' and 'PinCategory="exec"' not in p:
                for a, c in pin_links(p):
                    if a in seen or a not in B: continue
                    seen.add(a)
                    if find_pin(a, 'execute') is not None and pin_links(find_pin(a, 'execute')): target = a; break
                    q.append(a)
            if target: break
    if not target: log.append(nn + ': no impure consumer'); continue
    srcs = pin_links(find_pin(target, 'execute')); tex = pinid(target, 'execute')
    for a, c in srcs:
        for p in pins(B[a]):
            if pin_field(p, 'PinId') == c:
                pn = pin_field(p, 'PinName')
                set_links(a, pn, [(x, y) if not (x == target and y == tex) else (nn, ein) for x, y in pin_links(p)])
    set_links(nn, 'execute', srcs); set_links(nn, 'then', [(target, tex)])
    if efail: set_links(nn, 'CastFailed', [(target, tex)])
    set_links(target, 'execute', [(nn, eout)] + ([(nn, efail)] if efail else []))
    log.append('%s spliced before %s (cls=%s)' % (nn, target, cls.group(1).split('.')[-1] if cls else None))
open(dst, 'w', encoding='utf-8').write(''.join(B[n] for n in order))
print('\n'.join(log))
