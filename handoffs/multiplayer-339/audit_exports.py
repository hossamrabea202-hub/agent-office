import re,os,glob,sys
root=sys.argv[1]
files=sorted(glob.glob(root+'/handoffs/exports/**/*.t*', recursive=True))
files=[f for f in files if f.endswith(('.txt','.t3d'))]
best={}
for f in files:
    t=open(f,encoding='utf-8',errors='replace').read()
    m=re.search(r"ExportPath=\"[^\"]*'(/Game/[^.']+)\.(\w+)[:.]",t)
    if not m: continue
    bp=m.group(2); mt=os.path.getmtime(f)
    if bp not in best or mt>best[bp][0]: best[bp]=(mt,f,t)
rows=[]
for bp,(mt,f,t) in sorted(best.items()):
    pl=len(re.findall(r'MemberName="GetPlayer(?:Character|Controller|Pawn|CameraManager)"',t))
    sv=len(re.findall(r'MemberName="(?:SaveGameToSlot|LoadGameFromSlot|AsyncSaveGameToSlot)"',t))
    eco=sorted(set(re.findall(r'MemberName="(Gold|Ore|Iron|XP|SkillPoints|Metal\w*|Coins)"',t)))
    hud=len(re.findall(r'MemberName="(?:CreateWidget|AddToViewport|GetHUD|ReceiveDrawHUD)"',t))
    if pl or sv or eco or hud: rows.append((pl,bp,sv,', '.join(eco),hud,os.path.relpath(f,root).replace(os.sep,'/')))
rows.sort(reverse=True)
print('| Blueprint | player-0 calls | save/load | economy vars | HUD calls | export |\n|---|---|---|---|---|---|')
for pl,bp,sv,eco,hud,f in rows: print('| %s | %d | %d | %s | %d | `%s` |'%(bp,pl,sv,eco or '-',hud,f))
print('\nTotal player-0 calls: %d in %d Blueprints'%(sum(r[0] for r in rows),sum(1 for r in rows if r[0])))
