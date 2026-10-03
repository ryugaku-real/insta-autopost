// Builds the full school list from the free U.S. College Scorecard API
// (location, public/private, 2yr/4yr, tuition). Athletic data (association,
// division, sports) comes from data/athletics.json (see scripts/build-athletics.py, EADA data).
//
//   SCORECARD_API_KEY=xxxx node scripts/build-data.mjs
//   (free key: https://api.data.gov/signup/)
import { writeFileSync, existsSync, readFileSync, mkdirSync } from 'node:fs';

const key = process.env.SCORECARD_API_KEY;
if (!key) { console.error('Set SCORECARD_API_KEY'); process.exit(1); }

const fields = [
  'id', 'school.name', 'school.city', 'school.state', 'school.school_url', 'school.ownership',
  'school.degrees_awarded.predominant', 'location.lat', 'location.lon',
  'latest.cost.tuition.in_state', 'latest.cost.tuition.out_of_state', 'latest.cost.avg_net_price.overall',
].join(',');

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
for (let page = 0; ; page++) {
  const url = `https://api.data.gov/ed/collegescorecard/v1/schools.json?api_key=${key}&per_page=100&page=${page}` +
    `&school.degrees_awarded.predominant=1,2,3&school.operating=1&fields=${fields}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  const { results, metadata } = await res.json();
  for (const r of results) {
    const a = ath.get(String(r.id));
    if (!a) continue; // only schools with a known athletic program
    out.push({
      id: String(r.id), name: r['school.name'], level: r['school.degrees_awarded.predominant'] === 3 ? '4year' : '2year',
      control: r['school.ownership'] === 1 ? 'public' : 'private', city: r['school.city'], state: r['school.state'],
      lat: r['location.lat'], lng: r['location.lon'], ...a,
      conference: conf.get(dom(r['school.school_url']))?.conference || undefined,
      athleticsUrl: conf.get(dom(r['school.school_url']))?.athleticUrl ? `https://${conf.get(dom(r['school.school_url'])).athleticUrl}` : undefined,
      avgNetPrice: r['latest.cost.avg_net_price.overall'], tuitionInState: r['latest.cost.tuition.in_state'], tuitionOutOfState: r['latest.cost.tuition.out_of_state'],
      athleticScholarship: ['D1', 'D2', 'NJCAA-D1', 'NJCAA-D2', 'NAIA'].includes(a.division),
      scholarshipNote: a.division === 'D3' || a.division === 'NJCAA-D3' ? 'D3はアスリート奨学金なし(学業・ニーズ型のみ)' : a.association === 'CCCAA' || a.association === 'NWAC' ? `${a.association}は原則アスリート奨学金なし` : a.association === 'NCAA' ? 'アスリート奨学金は競技・学校により異なります(Ivy Leagueなど例外あり)' : 'アスリート奨学金は競技・学校により異なります',
      website: /^https?:/.test(r['school.school_url']) ? r['school.school_url'] : `https://${r['school.school_url']}`, verified: false,
    });
  }
  if ((page + 1) * 100 >= metadata.total) break;
}
for (const sc of out) Object.assign(sc, overrides[sc.id] ?? {});
mkdirSync('public-data', { recursive: true });
const updatedAt = new Date().toISOString();
writeFileSync('public-data/schools.json', JSON.stringify({ updatedAt, schools: out }));
writeFileSync('src/data/schools.generated.json', JSON.stringify(out)); // bundled fallback for offline first launch
console.log(`wrote ${out.length} schools`);
