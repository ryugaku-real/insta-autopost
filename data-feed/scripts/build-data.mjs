// Builds the full school list from the U.S. College Scorecard data
// (location, public/private, 2yr/4yr, tuition). Athletic data (association,
// division, sports) comes from data/athletics.json (see scripts/build-athletics.py, EADA data).
//
//   node scripts/build-data.mjs   (no API key needed: uses data/scorecard.json)
import { writeFileSync, existsSync, readFileSync, mkdirSync } from 'node:fs';

// College Scorecard institution data. CI runners get HTTP 403 from the Scorecard download hosts, so the needed
// columns are kept in data/scorecard.json (refresh ~yearly with `npm run refresh:scorecard`, run from a normal machine).
async function loadScorecard() {
  return JSON.parse(readFileSync('data/scorecard.json', 'utf8')).rows;
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
console.log(`wrote ${out.length} schools`);
