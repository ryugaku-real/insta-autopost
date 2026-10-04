export type Association = 'NCAA' | 'NAIA' | 'NJCAA' | 'CCCAA' | 'NWAC';
export type Division = 'D1' | 'D2' | 'D3' | 'NAIA' | 'NJCAA-D1' | 'NJCAA-D2' | 'NJCAA-D3' | 'CCCAA' | 'NWAC';

export interface Sport {
  name: string;      // English, e.g. "Baseball"
  nameJa: string;    // e.g. "野球"
  gender: 'M' | 'W' | 'Both';
}

export interface School {
  id: string;
  name: string;
  nameJa?: string;
  level: '4year' | '2year';
  control: 'public' | 'private';
  city: string;
  state: string;     // 2-letter code
  lat?: number;
  lng?: number;
  association: Association;
  division: Division;
  conference?: string;
  sports: Sport[];
  /** Annual cost in USD (approx.), null if unknown */
  tuitionInState: number | null;
  tuitionOutOfState: number | null;
  /** Total athletics-related student aid reported to the U.S. Dept. of Education (EADA), USD/year */
  athleticAid?: { total: number; men: number; women: number; coed: number };
  /** Average net price after grant aid (College Scorecard), USD/year */
  avgNetPrice?: number | null;
  /** Does the school give athletic scholarships? (D3 and NCAA D1/D2 rules differ) */
  athleticScholarship: boolean;
  /** Maximum athletic scholarship per athlete under this school's association/division rules (text) */
  athleticScholarshipMax?: string;
  /** Cheer / dance / stunt / acrobatics & tumbling programs (text), from the USA Cheer directory and NCAA/NAIA lists */
  cheerNote?: string;
  scholarshipNote?: string;
  website: string;
  /** Athletics department site, when known (NCAA schools) */
  athleticsUrl?: string;
  /** Direct link to the scholarship / international admissions page (from data/overrides.json) */
  scholarshipUrl?: string;
  /** Researched notes on international-student aid/policies (from the data feed's overrides) */
  intlAidNote?: string;
  /** Date (YYYY-MM-DD) the note was checked against the school's site */
  intlAidCheckedAt?: string;
  /** true = generic estimate generated from known data, not individually researched yet */
  intlAidAuto?: boolean;
  /** false = needs manual verification against the official site */
  verified: boolean;
}
