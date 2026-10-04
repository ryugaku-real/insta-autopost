import { Division, School } from '../types';

// Team-level athletic scholarship limits, in "full-scholarship equivalents" (1.0 = one full ride). One athlete can receive up to a full ride.
// NCAA D1: old limits -> new limits from 2025-26 (House v. NCAA settlement; the new limits apply to schools that opt in).
// Sources: scholarshipstats.com (NCAA D1 limits table), NCAA/NAIA published rules. Rules change often: confirm with each coach/school.
type Pair = [number, number]; // [old, new]
type D1Row = { M?: Pair; W?: Pair };
const D1: Record<string, D1Row> = {
  Baseball: { M: [11.7, 34] }, Basketball: { M: [13, 15], W: [15, 15] }, Fencing: { M: [4.5, 24], W: [5, 24] },
  Football: { M: [85, 105] }, Golf: { M: [4.5, 9], W: [6, 9] }, Gymnastics: { M: [6.3, 20], W: [12, 20] },
  'Ice Hockey': { M: [18, 26], W: [18, 26] }, Lacrosse: { M: [12.6, 48], W: [12, 38] }, Skiing: { M: [6.3, 16], W: [7, 16] },
  Soccer: { M: [9.9, 28], W: [14, 28] }, Swimming: { M: [9.9, 30], W: [14, 30] }, Tennis: { M: [4.5, 10], W: [8, 10] },
  Track: { M: [12.6, 62], W: [18, 62] }, Volleyball: { M: [4.5, 18], W: [12, 18] }, 'Water Polo': { M: [4.5, 24], W: [8, 24] },
  Wrestling: { M: [9.9, 30], W: [10, 30] }, 'Beach Volleyball': { W: [6, 19] }, Bowling: { W: [5, 11] }, Equestrian: { W: [15, 50] },
  'Field Hockey': { W: [12, 27] }, Rowing: { W: [20, 68] }, Softball: { W: [12, 25] }, Rifle: { M: [3.6, 12], W: [3.6, 12] },
  'Acrobatics & Tumbling': { W: [14, 55] }, STUNT: { W: [14, 65] },
};
// NCAA D2 / NAIA: team caps in full-scholarship equivalents (approximate; by sport, both genders unless noted).
const D2: Record<string, string> = {
  Football: '36', Basketball: '10', Baseball: '9', Softball: '7.2', Volleyball: '8', Soccer: '男子9 / 女子9.9', Wrestling: '9',
  Golf: '男子3.6 / 女子5.4', Tennis: '男子4.5 / 女子6', Track: '12.6', Lacrosse: '男子10.8 / 女子9.9', Swimming: '8.1',
};
const NAIA: Record<string, string> = {
  Football: '24', Basketball: '11(NAIA D1) / 6(NAIA D2)', Baseball: '12', Softball: '10', Soccer: '12', Volleyball: '8',
  Track: '12', Wrestling: '8', Golf: '5', Tennis: '5', Swimming: '8', Cheerleading: '12(競技チア)',
};

// map the data's sport names onto the limit tables
const key = (name: string): string => {
  if (/^Track|Cross Country/.test(name)) return 'Track';
  if (/^Swimming|^Diving/.test(name)) return 'Swimming';
  return name;
};

export function sportLimits(sc: School): string[] {
  const rows: string[] = [];
  const seen = new Set<string>();
  for (const sp of sc.sports) {
    const k = key(sp.name);
    if (seen.has(k + sp.gender)) continue;
    seen.add(k + sp.gender);
    const label = k === 'Track' ? '陸上・クロスカントリー' : k === 'Swimming' ? '水泳・飛込' : sp.nameJa;
    if (sc.division === 'D1') {
      const r = D1[k];
      if (!r) continue;
      const g = (x: 'M' | 'W', jp: string) => r[x] ? `${jp}${r[x]![0]}→${r[x]![1]}人分` : null;
      const t = [g('M', '男子'), g('W', '女子')].filter(Boolean).join(' / ');
      if (t) rows.push(`${label}: ${t}${k === 'Football' ? '(FCSは旧63)' : ''}`);
    } else if (sc.division === 'D2') {
      if (D2[k]) rows.push(`${label}: ${D2[k]}人分`);
    } else if (sc.division === 'NAIA') {
      if (NAIA[k]) rows.push(`${label}: ${NAIA[k]}人分`);
    }
  }
  return rows;
}

export const limitHeader: Partial<Record<Division, string>> = {
  D1: 'チーム全体の奨学金上限(フルライド何人分か。旧上限→新上限=2025-26の新ルール。新ルールは対応した学校のみ)',
  D2: 'チーム全体の奨学金上限(フルライド何人分か。目安)',
  NAIA: 'チーム全体の奨学金上限(フルライド何人分か。目安)',
};

export const CHEER_AID_NOTE = 'チア・ダンス: NCAAで正式競技のスタント/アクロバット&タンブリングはD1で旧14→新55〜65人分、NAIAの競技チアは12人分。ゲームデイ(応援)チアは学校独自の少額〜部分奨学金が一般的で、学校ごとに大きく異なります。';
