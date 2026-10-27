/* Codex asset library: shared files, independent of the office's browser-local agent records. */
(()=>{'use strict';
const script=document.currentScript;
const base=new URL('./',script.src);
const part=new URL('Obsidian-Sovereign/Helmet/',base);
const repo='https://github.com/hossamrabea202-hub/agent-office';
const archive=repo+'/releases/download/helmet-wip-2026-10-27/Obsidian_Sovereign_Helmet_WIP_2026-10-27.zip';
const grid=document.getElementById('assetGrid');
if(!grid||document.getElementById('codex-assets'))return;
const style=document.createElement('style');
style.textContent=`
.codex-asset-folder{display:flex;align-items:center;gap:calc(6*var(--u));padding:calc(4*var(--u)) calc(7*var(--u));border:1px solid #c49b59;border-radius:6px;background:#30283d;color:#f1dfb5;font-size:calc(10*var(--u));text-align:left;cursor:pointer}
.codex-asset-folder img{width:calc(34*var(--u));height:calc(34*var(--u));min-width:24px;min-height:24px;object-fit:cover;border-radius:4px}
.codex-asset-folder span{display:grid;gap:2px}.codex-asset-folder small{font-size:.85em;color:#c9bbd6}
#codex-assets{background:#141d2b;color:#e9edf3;border:1px solid #b18b50;border-radius:14px;width:min(800px,calc(100% - 28px));max-height:88vh;padding:22px;box-shadow:0 20px 70px #000a}
#codex-assets::backdrop{background:#060b14d9}
#codex-assets .ca-head{display:flex;align-items:start;justify-content:space-between;gap:16px}
#codex-assets h2{margin:3px 0 16px;font-size:23px}#codex-assets h3{margin:0 0 7px}
#codex-assets .ca-breadcrumb{display:flex;gap:7px;flex-wrap:wrap;align-items:center;color:#a9b9cc;font-size:12px}
#codex-assets .ca-breadcrumb button{border:0;background:none;padding:2px 0;color:#dfb874;font-size:12px}
#codex-assets .ca-folder{display:flex;align-items:center;gap:14px;width:100%;padding:15px;text-align:left;background:#1c293d;border:1px solid #455674;border-radius:10px;margin:10px 0}
#codex-assets .ca-folder img{width:74px;height:74px;object-fit:cover;border-radius:7px;border:1px solid #78603a}
#codex-assets .ca-folder .ca-label{display:grid;gap:6px}#codex-assets .ca-folder strong{font-size:18px;color:#e8c784}
#codex-assets .ca-muted{color:#a9b9cc;line-height:1.6;font-size:13px}
#codex-assets .ca-hero{display:grid;grid-template-columns:minmax(180px,.85fr) 1.15fr;gap:22px;align-items:start}
#codex-assets .ca-preview{width:100%;border-radius:9px;background:#0d1521;border:1px solid #40506a}
#codex-assets .ca-badge{display:inline-block;padding:5px 8px;border:1px solid #936d3c;background:#342b1d;color:#f0cf94;border-radius:6px;font-size:11px;margin-bottom:12px}
#codex-assets .ca-files{display:grid;gap:9px;margin:15px 0}
#codex-assets .ca-files a{color:#e9c783;border:1px solid #465674;border-radius:7px;padding:10px 12px;text-decoration:none;background:#1b2940;font-size:13px}
#codex-assets .ca-files a:hover{background:#293d58}#codex-assets a:focus-visible,#codex-assets button:focus-visible{outline:2px solid #ebc77f;outline-offset:3px}
#codex-assets .ca-note{padding:12px;background:#211f1b;border-left:3px solid #b38b4e;line-height:1.6;font-size:12px;color:#d9c6a6;margin-top:16px}
#codex-assets .ca-folder-glyph{font-size:38px;color:#d9af65;line-height:1}
@media(max-width:580px){#codex-assets{padding:15px}#codex-assets .ca-hero{grid-template-columns:1fr}#codex-assets .ca-preview{max-width:270px;justify-self:center}}
`;
document.head.append(style);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const launch=document.createElement('button');launch.type='button';launch.className='codex-asset-folder';launch.setAttribute('aria-label','Open Codex asset folder');
launch.innerHTML='<img src="'+new URL('icon.png',part).href+'" alt="Black and gold Obsidian Sovereign helmet"><span><b>Codex</b><small id="codex-count">Shared WIP assets</small></span>';
grid.prepend(launch);
const dialog=document.createElement('dialog');dialog.id='codex-assets';dialog.setAttribute('aria-labelledby','ca-title');document.body.append(dialog);
const crumb=(name,route)=>'<button type="button" data-ca="'+esc(route)+'">'+esc(name)+'</button>';
const safe=(value,parent)=>{const u=new URL(value,parent);if(!['https:','http:'].includes(u.protocol))throw new Error('Unsupported asset URL');return esc(u.href)};
const bytes=n=>Number.isFinite(n)?' · '+(n/1e6).toFixed(n<1e6?2:1)+' MB':'';
let sets=[],serial=0;
async function json(url){const u=new URL(url);u.searchParams.set('v',String(Date.now()));const r=await fetch(u,{cache:'no-store'});if(!r.ok)throw new Error('Asset information is temporarily unavailable. Please try again.');return r.json()}
async function catalogue(){const data=await json(new URL('catalog.json',base));sets=data.sets||[];document.getElementById('codex-count').textContent=sets.length+' set · '+sets.reduce((n,s)=>n+s.parts.length,0)+' groups · WIP'}
function frame(title,trail,body){dialog.innerHTML='<div class="ca-head"><div><nav class="ca-breadcrumb" aria-label="Asset folders">'+trail+'</nav><h2 id="ca-title">'+esc(title)+'</h2></div><button type="button" data-ca="close" aria-label="Close Codex assets">Close</button></div>'+body}
async function render(route){
 const ticket=++serial;const segments=route.split(':');const si=Number(segments[1]||0),pi=Number(segments[2]||0);let trail=crumb('3D Assets','close')+'<span>/</span>';
 if(route==='root'){
  trail+='<span>Codex</span>';frame('Codex',trail,'<p class="ca-muted">Shared model files and editable handoffs created by Codex.</p>'+sets.map((s,i)=>'<button type="button" class="ca-folder" data-ca="set:'+i+'"><span class="ca-folder-glyph" aria-hidden="true">📁</span><span class="ca-label"><strong>'+esc(s.name)+'</strong><span class="ca-muted">'+s.parts.length+' uploaded equipment groups · work in progress</span></span></button>').join(''));return;
 }
 const set=sets[si];if(!set)return;
 if(segments[0]==='set'){
  trail+=crumb('Codex','root')+'<span>/</span><span>'+esc(set.name)+'</span>';
  frame(set.name,trail,'<p class="ca-muted">Each folder contains actual model files, preview images and takeover notes. Left/right pieces remain separate equipment objects. Final character fit and skinning are pending.</p>'+set.parts.map((p,i)=>'<button type="button" class="ca-folder" data-ca="part:'+si+':'+i+'"><img loading="lazy" src="'+safe(p.icon,base)+'" alt="'+esc(p.name)+' preview"><span class="ca-label"><strong>'+esc(p.name)+'</strong><span class="ca-muted">FBX · textured GLB · authoring handoff</span><span class="ca-muted">Geometry checked · unskinned WIP</span></span></button>').join(''));return;
 }
 const entry=set.parts[pi];if(!entry)return;const manifest=new URL(entry.manifest,base);const folder=new URL('./',manifest);
 trail+=crumb('Codex','root')+'<span>/</span>'+crumb(set.name,'set:'+si)+'<span>/</span><span>'+esc(entry.name)+'</span>';frame(entry.name,trail,'<p class="ca-muted">Loading model information…</p>');
 const m=await json(manifest);if(ticket!==serial)return;
 const files=m.geometries||[m.geometry];const triangles=m.triangles_per_piece||m.triangles;
 const actions=files.map((file,i)=>'<a href="'+safe(file,folder)+'" download>Download '+(files.length===2?(i===0?'left':'right')+' FBX':'FBX geometry')+bytes(m.geometry_bytes?.[file])+'</a>').join('')+'<a href="'+safe(m.review_model,folder)+'" download>Download textured GLB preview'+bytes(m.review_bytes)+'</a>'+(m.package_available!==false?'<a href="'+safe(m.package_url,folder)+'">Download editable Blender / 4K master'+bytes(m.package_bytes)+'</a>':'<p class="ca-muted">Editable master archive upload is in progress. The FBX and GLB files above are available now.</p>')+'<a href="'+repo+'/blob/main/'+esc(m.folder)+'/README.md" target="_blank" rel="noopener">Read takeover instructions ↗</a><a href="'+repo+'/blob/main/'+esc(m.folder)+'/'+esc(m.validation||'validation.json')+'" target="_blank" rel="noopener">Read geometry and bake validation ↗</a><a href="'+repo+'/issues/1" target="_blank" rel="noopener">Project-PC reference-export task ↗</a>';
 frame(entry.name,trail,'<div class="ca-hero"><img class="ca-preview" src="'+safe(m.preview,folder)+'" alt="Rendered '+esc(entry.name)+'"><div><span class="ca-badge">WORK IN PROGRESS · UNSKINNED</span><h3>'+esc(set.name+' — '+entry.name)+'</h3><p class="ca-muted">'+Number(triangles).toLocaleString()+' triangles per piece · one connected material shell per piece. '+(m.master_texture_resolution||4096)/1024+'K master maps; '+(m.review_texture_resolution||2048)/1024+'K preview maps.</p><div class="ca-files">'+actions+'</div></div></div><div class="ca-note">Reference fidelity, final fit, skinning, articulation or cloth behavior, and Unreal Engine import remain unapproved. Keep the extracted Blender project and textures together when another agent takes over.</div>');
}
function fail(e){frame('Codex',crumb('3D Assets','close'),'<p class="ca-muted">'+esc(e.message)+'</p><p><a href="'+repo+'/tree/main/assets/Codex" target="_blank" rel="noopener">Open the shared files on GitHub ↗</a></p>')}
launch.addEventListener('click',async()=>{frame('Codex',crumb('3D Assets','close'),'<p class="ca-muted">Loading shared folders…</p>');dialog.showModal();try{await catalogue();await render('root')}catch(e){fail(e)}});
dialog.addEventListener('click',ev=>{if(ev.target===dialog){dialog.close();return}const b=ev.target.closest('[data-ca]');if(!b)return;if(b.dataset.ca==='close'){serial++;dialog.close()}else render(b.dataset.ca).catch(fail)});
catalogue().catch(()=>{});
})();