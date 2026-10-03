// Refreshes data/scorecard.json from the College Scorecard bulk CSV. Run ~once a year from a normal machine
// (GitHub-hosted runners are blocked by the download host).   npm run refresh:scorecard
import { writeFileSync, readFileSync } from 'node:fs';
import { execSync } from 'node:child_process';

const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';
const page = await (await fetch('https://collegescorecard.ed.gov/data/', { headers: { 'User-Agent': UA } })).text();
const url = page.match(/https:\/\/ed-public-download[^"'\s]*Most-Recent-Cohorts-Institution[^"'\s]*\.zip/)?.[0];
if (!url) throw new Error('Scorecard institution file link not found');
console.log('downloading', url);
execSync(`rm -rf scorecard && mkdir scorecard && curl -sSfL -A "${UA}" "${url}" -o scorecard/sc.zip && unzip -q -o scorecard/sc.zip -d scorecard`, { stdio: 'inherit' });

function parseCsv(text) {
  const rows = []; let row = [], f = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (q) { if (ch === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += ch; }
    else if (ch === '"') q = true;
    else if (ch === ',') { row.push(f); f = ''; }
    else if (ch === '\n') { row.push(f.replace(/\r$/, '')); rows.push(row); row = []; f = ''; }
    else f += ch;
  }
  if (f || row.length) { row.push(f); rows.push(row); }
  const h = rows.shift().map((x) => x.replace(/^\uFEFF/, ''));
  return rows.filter((r) => r.length === h.length).map((r) => Object.fromEntries(h.map((k, i) => [k, r[i]])));
}
const KEEP = ['UNITID', 'INSTNM', 'CITY', 'STABBR', 'INSTURL', 'PREDDEG', 'CONTROL', 'LATITUDE', 'LONGITUDE', 'CURROPER', 'NPT4_PUB', 'NPT4_PRIV', 'TUITIONFEE_IN', 'TUITIONFEE_OUT'];
const rows = parseCsv(readFileSync('scorecard/Most-Recent-Cohorts-Institution.csv', 'utf8'))
  .filter((r) => r.CURROPER === '1' && ['1', '2', '3'].includes(r.PREDDEG))
  .map((r) => Object.fromEntries(KEEP.map((k) => [k, r[k]])));
writeFileSync('data/scorecard.json', JSON.stringify({ source: url, fetchedAt: new Date().toISOString(), rows }));
console.log(`wrote ${rows.length} institutions`);
