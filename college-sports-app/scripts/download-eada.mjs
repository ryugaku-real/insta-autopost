// Downloads the latest EADA single-year zip from the U.S. Dept. of Education and unzips into eada/ (used by CI).
import { execSync } from 'node:child_process';
const list = await (await fetch('https://ope.ed.gov/athletics/api/dataFiles/fileList')).json();
const f = list.filter((x) => /^EADA_\d{4}-\d{4}\.zip$/.test(x.FileName)).sort((a, b) => b.Year - a.Year)[0];
if (!f) throw new Error('no EADA file found');
console.log('using', f.FileName);
execSync(`curl -sSfL "https://ope.ed.gov/athletics/api/dataFiles/file?fileName=${f.FileName}" -o eada.zip && rm -rf eada && mkdir eada && unzip -q eada.zip -d eada`, { stdio: 'inherit' });
