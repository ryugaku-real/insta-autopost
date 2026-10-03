import { Division } from '../types';

// General rules per association/division (summary; rules change yearly — confirm with each school/association).
export const aidRules: Record<Division, { title: string; points: string[] }> = {
  D1: { title: 'NCAA D1', points: ['アスリート奨学金あり(競技ごとに全額/分割。留学生も対象)', '出願にNCAA Eligibility Centerの登録・認定が必要', 'アイビーリーグは運動奨学金なし(学業・ニーズ型のみ)'] },
  D2: { title: 'NCAA D2', points: ['アスリート奨学金あり(分割型が中心。留学生も対象)', 'NCAA Eligibility Centerの登録が必要'] },
  D3: { title: 'NCAA D3', points: ['アスリート奨学金なし', '学業・経済ニーズ型の奨学金は学校ごとにあり(留学生向けの有無は要確認)'] },
  NAIA: { title: 'NAIA', points: ['アスリート奨学金あり(留学生も対象)', 'NAIA Eligibility Centerの登録が必要'] },
  'NJCAA-D1': { title: 'NJCAA D1', points: ['フル奨学金(授業料・寮・食事・本など)が可能', '留学生も対象。短大から4年制へ編入する人が多い'] },
  'NJCAA-D2': { title: 'NJCAA D2', points: ['授業料・諸費用・本までの奨学金(寮・食事は対象外)', '留学生も対象'] },
  'NJCAA-D3': { title: 'NJCAA D3', points: ['アスリート奨学金なし'] },
  CCCAA: { title: 'CCCAA(カリフォルニア)', points: ['アスリート奨学金は原則なし', '留学生の授業料は州内生より高い。学校独自の奨学金は要確認'] },
  NWAC: { title: 'NWAC(北西部)', points: ['アスリート奨学金は原則なし(学校ごとの授業料免除などは要確認)'] },
};
