// Builds the full school list from the free U.S. College Scorecard API
// (location, public/private, 2yr/4yr, tuition). Athletic data (association,
// division, sports) is NOT in Scorecard — merge from data/athletics.csv
// (columns: unitid,association,division,conference,sports) compiled from
// NCAA / NAIA / NJCAA / CCCAA / NWAC official membership lists.
//
//   SCORECARD_API_KEY=xxxx node scripts/build-data.mjs
//   (free key: https://api.data.gov/signup/)
import { writeFileSync, existsSync, readFileSync } from 'node:fs';

const key = process.env.SCORECARD_API_KEY;
if (!key) { console.error('Set SCORECARD_API_KEY'); process.exit(1); }

const fields = [
  'id', 'school.name', 'school.city', 'school.state', 'school.school_url', 'school.ownership',
  'school.degrees_awarded.predominant', 'location.lat', 'location.lon',
  'latest.cost.tuition.in_state', 'latest.cost.tuition.out_of_state',
].join(',');

const ath = new Map();
if (existsSync('data/athletics.csv')) {
  for (const line of readFileSync('data/athletics.csv', 'utf8').trim().split('\n').slice(1)) {
    const [unitid, association, division, conference, sports] = line.split(',');
    ath.set(unitid, { association, division, conference, sports: (sports ?? '').split('|').filter(Boolean) });
  }
}

const out = [];
for (let page = 0; ; page++) {
  const url = `https://api.data.gov/ed/collegescorecard/v1/schools.json?api_key=${key}&per_page=100&page=${page}` +
    `&school.degrees_awarded.predominant=2,3&school.operating=1&fields=${fields}`;
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
      tuitionInState: r['latest.cost.tuition.in_state'], tuitionOutOfState: r['latest.cost.tuition.out_of_state'],
      website: `https://${r['school.school_url']}`, verified: false,
    });
  }
  if ((page + 1) * 100 >= metadata.total) break;
}
writeFileSync('src/data/schools.generated.json', JSON.stringify(out, null, 1));
console.log(`wrote ${out.length} schools`);
