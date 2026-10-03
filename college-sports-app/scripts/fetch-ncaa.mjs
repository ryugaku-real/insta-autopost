// Writes data/athletics.csv rows for NCAA D1/D2/D3 from the public NCAA directory API.
// Columns: domain,association,division,conference,sports,athleticUrl  (sports left empty: not in this API)
import { writeFileSync, mkdirSync } from 'node:fs';
const dom = (u) => (u ?? '').toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0];
const rows = ['domain,association,division,conference,sports,athleticUrl'];
for (const [d, label] of [['I', 'D1'], ['II', 'D2'], ['III', 'D3']]) {
  const res = await fetch(`https://web3.ncaa.org/directory/api/directory/memberList?type=12&division=${d}`);
  for (const m of await res.json()) {
    if (m.deactive === 'Y' || !m.webSiteUrl) continue;
    rows.push([dom(m.webSiteUrl), 'NCAA', label, (m.conferenceName ?? '').trim().replace(/,/g, ''), '', (m.athleticWebUrl ?? '').trim()].join(','));
  }
}
mkdirSync('data', { recursive: true });
writeFileSync('data/athletics.csv', rows.join('\n') + '\n');
console.log(`wrote ${rows.length - 1} NCAA rows`);
