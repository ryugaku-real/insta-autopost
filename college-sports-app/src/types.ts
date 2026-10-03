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
  scholarshipNote?: string;
  website: string;
  /** Athletics department site, when known (NCAA schools) */
  athleticsUrl?: string;
  /** false = needs manual verification against the official site */
  verified: boolean;
}
