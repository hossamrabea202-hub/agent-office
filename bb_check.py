import unreal, os, glob
EAL=unreal.EditorAssetLibrary
a=EAL.list_assets('/Game/CastleDefender/Gameplay/Realm/_Backup')
f=[(p,os.path.getsize(p)) for p in glob.glob(r'C:/Users/hossa/Documents/BubbleBackups/*')]
open(r'C:/Users/hossa/Documents/agent-office/_bb_out.txt','w').write('assets %s\nfbx %s'%(a,f))
