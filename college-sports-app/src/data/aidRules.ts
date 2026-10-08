import { Division } from '../types';

// General rules per association/division (summary; rules change yearly — confirm with each school/association).
export const aidRules: Record<Division, { title: string; points: string[]; pointsEn: string[] }> = {
  D1: { title: 'NCAA D1', points: ['アスリート奨学金あり(競技ごとに全額/分割。留学生も対象)', '出願にNCAA Eligibility Centerの登録・認定が必要', 'アイビーリーグは運動奨学金なし(学業・ニーズ型のみ)'], pointsEn: ["Athletic scholarships available (full or partial by sport; international students eligible)", "Registration/certification with the NCAA Eligibility Center is required to apply", "Ivy League schools give no athletic scholarships (academic/need-based aid only)"] },
  D2: { title: 'NCAA D2', points: ['アスリート奨学金あり(分割型が中心。留学生も対象)', 'NCAA Eligibility Centerの登録が必要'], pointsEn: ["Athletic scholarships available (mostly partial; international students eligible)", "NCAA Eligibility Center registration is required"] },
  D3: { title: 'NCAA D3', points: ['アスリート奨学金なし', '学業・経済ニーズ型の奨学金は学校ごとにあり(留学生向けの有無は要確認)'], pointsEn: ["No athletic scholarships", "Academic / need-based aid varies by school (check whether it is open to international students)"] },
  NAIA: { title: 'NAIA', points: ['アスリート奨学金あり(留学生も対象)', 'NAIA Eligibility Centerの登録が必要'], pointsEn: ["Athletic scholarships available (international students eligible)", "NAIA Eligibility Center registration is required"] },
  'NJCAA-D1': { title: 'NJCAA D1', points: ['フル奨学金(授業料・寮・食事・本など)が可能', '留学生も対象。短大から4年制へ編入する人が多い'], pointsEn: ["Full scholarships possible (tuition, room, meals, books, etc.)", "International students eligible. Many transfer from junior college to 4-year schools"] },
  'NJCAA-D2': { title: 'NJCAA D2', points: ['授業料・諸費用・本までの奨学金(寮・食事は対象外)', '留学生も対象'], pointsEn: ["Aid up to tuition, fees and books (room and meals not covered)", "International students eligible"] },
  'NJCAA-D3': { title: 'NJCAA D3', points: ['アスリート奨学金なし'], pointsEn: ["No athletic scholarships"] },
  CCCAA: { title: 'CCCAA(カリフォルニア)', points: ['アスリート奨学金は原則なし', '留学生の授業料は州内生より高い。学校独自の奨学金は要確認'], pointsEn: ["Generally no athletic scholarships", "International tuition is higher than in-state; check school-specific scholarships"] },
  NWAC: { title: 'NWAC(北西部)', points: ['アスリート奨学金は原則なし(学校ごとの授業料免除などは要確認)'], pointsEn: ["Generally no athletic scholarships (check school-specific tuition waivers)"] },
};
