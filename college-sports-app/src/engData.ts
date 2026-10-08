import { getLang } from './i18n';
import notesEn from './data/notesEn.json';

const NOTES = notesEn as Record<string, string>;

// Template-based English for the generated (formulaic) parts of the school data.
// Free-form per-school research notes are not translated; callers fall back to the original Japanese.
const JP = /[぀-ヿ一-鿿ー々]/;

const RULES: [RegExp, string][] = [
  [/\(参考: この学校の授業料は年約(\$[\d,]+)\)/g, '(for reference: tuition here is about $1/yr)'],
  // --- cost lines ---
  [/年約(\$[\d,]+)/g, 'about $1/yr'],
  [/教材費: /g, 'Books & supplies: '],
  [/寮・食費\(キャンパス内\): /g, 'Room & board (on campus): '],
  [/留学生の総費用の目安\(授業料・寮食費・教材・生活費、州外料金で換算\): /g, 'Estimated total cost for international students (tuition, room & board, books, living costs; at out-of-state rates): '],
  [/留学生の総費用の目安\(授業料・寮食費・教材・生活費\): /g, 'Estimated total cost for international students (tuition, room & board, books, living costs): '],
  [/授業料・諸費用\(留学生は州外料金が一般的\): /g, 'Tuition & fees (international students usually pay out-of-state rates): '],
  [/授業料・諸費用\(私立は留学生も同額が一般的\): /g, 'Tuition & fees (private schools usually charge international students the same): '],
  [/\(州内の学生は約(\$[\d,]+)\)/g, ' (in-state students: about $1)'],
  // --- verification note ---
  [/リンク先の公式ページで、メモの金額(\d+)件\(全(\d+)件中\)の記載を自動照合で確認済み\(([\d-]+)\)。/g, 'Auto-check: $1 of $2 amounts in our notes were found on the linked official page ($3). '],
  [/リンク先ページは読めましたが、メモの金額を自動照合では確認できませんでした\(別ページの情報やJS表示の可能性\)。公式サイトで要確認\(([\d-]+)\)。/g, 'The linked page could be read, but the amounts in our notes could not be auto-matched (they may be on another page or rendered by JavaScript). Please confirm on the official site ($1). '],
  [/メモに金額の記載がなく、金額の自動照合は未実施です。/g, 'Our notes contain no amounts, so no auto-check was run. '],
  [/リンク先ページに自動アクセスできず、金額は未照合です。公式サイトで要確認\(([\d-]+)\)。/g, 'The linked page could not be accessed automatically, so amounts are unchecked. Please confirm on the official site ($1). '],
  [/専用ページのリンクがないため、金額は未照合です。/g, 'No dedicated page link, so amounts are unchecked. '],
  [/※メモの授業料と米国教育省データ\(上記\)に差があります。年度・料金区分の違いの可能性があるため公式サイトで確認してください。/g, 'Note: tuition in our notes differs from US Dept. of Education data (above); this may be due to year or rate category, so please confirm on the official site.'],
  // --- athletic scholarship max ---
  [/アスリート奨学金は出ません\(最大([$\d%,]+)\)。学業・ニーズ型の奨学金は別途あり。/g, 'No athletic scholarships (max $1). Academic / need-based aid is separate.'],
  [/アイビーリーグは運動奨学金なし\(最大([$\d%,]+)\)。学業・ニーズ型の奨学金のみ\(留学生も対象となる学校が多い\)。/g, 'Ivy League: no athletic scholarships (max $1). Academic / need-based aid only (often open to international students).'],
  [/(\d+)人あたり最大=全額\(授業料・寮・食費・教材などの大学公式の総費用\)。フルライド可/g, 'Max per athlete = full cost of attendance (tuition, room, meals, books, etc.). Full rides possible'],
  [/(\d+)人あたり最大=全額まで可\(ただしチーム全体に上限があり、多くは部分奨学金の分割\)/g, 'Max per athlete = up to full cost (but teams have an overall cap, so most awards are split into partial scholarships)'],
  [/(\d+)人あたり最大=全額まで可\(チーム全体に上限があり、多くは部分奨学金\)/g, 'Max per athlete = up to full cost (teams have an overall cap; most awards are partial)'],
  [/(\d+)人あたり最大=授業料・諸費用・寮・食費・教材・交通費まで\(フル奨学金可\)/g, 'Max per athlete = up to tuition, fees, room, meals, books and travel (full scholarship possible)'],
  [/(\d+)人あたり最大=授業料・諸費用・教材まで\(寮・食費は対象外\)/g, 'Max per athlete = up to tuition, fees and books (room and meals not covered)'],
  [/NWAC\(ワシントン・オレゴンの短大\)の運動奨学金は授業料免除のみで、州内授業料の最大([\d%]+)まで。ただしF-1などの留学生ビザの選手は運動奨学金の対象外\(ブリティッシュ・コロンビア州出身を除く\)なので、留学生の最大は([\d%]+)です。寮・食費・教材費は出ません。/g, 'NWAC (Washington/Oregon community colleges) athletic aid is a tuition waiver only, up to $1 of in-state tuition. Athletes on F-1 and other international visas are not eligible (except those from British Columbia), so the maximum for international students is $2. Room, meals and books are not covered.'],
  [/^あり。/g, 'Yes. '], [/^なし。/g, 'No. '],
  // --- scholarship notes ---
  [/アスリート奨学金は競技・学校により異なります\(Ivy Leagueなど例外あり\)/g, 'Athletic scholarships vary by sport and school (exceptions such as the Ivy League)'],
  [/アスリート奨学金は競技・学校により異なります/g, 'Athletic scholarships vary by sport and school'],
  [/D(\d)はアスリート奨学金なし\(学業・ニーズ型のみ\)/g, 'D$1: no athletic scholarships (academic / need-based aid only)'],
  [/CCCAAは原則アスリート奨学金なし/g, 'CCCAA: generally no athletic scholarships'],
  [/NWACの運動奨学金は授業料免除のみ\(州内授業料の最大([\d%]+)\)、留学生は対象外/g, 'NWAC athletic aid is a tuition waiver only (up to $1 of in-state tuition); international students are not eligible'],
  // --- scholarship sections ---
  [/F-1留学生は米国連邦・州の学費援助\(Pell Grant・連邦ローンなど\)の対象外です。/g, 'F-1 international students are not eligible for US federal or state aid (Pell Grant, federal loans, etc.).'],
  [/本国政府・財団・民間団体の奨学金、保証人の資金、学内就労\(F-1は就労条件あり\)などを組み合わせるのが一般的です。/g, 'Students typically combine home-government, foundation and private scholarships, sponsor funds and on-campus work (F-1 work rules apply).'],
  [/成績基準を明記した制度は確認できていません。この学校の奨学金・留学生向け制度は下の「大学の奨学金・留学生向け制度」を参照してください\(成績・GPAの条件は公式ページで確認\)。/g, 'No scholarship with published grade criteria was found. See "School scholarships / international programs" below (check GPA conditions on the official page).'],
  [/個別の成績・メリット奨学金は確認できていません。短大\(コミュニティカレッジ\)は留学生向けの大型メリット奨学金が少なく、学校財団の小額奨学金\(年(\$?[\d,]+)〜(\$?[\d,]+)程度\)や成績優秀者向けの授業料の一部免除が中心です。学校の国際学生課・奨学金ページで確認してください。/g, 'No individual merit scholarships were found. Community colleges rarely offer large merit awards to international students; small foundation scholarships (about $1–$2 per year) or partial tuition waivers for top students are typical. Check the international office / scholarship page.'],
  [/上記のほか、個別の制度は確認できていません。/g, 'No other individual programs were found.'],
  [/留学生向け(?:の)?奨学金(?:の個別)?情報は見つかりませんでした。/g, 'No scholarship information for international students was found.'],
  [/連邦援助は対象外。/g, 'Not eligible for federal aid.'],
  [/メリット奨学金は無し。/g, 'No merit scholarships.'],
  // --- cheer ---
  [/チア系: /g, 'Cheer: '],
  [/競技チア\(女子\)/g, 'competitive cheer (women)'], [/競技チア\(男女混合\)/g, 'competitive cheer (co-ed)'], [/競技チア/g, 'competitive cheer'],
  [/ゲームデイ\(応援\)チア/g, 'game-day (sideline) cheer'], [/アクロバット&タンブリング/g, 'Acrobatics & Tumbling'],
  [/スタント\(大学の正式競技チーム\)/g, 'STUNT (official varsity team)'],
  [/プログラム掲載情報に「奨学金あり」の記載あり\(額・対象は要確認\)/g, 'program listing mentions scholarships (amount and eligibility to be confirmed)'],
  [/奨学金の有無は要確認/g, 'scholarship availability to be confirmed'], [/奨学金は要確認/g, 'scholarships to be confirmed'], [/奨学金の詳細は要確認/g, 'scholarship details to be confirmed'],
  [/\(情報源: USA Cheerカレッジディレクトリほか。プログラムサイト: /g, '(Source: USA Cheer college directory etc. Program site: '],
  [/\(情報源: USA Cheerカレッジディレクトリ・NCAA\/NAIA公表リスト\)/g, '(Source: USA Cheer college directory and NCAA/NAIA published lists)'],
  [/\(情報源: 各校の運動部・プログラム公式情報ほか。最新は要確認\)/g, '(Source: official athletics / program information; confirm the latest)'],
  [/他の奨学金・学費減免は別途/g, 'other scholarships or fee waivers are separate'], [/は運動奨学金なし/g, ': no athletic scholarships'],
  [/チア・スタント/g, 'cheer / stunt'], [/クラブチーム/g, 'club team'],
  [/・/g, ' / '], [/。/g, '. '], [/、/g, ', '],
];

export const noteEn = (t: string): string | null => (getLang() === 'en' ? NOTES[t] ?? null : null);

export function engData(t: string | undefined | null): string | null {
  if (!t) return t ?? null;
  if (getLang() !== 'en') return t;
  if (NOTES[t]) return NOTES[t];
  let s = t.replace(/（/g, '(').replace(/）/g, ')');
  for (const [re, r] of RULES) s = s.replace(re, r);
  if (JP.test(s)) return null;
  return s.replace(/\(\s+/g, '(').replace(/\s+\)/g, ')').replace(/\s{2,}/g, ' ').trim();
}

/** Translated text if available, otherwise the original (Japanese). `miss` is set when the fallback was used. */
export function dt(t: string, miss?: { n: number }): string {
  const r = engData(t);
  if (r == null) { if (miss) miss.n++; return t; }
  return r;
}

export const sectionTitleEn: Record<string, string> = {
  '連邦・州の学費援助': 'Federal / state aid',
  'アカデミック(成績)奨学金の制度': 'Academic (merit) scholarships',
  '大学の奨学金・留学生向け制度(個別調査)': 'School scholarships / international programs',
  'アスリート奨学金': 'Athletic scholarships',
  '外部奨学金・その他': 'Outside scholarships & other',
};
