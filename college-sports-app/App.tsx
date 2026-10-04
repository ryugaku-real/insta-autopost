import { useMemo, useState } from 'react';
import { FlatList, Linking, Modal, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSchools } from './src/data/useSchools';
import { Division, School } from './src/types';
import { aidRules } from './src/data/aidRules';
import { stateJa } from './src/data/states';
import { CHEER_AID_NOTE, limitHeader, sportLimits } from './src/data/athleticLimits';

const DIVISIONS: { key: Division | 'ALL'; label: string }[] = [
  { key: 'ALL', label: 'すべて' }, { key: 'D1', label: 'NCAA D1' }, { key: 'D2', label: 'NCAA D2' },
  { key: 'D3', label: 'NCAA D3' }, { key: 'NAIA', label: 'NAIA' }, { key: 'NJCAA-D1', label: 'NJCAA D1' },
  { key: 'NJCAA-D2', label: 'NJCAA D2' }, { key: 'NJCAA-D3', label: 'NJCAA D3' },
  { key: 'CCCAA', label: 'CCCAA(CA)' }, { key: 'NWAC', label: 'NWAC(北西部)' },
];

export default function App() {
  const { schools, updatedAt, source } = useSchools();
  const [query, setQuery] = useState('');
  const [division, setDivision] = useState<Division | 'ALL'>('ALL');
  const [level, setLevel] = useState<'ALL' | '4year' | '2year'>('ALL');
  const [scholarshipOnly, setScholarshipOnly] = useState(false);
  const [selected, setSelected] = useState<School | null>(null);
  const [state, setState] = useState<string | null>(null);
  const [conference, setConference] = useState<string | null>(null);
  const [sport, setSport] = useState<string | null>(null);
  const [picker, setPicker] = useState<'state' | 'conf' | 'sport' | null>(null);

  const states = useMemo(() => [...new Set(schools.map((x) => x.state))].sort(), [schools]);
  // conferences available for the currently chosen division (conference data exists for NCAA schools only)
  const conferences = useMemo(
    () => [...new Set(schools.filter((x) => division === 'ALL' || x.division === division).map((x) => x.conference).filter((c): c is string => !!c))].sort(),
    [division, schools]);

  // every sport that appears in the data (incl. cheer/dance/stunt), most common first
  const sportList = useMemo(() => {
    const m = new Map<string, { ja: string; n: number }>();
    for (const x of schools) for (const sp of x.sports) m.set(sp.name, { ja: sp.nameJa, n: (m.get(sp.name)?.n ?? 0) + 1 });
    return [...m.entries()].sort((a, b) => b[1].n - a[1].n).map(([name, v]) => ({ name, ja: v.ja }));
  }, [schools]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    return schools.filter((sc) =>
      (division === 'ALL' || sc.division === division) &&
      (level === 'ALL' || sc.level === level) &&
      (!state || sc.state === state) &&
      (!conference || sc.conference === conference) &&
      (!sport || sc.sports.some((x) => x.name === sport)) &&
      (!scholarshipOnly || sc.athleticScholarship) &&
      (!q || [sc.name, sc.nameJa ?? '', sc.state, sc.city, ...sc.sports.flatMap((x) => [x.name, x.nameJa])]
        .some((t) => t.toLowerCase().includes(q))));
  }, [schools, query, division, level, scholarshipOnly, state, conference, sport]);

  if (selected) return <Detail school={selected} onBack={() => setSelected(null)} />;

  return (
    <View style={st.root}>
      <StatusBar style="auto" />
      <Text style={st.title}>アメリカ大学スポーツ検索</Text>
      <TextInput style={st.input} placeholder="学校名・州・スポーツで検索 (例: 野球, CA)" value={query} onChangeText={setQuery} />
      <FlatList horizontal showsHorizontalScrollIndicator={false} data={DIVISIONS} keyExtractor={(d) => d.key}
        style={st.chips} renderItem={({ item }) => (
          <Chip label={item.label} on={division === item.key} onPress={() => { setDivision(item.key); setConference(null); }} />)} />
      <View style={st.row}>
        <Chip label="4年制" on={level === '4year'} onPress={() => setLevel(level === '4year' ? 'ALL' : '4year')} />
        <Chip label="短大" on={level === '2year'} onPress={() => setLevel(level === '2year' ? 'ALL' : '2year')} />
        <Chip label="アスリート奨学金あり" on={scholarshipOnly} onPress={() => setScholarshipOnly(!scholarshipOnly)} />
      </View>
      <View style={st.row}>
        <Chip label={state ? `州: ${stateJa[state] ?? state}` : '州で絞る ▾'} on={!!state} onPress={() => setPicker('state')} />
        <Chip label={conference ? `リーグ: ${conference}` : 'リーグ(カンファレンス)で絞る ▾'} on={!!conference} onPress={() => setPicker('conf')} />
        <Chip label={sport ? `競技: ${sportList.find((x) => x.name === sport)?.ja ?? sport}` : '競技で絞る(チア含む全競技) ▾'} on={!!sport} onPress={() => setPicker('sport')} />
      </View>
      <Modal visible={picker !== null} animationType="slide" onRequestClose={() => setPicker(null)}>
        <View style={st.root}>
          <Text style={st.title}>{picker === 'state' ? '州を選ぶ' : picker === 'sport' ? '競技を選ぶ' : 'リーグを選ぶ'}</Text>
          {picker === 'conf' && <Text style={st.sub}>※ リーグ名はNCAA加盟校のみ。{division === 'ALL' ? '' : `${division}のリーグを表示中。`}</Text>}
          <FlatList
            data={[null, ...(picker === 'state' ? states : picker === 'sport' ? sportList.map((x) => x.name) : conferences)]}
            keyExtractor={(x) => x ?? 'all'}
            renderItem={({ item }) => (
              <Pressable style={st.pickRow} onPress={() => { picker === 'state' ? setState(item) : picker === 'sport' ? setSport(item) : setConference(item); setPicker(null); }}>
                <Text style={st.name}>{item === null ? 'すべて' : picker === 'state' ? `${stateJa[item] ?? item} (${item})` : picker === 'sport' ? `${sportList.find((x) => x.name === item)?.ja ?? item} (${item})` : item}</Text>
              </Pressable>)} />
          <Pressable onPress={() => setPicker(null)}><Text style={st.link}>閉じる</Text></Pressable>
        </View>
      </Modal>
      <Text style={st.count}>{results.length} 校 ・ データ更新: {updatedAt ? updatedAt.slice(0, 10) : '同梱版'}{source === 'remote' ? '(最新)' : ''}</Text>
      <FlatList data={results} keyExtractor={(x) => x.id} renderItem={({ item }) => (
        <Pressable style={st.card} onPress={() => setSelected(item)}>
          <Text style={st.name}>{item.nameJa ?? item.name}</Text>
          <Text style={st.sub}>{item.name}</Text>
          <Text style={st.meta}>{item.city}, {item.state} ・ {item.level === '4year' ? '4年制' : '短大'} ・ {item.association} {item.division}</Text>
          <Text style={st.meta}>{item.sports.length ? item.sports.map((x) => x.nameJa).join('・') : '競技情報: 準備中'}</Text>
        </Pressable>)} />
    </View>
  );
}

const host = (u: string) => u.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0];
const google = (q: string) => `https://www.google.com/search?q=${encodeURIComponent(q)}`;

function LinkRow({ icon, label, desc, url }: { icon: string; label: string; desc: string; url: string }) {
  return (
    <Pressable onPress={() => Linking.openURL(url)} style={st.linkBox}>
      <Text style={st.link}>{icon} {label}</Text>
      <Text style={st.linkDesc}>{desc}</Text>
    </Pressable>
  );
}

const LEVEL_EXPLAIN: Record<string, string> = {
  D1: 'NCAAで最も競技レベルが高いクラス', D2: 'NCAAの中間クラスで、奨学金が分割で出やすい',
  D3: 'NCAAの学業重視クラス(運動奨学金は出ません)', NAIA: 'NCAAとは別の大学リーグで、小規模校が中心',
  'NJCAA-D1': '短大リーグの最上位でフル奨学金も可能。4年制への編入ルートにもなる',
  'NJCAA-D2': '短大リーグの中位(授業料までの奨学金)', 'NJCAA-D3': '短大リーグ(運動奨学金なし)',
  CCCAA: 'カリフォルニア州の公立短大リーグ(運動奨学金なし)', NWAC: '北西部(ワシントン・オレゴン等)の短大リーグ',
};

function summarize(sc: School) {
  const sports = sc.sports.slice(0, 5).map((x) => x.nameJa).join('・');
  const aid = sc.athleticAid && sc.athleticAid.total > 0 ? `運動部への奨学金は年間およそ$${Math.round(sc.athleticAid.total / 1000).toLocaleString()}K。` : '';
  return `${sc.state}州の${sc.control === 'public' ? '公立' : '私立'}${sc.level === '4year' ? '4年制大学' : '短大'}。` +
    `${sc.division.startsWith(sc.association) ? sc.division : `${sc.association} ${sc.division}`}所属(${LEVEL_EXPLAIN[sc.division]})。` +
    `${sports ? `競技は${sports}など${sc.sports.length}種目。` : ''}` +
    `運動奨学金は${sc.athleticScholarship ? 'あり' : 'なし'}。${aid}`;
}

function Chip({ label, on, onPress }: { label: string; on: boolean; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={[st.chip, on && st.chipOn]}>
      <Text style={on ? st.chipTextOn : st.chipText}>{label}</Text>
    </Pressable>
  );
}

function Detail({ school: sc, onBack }: { school: School; onBack: () => void }) {
  const money = (n: number | null) => (n == null ? '—' : `$${n.toLocaleString()}`);
  return (
    <View style={st.root}>
      <Pressable onPress={onBack}><Text style={st.link}>← 戻る</Text></Pressable>
      <Text style={st.title}>{sc.nameJa ?? sc.name}</Text>
      <Text style={st.sub}>{sc.name}</Text>
      <View style={st.summary}>
        <Text style={st.name}>ひとことで言うと</Text>
        <Text style={st.meta}>{summarize(sc)}</Text>
      </View>
      <Text style={st.meta}>所在地: {sc.city}, {sc.state}</Text>
      <Text style={st.meta}>種別: {sc.level === '4year' ? '4年制' : '短大'} / {sc.control === 'public' ? '公立' : '私立'}</Text>
      <Text style={st.meta}>所属: {sc.association} / {sc.division}{sc.conference ? ` / ${sc.conference}` : ''}</Text>
      <Text style={st.meta}>学費(年): 州内 {money(sc.tuitionInState)} / 州外 {money(sc.tuitionOutOfState)}</Text>
      <Text style={st.meta}>アスリート奨学金: {sc.athleticScholarship ? 'あり' : 'なし'}</Text>
      {(
        <View style={st.summary}>
          <Text style={st.name}>アスリート奨学金の最大額</Text>
          <Text style={st.meta}>{sc.athleticScholarshipMax || (sc.athleticScholarship ? '—' : '$0(運動奨学金なし)')}</Text>
          <Text style={st.linkDesc}>実際の金額は選手ごとに異なります(最大額のみ表示)。</Text>
        </View>)}
      <View style={st.summary}>
        <Text style={st.name}>チア・ダンス・スタント</Text>
        <Text style={st.meta}>{sc.cheerNote ?? '—'}</Text>
        {!!sc.cheerNote && <Text style={st.linkDesc}>{CHEER_AID_NOTE}</Text>}
      </View>
      <Text style={st.meta}>平均ネットプライス(奨学金差引後・米国学生): {money(sc.avgNetPrice ?? null)}/年</Text>
      {sc.tuitionLines && sc.tuitionLines.length > 0 && (
        <View style={st.summary}>
          <Text style={st.name}>学費・費用(留学生の目安)</Text>
          {sc.tuitionLines.map((t) => <Text key={t} style={st.meta}>・{t}</Text>)}
          {!!sc.tuitionResearch && <Text style={[st.meta, { marginTop: 6 }]}>{sc.tuitionResearch}</Text>}
          <Text style={st.linkDesc}>数値は米国教育省(College Scorecard)ベースの概算と個別調査メモです。最新は学校の公式ページで確認してください。</Text>
        </View>)}
      {sc.scholarshipSections && sc.scholarshipSections.length > 0 ? (
        <View style={st.summary}>
          <Text style={st.name}>奨学金制度</Text>
          {sc.scholarshipSections.map((x) => (
            <View key={x.title} style={{ marginTop: 6 }}>
              <Text style={st.meta}>■ {x.title}</Text>
              <Text style={st.meta}>{x.text}</Text>
            </View>))}
          <Text style={st.linkDesc}>確認日: {sc.intlAidCheckedAt ?? '不明'} ・ 最新は必ず学校の公式ページで確認してください</Text>
          {!!sc.verifyNote && <Text style={st.linkDesc}>検証: {sc.verifyNote}</Text>}
        </View>
      ) : sc.intlAidNote ? (
        <View style={st.summary}>
          <Text style={st.name}>{sc.intlAidAuto ? '留学生向け情報(個別調査前の目安)' : '留学生向け情報(調査メモ)'}</Text>
          <Text style={st.meta}>{sc.intlAidNote}</Text>
          <Text style={st.linkDesc}>{sc.intlAidAuto ? '個別の調査は順次進めています' : `確認日: ${sc.intlAidCheckedAt ?? '不明'}`} ・ 最新は必ず学校の公式ページで確認してください</Text>
        </View>) : null}
      <Text style={[st.name, { marginTop: 12 }]}>奨学金ルール({aidRules[sc.division].title})</Text>
      {aidRules[sc.division].points.map((t) => <Text key={t} style={st.meta}>・{t}</Text>)}
      <Text style={[st.name, { marginTop: 12 }]}>スポーツ</Text>
      {sc.sports.map((x) => (
        <Text key={x.name} style={st.meta}>・{x.nameJa} ({x.name}) {x.gender === 'M' ? '男子' : x.gender === 'W' ? '女子' : '男女'}</Text>))}
      <Text style={[st.name, { marginTop: 12 }]}>リンク(タップで開く)</Text>
      <LinkRow icon="🏫" label="学校の公式サイト" desc="学部・学費・キャンパスなど学校全体の情報" url={sc.website} />
      <LinkRow icon="🏅" label="運動部(アスレチックス)サイト" desc={sc.athleticsUrl ? 'チームのスケジュール・コーチ・選手募集の連絡先' : '運動部の公式サイトをGoogleで探します'} url={sc.athleticsUrl ?? google(`${sc.name} athletics official site`)} />
      <LinkRow icon="💰" label={sc.scholarshipUrl ? 'スカラーシップ(奨学金)ページ' : 'スカラーシップ(奨学金)を探す'} desc={sc.scholarshipUrl ? '運動奨学金・留学生向け奨学金の案内ページ' : 'この学校のサイト内から、運動奨学金・留学生向け奨学金のページを検索します'} url={sc.scholarshipUrl ?? google(`site:${host(sc.website)} athletic scholarship international student`)} />
      <LinkRow icon="✈️" label="留学生の出願ページを探す" desc="出願方法・必要書類・英語スコアなど留学生向けの案内を検索します" url={google(`site:${host(sc.website)} international admissions`)} />
      {!sc.verified && <Text style={st.warn}>※ データ出典: 米国教育省 EADA 2024-25 / College Scorecard。奨学金・競技は年度で変わるため、出願前に必ず公式サイトで確認してください。</Text>}
    </View>
  );
}

const st = StyleSheet.create({
  root: { flex: 1, padding: 16, paddingTop: 48, backgroundColor: '#fff' },
  title: { fontSize: 22, fontWeight: '700', marginBottom: 8 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 10, marginBottom: 8 },
  chips: { flexGrow: 0, marginBottom: 6 },
  row: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 6 },
  chip: { borderWidth: 1, borderColor: '#bbb', borderRadius: 16, paddingHorizontal: 12, paddingVertical: 6, marginRight: 6, marginBottom: 6 },
  chipOn: { backgroundColor: '#0a5', borderColor: '#0a5' },
  chipText: { color: '#333' }, chipTextOn: { color: '#fff' },
  count: { color: '#666', marginBottom: 6 },
  card: { borderWidth: 1, borderColor: '#e2e2e2', borderRadius: 10, padding: 12, marginBottom: 10 },
  name: { fontSize: 16, fontWeight: '600' }, sub: { color: '#666', marginBottom: 4 },
  meta: { color: '#333', marginTop: 2 }, link: { color: '#06c', fontSize: 16 }, pickRow: { paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#eee' }, linkBox: { paddingVertical: 8 }, linkDesc: { color: '#666', fontSize: 13, marginTop: 2 }, summary: { backgroundColor: '#f2f8f4', borderRadius: 8, padding: 12, marginVertical: 8 }, linkRow: { color: '#06c', fontSize: 16, paddingVertical: 8 }, warn: { color: '#c60', marginTop: 16 },
});
