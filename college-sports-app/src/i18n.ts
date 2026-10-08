// Minimal two-language UI helper. `tr(ja, en)` returns the string for the current language.
export type Lang = 'ja' | 'en';
let current: Lang = 'ja';
export const setLang = (l: Lang) => { current = l; };
export const getLang = (): Lang => current;
export const tr = (ja: string, en: string): string => (current === 'en' ? en : ja);

export const detectLang = (): Lang => {
  try {
    const loc = (Intl.DateTimeFormat().resolvedOptions().locale || 'ja').toLowerCase();
    return loc.startsWith('ja') ? 'ja' : 'en';
  } catch { return 'ja'; }
};

export const stateEn: Record<string, string> = {
  AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut',
  DE: 'Delaware', DC: 'Washington, D.C.', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois',
  IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland',
  MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri', MT: 'Montana', NE: 'Nebraska',
  NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York', NC: 'North Carolina',
  ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island',
  SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont', VA: 'Virginia',
  WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming', PR: 'Puerto Rico',
};
