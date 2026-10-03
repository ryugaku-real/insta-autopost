// Builds the full school list from the U.S. College Scorecard data
// (location, public/private, 2yr/4yr, tuition). Athletic data (association,
// division, sports) comes from data/athletics.json (see scripts/build-athletics.py, EADA data).
//
//   node scripts/build-data.mjs   (no API key needed: uses the College Scorecard bulk CSV)
import { writeFileSync, existsSync, readFileSync, mkdirSync } from 'node:fs';
import { execSync } from 'node:child_process';

// College Scorecard bulk file (no API key needed): https://collegescorecard.ed.gov/data/
async function loadScorecard() {
  if (!existsSync('scorecard/Most-Recent-Cohorts-Institution.csv')) {
    // Find the current file link on the data page; fall back to the last known file if the page can't be parsed (e.g. bot blocking).
    const FALLBACK = 'https://ed-public-download.scorecard.network/downloads/Most-Recent-Cohorts-Institution_06102026.zip';
    let url = FALLBACK;
    try {
      const res = await fetch('https://collegescorecard.ed.gov/data/');
      const found = (await res.text()).match(/https:\/\/ed-public-download[^"'\s]*Most-Recent-Cohorts-Institution[^"'\s]*\.zip/)?.[0];
      if (found) url = found;
      else console.warn(`link not found on data page (HTTP ${res.status}); using fallback file`);
    } catch (e) { console.warn('data page fetch failed; using fallback file:', e.message); }
    console.log('downloading', url);
    execSync(`rm -rf scorecard && mkdir scorecard && curl -sSfL "${url}" -o scorecard/sc.zip && unzip -q -o scorecard/sc.zip -d scorecard`, { stdio: 'inherit' });
  }
  return parseCsv(readFileSync('scorecard/Most-Recent-Cohorts-Institution.csv', 'utf8'));
}

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

const dom = (u) => (u ?? '').toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0];
// unitid -> { association, division, sports } from scripts/build-athletics.py (EADA data)
const ath = new Map(Object.entries(JSON.parse(readFileSync('data/athletics.json', 'utf8'))));
// optional: NCAA conference names by website domain from scripts/fetch-ncaa.mjs
const conf = new Map();
if (existsSync('data/athletics.csv')) {
  for (const line of readFileSync('data/athletics.csv', 'utf8').trim().split('\n').slice(1)) {
    const [domain, , , conference, , athleticUrl] = line.split(',');
    conf.set(domain, { conference, athleticUrl });
  }
}

// manual fixes for fast-changing facts: { "<unitid>": { conference, athleticsUrl, scholarshipUrl, ... } }
const overrides = existsSync('data/overrides.json') ? JSON.parse(readFileSync('data/overrides.json', 'utf8')) : {};
const out = [];
for (const r of await loadScorecard()) {
  const a = ath.get(r.UNITID);
  if (!a || r.CURROPER !== '1' || !['1', '2', '3'].includes(r.PREDDEG)) continue; // only operating schools with a known athletic program
  const c = conf.get(dom(r.INSTURL));
  const num = (v) => (v && !isNaN(Number(v)) ? Number(v) : null);
  out.push({
    id: r.UNITID, name: r.INSTNM, level: r.PREDDEG === '3' ? '4year' : '2year',
    control: r.CONTROL === '1' ? 'public' : 'private', city: r.CITY, state: r.STABBR,
    lat: num(r.LATITUDE) ?? undefined, lng: num(r.LONGITUDE) ?? undefined, ...a,
    conference: c?.conference || undefined,
    athleticsUrl: c?.athleticUrl ? `https://${c.athleticUrl}` : undefined,
    athleticScholarship: ['D1', 'D2', 'NJCAA-D1', 'NJCAA-D2', 'NAIA'].includes(a.division),
    scholarshipNote: a.division === 'D3' || a.division === 'NJCAA-D3' ? 'D3はアスリート奨学金なし(学業・ニーズ型のみ)'
      : a.association === 'CCCAA' || a.association === 'NWAC' ? `${a.association}は原則アスリート奨学金なし`
      : a.association === 'NCAA' ? 'アスリート奨学金は競技・学校により異なります(Ivy Leagueなど例外あり)' : 'アスリート奨学金は競技・学校により異なります',
    avgNetPrice: num(r.NPT4_PUB) ?? num(r.NPT4_PRIV), tuitionInState: num(r.TUITIONFEE_IN), tuitionOutOfState: num(r.TUITIONFEE_OUT),
    website: /^https?:/.test(r.INSTURL) ? r.INSTURL : `https://${r.INSTURL}`, verified: false,
  });
}
for (const sc of out) Object.assign(sc, overrides[sc.id] ?? {});
mkdirSync('public-data', { recursive: true });
const updatedAt = new Date().toISOString();
writeFileSync('public-data/schools.json', JSON.stringify({ updatedAt, schools: out }));
writeFileSync('src/data/schools.generated.json', JSON.stringify(out)); // bundled fallback for offline first launch
console.log(`wrote ${out.length} schools`);
