import REQ_EN from './data/engReqEn.json';
import { getLang } from './i18n';

// Translates the researched English-requirement notes (written in Japanese) into English by phrase.
// Notes containing phrases we cannot translate yet are returned as-is (Japanese) with a marker.
const JP = /[぀-ヿ一-鿿ー々]/;
const MONTHS = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const PHRASES: [string, string][] = [
  ['キャンパスにより異なる場合あり', 'may differ by campus'], ['アラバマ州短大システム共通の基準', 'common Alabama community-college system standard'],
  ['各校で差がある場合あり', 'may vary by school'], ['情報源が限定的で要確認', 'limited sources; please verify'],
  ['未満は英語プログラム経由の条件付き入学', 'below this: conditional admission via an English program'],
  ['未満は同校の英語プログラム', 'below this: the school\'s English program'], ['未満は条件付き入学あり', 'below this: conditional admission available'],
  ['公式の最低点なし', 'no official minimum'], ['公式の最低基準', 'official minimum'], ['公式資料間で不一致', 'official sources conflict'],
  ['公式ページ未確認で要確認', 'official page not checked; please verify'], ['公式資料が古く要確認', 'official material is dated; please verify'],
  ['最低点は未確認のため大学に確認', 'minimum not confirmed; ask the school'], ['の最低点は未確認', ' minimum not confirmed'],
  ['の学部基準は未確認', ' undergraduate standard not confirmed'], ['の基準は未確認', ' standard not confirmed'], ['は公式で未確認', ' not confirmed officially'],
  ['基準は未確認', 'standard not confirmed'], ['の扱いは未確認', ' handling not confirmed'], ['情報源により差あり', 'sources differ'], ['資料により差あり', 'sources differ'],
  ['資料により', 'depending on source'], ['情報源により', 'depending on source'], ['第三者サイト情報', 'third-party site info'], ['第三者情報では', 'third-party info says '], ['第三者情報', 'third-party info'],
  ['共通の最低基準', 'common minimum standard'], ['共通の目安', 'common guideline'], ['共通基準', 'common standard'], ['競争的な目安', 'competitive guideline'],
  ['非常に低い基準', 'very low standard'], ['他の短大より高め', 'higher than other community colleges'], ['最低点の設定はなし', 'no minimum set'], ['最低点の設定なし', 'no minimum set'], ['最低点なし', 'no minimum'],
  ['英語テストは任意', 'English test optional'], ['スーパースコア不可', 'no superscoring'], ['入学後に配置テスト', 'placement test after enrollment'], ['配置テストあり', 'placement test required'], ['配置の目安', 'placement guideline'],
  ['以上で入学後の英語テスト免除', ' or higher waives the post-admission English test'], ['以上で免除', ' or higher: waived'], ['で免除の場合あり', ': may be waived'], ['で免除可', ': waivable'],
  ['併修で条件付き可', 'conditional with concurrent English study'], ['条件付き入学あり', 'conditional admission available'], ['条件付き入学', 'conditional admission'], ['条件付き', 'conditional'],
  ['パスウェイ入学は', 'pathway admission: '], ['直接入学', 'direct admission'], ['通常入学', 'regular admission'], ['フル入学', 'full admission'], ['無条件', 'unconditional'],
  ['英語での就学', 'schooling in English'], ['年未満の場合', ' years: '], ['は入学に不要', ' not required for admission'], ['非英語圏の場合', 'if from a non-English-speaking country'],
  ['英語集中プログラム修了でも可', 'or completion of an intensive English program'], ['同校の英語プログラム修了でも可', 'or completion of the school\'s English program'],
  ['他のテストは不可', 'other tests not accepted'], ['ブリッジ課程は', 'bridge program: '], ['提出は推奨', 'submission recommended'], ['必須ではない', 'not required'], ['提出必須', 'test required (minimum not published)'],
  ['以上が目安', ' or higher as a guideline'], ['合格者平均', 'admitted-student average'], ['合格者の目安', 'admitted-student guideline'], ['学部により異なる場合あり', 'may differ by program'], ['学部により', 'depending on program'],
  ['学部の目安', 'undergraduate guideline'], ['総合判断', 'holistic review'], ['医療系は', 'health programs: '], ['工学部は', 'engineering: '], ['看護は', 'nursing: '], ['看護', 'nursing'],
  ['プログラムあり', 'program available'], ['学位課程', 'degree programs'], ['大学院は', 'graduate: '], ['同校の', 'the school\'s '], ['同校', 'the school'], ['以前の基準は', 'earlier standard: '],
  ['月以降は新スケール', ' onward: new scale'], ['月以降の新形式は', ' onward new format: '], ['月以降の新形式', ' onward new format'], ['月より前', ' (before)'], ['日より前', ' (before)'],
  ['新スケールは', 'new scale: '], ['新スケール', 'new scale'], ['新形式', 'new format'], ['新入生', 'freshmen'], ['年生', ' year students'],
  ['等でも代替可', ' etc. also accepted'], ['等で代替可', ' etc. accepted instead'], ['等も可', ' etc. also accepted'], ['でも代替可', ' also accepted instead'], ['で代替可', ' accepted instead'], ['でも可', ' also accepted'], ['も可', ' also accepted'],
  ['ライティング各', 'Writing, each '], ['各セクション', 'each section'], ['各バンド', 'each band'], ['スピーキング', 'Speaking'], ['ライティング', 'Writing'], ['リスニング', 'Listening'], ['リーディング', 'Reading'], ['読解', 'Reading'], ['作文', 'Writing'],
  ['要確認', 'verify'], ['未達は', 'if not met: '], ['未満は', 'below: '], ['推奨値', 'recommended'], ['推奨', 'recommended'], ['以上で', ' or higher: '], ['以上', '+'], ['前後', ' approx.'], ['程度', ' approx.'], ['目安', 'guideline'],
  ['学部', 'undergrad'], ['英語', 'English'], ['英検', 'Eiken'], ['級', ' grade'], ['超', ' over'], ['紙', 'paper '], ['各', 'each '], ['旧', 'old '], ['または', ' or '], ['公式', 'official'],
  ['正規', 'regular'], ['年次', 'year'], ['必須', 'required'], ['経由', 'via'], ['あり', 'available'], ['とも', 'both'], ['基準', 'standard'], ['最低', 'minimum'], ['記載なし', 'not stated'], ['は記載なし', ' not stated'],
  ['不要', 'not required'], ['文理', 'liberal arts'], ['可', ' OK'], ['同', 'same'], ['は', ': '],

  ['第三者情報で', 'third-party sources say '], ['第三者では', 'third-party sources: '], ['第三者で', 'third-party sources: '], ['別情報で', 'other sources say '], ['の基準は未確認', ' standard not confirmed'], ['最低点は未公表', 'minimum score not published'], ['最低点は取得できず', 'minimum score could not be found'],
  ['公式の最低点は未確認', 'official minimum score not confirmed'], ['公式の最低点は未公表', 'official minimum score not published'], ['最低点は公式に明記なし', 'minimum score not stated officially'], ['最低点は明記なし', 'minimum score not stated'], ['英語最低点は公式未確認', 'English minimum not confirmed officially'],
  ['英語要件の公式情報が見つからず', 'no official English requirement info found'], ['英語要件の公式情報なし', 'no official English requirement info'], ['英語要件の情報が見つからず', 'no English requirement info found'], ['公式ページに英語最低点の記載なし', 'official page states no English minimum'],
  ['の記載なし', ' not stated'], ['の記載あり', ' mentioned'], ['の記載もあり要確認', ' also mentioned, verify'], ['の記載もあり', ' also mentioned'], ['の記載のみ', ' mentioned only'], ['の記載', ' mention'], ['任意の記載もあり', 'also described as optional'], ['任意の記載', 'described as optional'],
  ['公式チェックリスト', 'official checklist'], ['公式カタログ', 'official catalog'], ['公式出願書', 'official application form'], ['公式パケット', 'official packet'], ['公式ページ', 'official page'], ['公式で未確認', 'not confirmed officially'], ['公式未確認', 'not confirmed officially'], ['公式・古い可能性', 'official, may be outdated'], ['古い可能性', 'may be outdated'],
  ['入学事務局に要確認', 'check with the admissions office'], ['個別校の公式確認は未了', 'individual school not yet confirmed officially'], ['共通方針で', 'system-wide policy: '], ['共通の目安', 'system-wide guideline'], ['共通方針', 'system-wide policy'], ['共通', 'common'],
  ['年以内のスコア', '-year-old scores or newer'], ['年以内', ' years or less'], ['年有効', '-year validity'], ['年未満の場合', 'if less than '], ['を受付', ' accepted'], ['のみ受付', ' only accepted'], ['提出が必要', 'submission required'], ['提出必須', 'submission required'], ['提出', 'submit'],
  ['入学に不要', 'not required for admission'], ['は入学に不要', ': not required for admission'], ['英語テストは任意', 'English test optional'], ['最低点なし', 'no minimum score'], ['直接入学', 'direct admission'], ['通常入学', 'regular admission'], ['条件付き', 'conditional '],
  ['米高校卒は免除可', 'waived for US high school graduates'], ['以上で免除', ' or higher: waived'], ['等で免除可', ' etc.: may be waived'], ['免除', 'waiver'], ['修了でも可', ' completion also accepted'], ['修了等でも可', ' completion etc. also accepted'], ['修了', 'completion'],
  ['米大学の英作文', 'US college English composition'], ['英語での就学', 'schooling in English'], ['非英語母語者は', 'non-native speakers: '], ['非英語圏出身者は', 'applicants from non-English-speaking countries: '], ['が必須', ' required'], ['配置テスト', 'placement test'], ['競争的な目安', 'competitive guideline'],
  ['とは別校', ': a different school'], ['看護は', 'nursing: '], ['旧カタログで', 'old catalog: '], ['換算は約', 'converts to about '], ['以上推奨', '+ recommended'], ['以上でも可', '+ also accepted'], ['集中英語プログラムあり', 'intensive English program available'], ['集中英語', 'intensive English'], ['州コミュニティカレッジ', 'state community college'], ['州の', 'state '],
  ['受入', 'admission'], ['情報源が一般的で要確認', 'general source, verify'], ['公式の最低基準', 'official minimum standard'], ['英語能力の証明は必須だが最低点は公式未確認', 'English proof required but minimum not confirmed officially'], ['不可', 'not accepted'], ['相当', ' equivalent'], ['なし', 'none'], ['のみ', ' only'], ['等', ' etc.'], ['月', ' month'],
];

const PUNCT: [RegExp, string][] = [[/\u3002/g, '. '], [/\u3001/g, ', '], [/\uFF08/g, ' ('], [/\uFF09/g, ') '], [/\u30FB/g, ' / '], [/\u300C|\u300D/g, '"'], [/\u301C|\uFF5E/g, '–'], [/\uFF1A/g, ': '], [/undergrad\s*:/g, 'Undergrad:']];

export function engPartial(t: string): string {
  let s = t.replace(/(\d{4})年(\d{1,2})月(\d{1,2})日/g, (_m, y, mo, d) => `${MONTHS[+mo]} ${d}, ${y}`).replace(/(\d{4})年(\d{1,2})月/g, (_m, y, mo) => `${MONTHS[+mo]} ${y}`);
  const sorted = [...PHRASES].sort((a, b) => b[0].length - a[0].length);
  for (const [ja, en] of sorted) s = s.split(ja).join(en);
  for (const [re, r] of PUNCT) s = s.replace(re, r);
  return s;
}

export function engText(t: string): string {
  if (getLang() !== 'en') return t;
  const hit = (REQ_EN as Record<string, string>)[t];
  if (hit) return hit;
  let s = t.replace(/(\d{4})年(\d{1,2})月(\d{1,2})日/g, (_m, y, mo, d) => `${MONTHS[+mo]} ${d}, ${y}`).replace(/(\d{4})年(\d{1,2})月/g, (_m, y, mo) => `${MONTHS[+mo]} ${y}`);
  const sorted = [...PHRASES].sort((a, b) => b[0].length - a[0].length);
  for (const [ja, en] of sorted) s = s.split(ja).join(en);
  for (const [re, r] of PUNCT) s = s.replace(re, r);
  if (JP.test(s)) return `(Japanese only for now) ${t}`;
  return s.replace(/\s+([.,)])/g, '$1').replace(/\(\s+/g, '(').replace(/\s{2,}/g, ' ').trim();
}
