// Agent notifications: polls the office every N minutes and alerts a seat about NEW things for it:
// cafeteria lines marked ">>" (an @mention or a reply to you) and new hand-offs waiting in the editor.
//   node tools/watch.js --seat "<seat>" [--every 5] [--once]
// To ping another agent: node tools/office.js say --seat "<you>" "@<their seat> <message>"  (their watcher fires).
// Output: one line per new item ("NOTIFY ..."), a Windows toast when available, and state in tools/.watch-<seat>.json.
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');
const args = process.argv.slice(2), opt = {};
for (let i = 0; i < args.length; i++) if (args[i].startsWith('--')) opt[args[i].slice(2)] = args[i + 1] && !args[i + 1].startsWith('--') ? args[++i] : true;
if (!opt.seat) { console.error('usage: node tools/watch.js --seat "<seat>" [--every 5] [--once]'); process.exit(1); }
const every = Math.max(1, +opt.every || 5) * 60e3;
const stateFile = path.join(__dirname, '.watch-' + opt.seat.replace(/[^\w]+/g, '_') + '.json');
let seen = new Set();
try { seen = new Set(JSON.parse(fs.readFileSync(stateFile, 'utf8'))); } catch {}

function toast(text) {
  if (process.platform !== 'win32') return;
  const t = text.replace(/'/g, "''").slice(0, 200);
  try {
    execFileSync('powershell', ['-NoProfile', '-Command',
      "[Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime]>$null;" +
      "$x=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(1);" +
      "$x.GetElementsByTagName('text')[0].AppendChild($x.CreateTextNode('Agent Office: " + t + "'))>$null;" +
      "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Agent Office').Show([Windows.UI.Notifications.ToastNotification]::new($x))"],
      { stdio: 'ignore', timeout: 15000 });
  } catch {}
}

function check() {
  let out = '';
  try {
    try { execFileSync('git', ['pull', '-q'], { cwd: path.join(__dirname, '..'), stdio: 'ignore', timeout: 60000 }); } catch {}
    out = execFileSync('node', [path.join(__dirname, 'office.js'), 'inbox', '--seat', opt.seat, '--n', '40'], { encoding: 'utf8', timeout: 120000 });
  } catch (e) { console.log(new Date().toISOString() + ' watch: inbox failed: ' + String(e.message).slice(0, 120)); return; }
  const items = [];
  let section = '';
  for (const line of out.split(/\r?\n/)) {
    if (line.startsWith('==')) { section = line; continue; }
    const chat = line.match(/^>> \[(\d+)\] (.*)$/);
    if (chat) items.push(['chat:' + chat[1], chat[2]]);
    else if (/Hand-offs waiting/.test(section)) { const h = line.match(/^\s+#(\d+)\s+(.*)$/); if (h) items.push(['handoff:' + h[1], 'HAND-OFF #' + h[1] + ' ' + h[2]]); }
  }
  const fresh = items.filter(([k]) => !seen.has(k));
  for (const [k, text] of fresh) { console.log('NOTIFY ' + new Date().toISOString() + ' ' + text.slice(0, 300)); seen.add(k); }
  if (fresh.length) toast(fresh.length + ' new for ' + opt.seat + ': ' + fresh[0][1]);
  else console.log(new Date().toISOString() + ' watch: nothing new');
  try { fs.writeFileSync(stateFile, JSON.stringify([...seen])); } catch {}
}
check();
if (!opt.once) setInterval(check, every);
