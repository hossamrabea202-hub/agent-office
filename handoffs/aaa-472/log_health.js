// #472 Track L (i5): zero-errors policy. Group a UE log's errors and warnings so a Play test gives one short table instead of 678 lines.
// Read-only, works on any CastleDefender.log. Numbers and object suffixes are folded, so repeats of one fault count as one line.
// Usage: node log_health.js <CastleDefender.log> [--warnings] [--top 40]
const fs = require('fs');
const args = process.argv.slice(2);
const file = args.find(a => !a.startsWith('--') && !/^\d+$/.test(a));
if (!file) { console.log('usage: node log_health.js <log> [--warnings] [--top N]'); process.exit(1); }
const top = args.includes('--top') ? +args[args.indexOf('--top') + 1] : 40;
const groups = new Map(); let total = 0, lines = 0;
const want = args.includes('--warnings') ? /(Error|Warning):/ : /Error:/;
const skip = /\[Callstack\]|LogWindows: Error: *$/;
for (const raw of fs.readFileSync(file, 'latin1').split(/\r?\n/)) {
  lines++;
  const l = raw.replace(/^\[[^\]]*\]\[ *\d+\]/, '');
  if (!want.test(l) || skip.test(l)) continue;
  total++;
  const key = l.replace(/[A-Z]:[\\/][^ ]*Intermediate[^ ]*/g, '<path>').replace(/_C_\d+/g, '_C_#').replace(/_UAID_\w+/g, '_#').replace(/0x[0-9A-Fa-f]+/g, '#').replace(/-?\d+(\.\d+)?/g, '#').replace(/\s+/g, ' ').trim().slice(0, 220);
  const g = groups.get(key); if (g) g.n++; else groups.set(key, { n: 1, first: lines });
}
console.log(file.split(/[\\/]/).pop() + ': ' + lines + ' lines, ' + total + ' matching, ' + groups.size + ' distinct');
[...groups].sort((a, b) => b[1].n - a[1].n).slice(0, top).forEach(([k, g]) => console.log(String(g.n).padStart(6) + '  line ' + String(g.first).padEnd(8) + k));
