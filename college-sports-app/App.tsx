import { useEffect, useMemo, useState } from 'react';
import { FlatList, Linking, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
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
  const [divisions, setDivisions] = useState<Division[]>([]);
  const [level, setLevel] = useState<'ALL' | '4year' | '2year'>('ALL');
  const [scholarshipOnly, setScholarshipOnly] = useState(false);
  const [selected, setSelected] = useState<School | null>(null);
  const [stateSel, setStateSel] = useState<string[]>([]);
  const [confSel, setConfSel] = useState<string[]>([]);
  const [sportSel, setSportSel] = useState<string[]>([]);
  const [picker, setPicker] = useState<'state' | 'conf' | 'sport' | null>(null);
  const [sortKey, setSortKey] = useState<'name' | 'cost' | 'pct'>('name');
  const [maxCost, setMaxCost] = useState<number | null>(null);
  const [favs, setFavs] = useState<string[]>([]);
  const [favOnly, setFavOnly] = useState(false);
  const [cmp, setCmp] = useState<string[]>([]);
  const [showCmp, setShowCmp] = useState(false);
  const toggleIn = <T,>(set: (f: (c: T[]) => T[]) => void, v: T) => set((c) => (c.includes(v) ? c.filter((x) => x !== v) : [...c, v]));
  // cheer details are shown only while a cheer-type sport is selected in the sport filter
  const cheerSelected = sportSel.some((n) => ['Cheerleading', 'Dance', 'STUNT', 'Acrobatics & Tumbling'].includes(n));
  const toggleCmp = (id: string) => setCmp((c) => c.includes(id) ? c.filter((x) => x !== id) : c.length >= 3 ? c : [...c, id]);
  useEffect(() => { AsyncStorage.getItem('favs').then((v) => { if (v) setFavs(JSON.parse(v)); }).catch(() => {}); }, []);
  const toggleFav = (id: string) => setFavs((cur) => {
    const next = cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id];
    AsyncStorage.setItem('favs', JSON.stringify(next)).catch(() => {});
    return next;
  });

  const states = useMemo(() => [...new Set(schools.map((x) => x.state))].sort(), [schools]);
  // conferences available for the currently chosen division (conference data exists for NCAA schools only)
  const conferences = useMemo(
    () => [...new Set(schools.filter((x) => divisions.length === 0 || divisions.includes(x.division)).map((x) => x.conference).filter((c): c is string => !!c))].sort(),
    [divisions, schools]);

  // every sport that appears in the data (incl. cheer/dance/stunt), most common first
  const sportList = useMemo(() => {
    const m = new Map<string, { ja: string; n: number }>();
    for (const x of schools) for (const sp of x.sports) m.set(sp.name, { ja: sp.nameJa, n: (m.get(sp.name)?.n ?? 0) + 1 });
    return [...m.entries()].sort((a, b) => b[1].n - a[1].n).map(([name, v]) => ({ name, ja: v.ja }));
  }, [schools]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    const nq = q.replace(/[\s_-]+/g, '');
    const list = schools.filter((sc) =>
      (divisions.length === 0 || divisions.includes(sc.division)) &&
      (!favOnly || favs.includes(sc.id)) &&
      (maxCost == null || (sc.tuitionOutOfState != null && sc.tuitionOutOfState <= maxCost)) &&
      (level === 'ALL' || sc.level === level) &&
      (stateSel.length === 0 || stateSel.includes(sc.state)) &&
      (confSel.length === 0 || (!!sc.conference && confSel.includes(sc.conference))) &&
      (sportSel.length === 0 || sportSel.every((n) => sc.sports.some((x) => x.name === n))) &&
      (!scholarshipOnly || sc.athleticScholarship) &&
      (!q || [sc.name, sc.nameJa ?? '', sc.state, sc.city, ...sc.sports.flatMap((x) => [x.name, x.nameJa])]
        .some((t) => t.toLowerCase().includes(q)) ||
        [`${sc.association}${sc.division}`, sc.division, sc.association].some((t) => t.toLowerCase().replace(/[\s_-]+/g, '').includes(nq))));
    if (sortKey === 'cost') list.sort((a, b) => (a.tuitionOutOfState ?? Infinity) - (b.tuitionOutOfState ?? Infinity));
    else if (sortKey === 'pct') list.sort((a, b) => (b.athleticScholarshipPct ?? -1) - (a.athleticScholarshipPct ?? -1));
    return list;
  }, [schools, query, divisions, level, scholarshipOnly, stateSel, confSel, sportSel, maxCost, favOnly, favs, sortKey]);

  if (showCmp) return <Compare showCheer={cheerSelected} list={schools.filter((x) => cmp.includes(x.id))} onBack={() => setShowCmp(false)} onRemove={toggleCmp} />;
  if (selected) return <Detail school={selected} showCheer={cheerSelected} onBack={() => setSelected(null)} fav={favs.includes(selected.id)} onFav={() => toggleFav(selected.id)} />;

  return (
    <View style={st.root}>
      <StatusBar style="auto" />
      <Text style={st.title}>アメリカ大学スポーツ検索</Text>
      <TextInput style={st.input} placeholder="学校名・州・スポーツ・区分で検索 (例: 野球, CA, NCAA D2, NWAC)" placeholderTextColor="#888" value={query} onChangeText={setQuery} />
      <View style={st.row}>
        {DIVISIONS.map((item) => (
          <Chip key={item.key} label={item.label} on={item.key === 'ALL' ? divisions.length === 0 : divisions.includes(item.key as Division)}
            onPress={() => { if (item.key === 'ALL') setDivisions([]); else toggleIn<Division>(setDivisions, item.key as Division); setConfSel([]); }} />))}
      </View>
      <View style={st.row}>
        <Chip label="4年制" on={level === '4year'} onPress={() => setLevel(level === '4year' ? 'ALL' : '4year')} />
        <Chip label="短大" on={level === '2year'} onPress={() => setLevel(level === '2year' ? 'ALL' : '2year')} />
        <Chip label="アスリート奨学金あり" on={scholarshipOnly} onPress={() => setScholarshipOnly(!scholarshipOnly)} />
      </View>
      <View style={st.row}>
        <Chip label="★お気に入り" on={favOnly} onPress={() => setFavOnly(!favOnly)} />
        {[15000, 25000, 40000].map((c) => (
          <Chip key={c} label={`州外学費 $${c / 1000}K以下`} on={maxCost === c} onPress={() => setMaxCost(maxCost === c ? null : c)} />))}
      </View>
      <View style={st.row}>
        <Text style={[st.sub, { alignSelf: 'center', marginRight: 6 }]}>並び替え:</Text>
        <Chip label="名前順" on={sortKey === 'name'} onPress={() => setSortKey('name')} />
        <Chip label="学費が安い順" on={sortKey === 'cost'} onPress={() => setSortKey('cost')} />
        <Chip label="アスリート奨学金%が高い順" on={sortKey === 'pct'} onPress={() => setSortKey('pct')} />
      </View>
      <View style={st.row}>
        <Chip label={stateSel.length ? `州: ${stateSel.map((x) => stateJa[x] ?? x).join('・')}` : '州で絞る ▾'} on={stateSel.length > 0} onPress={() => setPicker('state')} />
        <Chip label={confSel.length ? `リーグ: ${confSel.length}件` : 'リーグ(カンファレンス)で絞る ▾'} on={confSel.length > 0} onPress={() => setPicker('conf')} />
        <Chip label={sportSel.length ? `競技: ${sportSel.map((n) => sportList.find((x) => x.name === n)?.ja ?? n).join('・')}` : '競技で絞る(チア含む) ▾'} on={sportSel.length > 0} onPress={() => setPicker('sport')} />
      </View>
      <Modal visible={picker !== null} animationType="slide" onRequestClose={() => setPicker(null)}>
        <View style={st.root}>
          <Text style={st.title}>{picker === 'state' ? '州を選ぶ(複数可)' : picker === 'sport' ? '競技を選ぶ(複数可・すべてに当てはまる学校)' : 'リーグを選ぶ(複数可)'}</Text>
          {picker === 'conf' && <Text style={st.sub}>※ リーグ名はNCAA加盟校のみ。{divisions.length === 0 ? '' : `${divisions.join('・')}のリーグを表示中。`}</Text>}
          <FlatList
            data={picker === 'state' ? states : picker === 'sport' ? sportList.map((x) => x.name) : conferences}
            keyExtractor={(x) => x}
            renderItem={({ item }) => {
              const sel = picker === 'state' ? stateSel : picker === 'sport' ? sportSel : confSel;
              const on = sel.includes(item);
              return (
                <Pressable style={st.pickRow} onPress={() => toggleIn<string>(picker === 'state' ? setStateSel : picker === 'sport' ? setSportSel : setConfSel, item)}>
                  <Text style={[st.name, on && { color: '#0a5' }]}>{on ? '✓ ' : ''}{picker === 'state' ? `${stateJa[item] ?? item} (${item})` : picker === 'sport' ? `${sportList.find((x) => x.name === item)?.ja ?? item} (${item})` : item}</Text>
                </Pressable>);
            }} />
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', paddingTop: 8 }}>
            <Pressable onPress={() => (picker === 'state' ? setStateSel([]) : picker === 'sport' ? setSportSel([]) : setConfSel([]))}><Text style={st.link}>選択をクリア</Text></Pressable>
            <Pressable onPress={() => setPicker(null)}><Text style={st.link}>完了</Text></Pressable>
          </View>
        </View>
      </Modal>
      {cmp.length > 0 && <Pressable onPress={() => setShowCmp(true)} style={st.cmpBar}><Text style={st.chipTextOn}>比較する({cmp.length}校) →</Text></Pressable>}
      {(() => {
        const pts = results.filter((x) => x.lat != null && x.lng != null).slice(0, 10);
        return pts.length >= 2 ? (
          <Pressable onPress={() => Linking.openURL(`https://www.google.com/maps/dir/${pts.map((x) => `${x.lat},${x.lng}`).join('/')}`)}>
            <Text style={st.link}>🗺️ 上位{pts.length}校を地図で見る(Googleマップ)</Text>
          </Pressable>) : null;
      })()}
      <Text style={st.count}>{results.length} 校 ・ データ更新: {updatedAt ? updatedAt.slice(0, 10) : '同梱版'}{source === 'remote' ? '(最新)' : ''}</Text>
      <FlatList data={results} keyExtractor={(x) => x.id} renderItem={({ item }) => (
        <Pressable style={st.card} onPress={() => setSelected(item)}>
          <Text style={st.name}>{favs.includes(item.id) ? '★ ' : ''}{item.nameJa ?? item.name}</Text>
          <Text style={st.sub}>{item.name}</Text>
          <Text style={st.meta}>{item.city}, {item.state} ・ {item.level === '4year' ? '4年制' : '短大'} ・ {item.division.startsWith(item.association) ? item.division : `${item.association} ${item.division}`}</Text>
          <Text style={st.meta}>州外学費 {item.tuitionOutOfState != null ? `$${item.tuitionOutOfState.toLocaleString()}` : '—'}/年 ・ アスリート奨学金 {item.athleticScholarshipPct == null ? '—' : `最大${item.athleticScholarshipPct}%`}</Text>
          <Pressable onPress={() => toggleCmp(item.id)}><Text style={st.link}>{cmp.includes(item.id) ? '✓ 比較に追加済み(タップで外す)' : cmp.length >= 3 ? '比較は3校まで' : '＋ 比較に追加'}</Text></Pressable>
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

function Detail({ school: sc, onBack, fav, onFav, showCheer }: { school: School; onBack: () => void; fav: boolean; onFav: () => void; showCheer: boolean }) {
  const money = (n: number | null) => (n == null ? '—' : `$${n.toLocaleString()}`);
  return (
    <ScrollView style={st.root} contentContainerStyle={{ paddingBottom: 48 }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
        <Pressable onPress={onBack}><Text style={st.link}>← 戻る</Text></Pressable>
        <Pressable onPress={onFav}><Text style={st.link}>{fav ? '★ お気に入り済み' : '☆ お気に入りに追加'}</Text></Pressable>
      </View>
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
          <Text style={st.name}>アスリート奨学金の最大割合</Text>
          <Text style={st.meta}>{sc.athleticScholarshipPct == null ? '—' : sc.athleticScholarshipPct === 0 ? '0%(運動奨学金なし)' : `最大 ${sc.athleticScholarshipPct}%まで(総費用に対して)`}</Text>
          {sc.division === 'NWAC' && <Text style={st.linkDesc}>{sc.athleticScholarshipMax}</Text>}
          {sc.athleticScholarshipPct != null && sc.athleticScholarshipPct > 0 && (
            <Text style={st.linkDesc}>{sc.division === 'NJCAA-D2' ? '授業料・教材のみが対象のため、総費用に対する目安の割合です。' : sc.athleticScholarshipPct === 100 ? '全額まで可能ですが、実際はチームの上限内で選手ごとに異なり、部分奨学金が多いです。' : ''}</Text>)}
        </View>)}
      {showCheer && (
      <View style={st.summary}>
        <Text style={st.name}>チア・ダンス・スタント</Text>
        <Text style={st.meta}>{sc.cheerNote ?? 'チーム情報なし(未確認)'}</Text>
        {!!sc.cheerNote && <Text style={st.linkDesc}>{CHEER_AID_NOTE}</Text>}
      </View>)}
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
      {sc.lat != null && sc.lng != null && <LinkRow icon="🗺️" label="地図で見る(Googleマップ)" desc={`${sc.city}, ${sc.state} の場所を開きます`} url={`https://www.google.com/maps/search/?api=1&query=${sc.lat},${sc.lng}`} />}
      <LinkRow icon="🏫" label="学校の公式サイト" desc="学部・学費・キャンパスなど学校全体の情報" url={sc.website} />
      <LinkRow icon="🏅" label="運動部(アスレチックス)サイト" desc={sc.athleticsUrl ? 'チームのスケジュール・コーチ・選手募集の連絡先' : '運動部の公式サイトをGoogleで探します'} url={sc.athleticsUrl ?? google(`${sc.name} athletics official site`)} />
      <LinkRow icon="💰" label={sc.scholarshipUrl ? 'スカラーシップ(奨学金)ページ' : 'スカラーシップ(奨学金)を探す'} desc={sc.scholarshipUrl ? '運動奨学金・留学生向け奨学金の案内ページ' : 'この学校のサイト内から、運動奨学金・留学生向け奨学金のページを検索します'} url={sc.scholarshipUrl ?? google(`site:${host(sc.website)} athletic scholarship international student`)} />
      <LinkRow icon="✈️" label="留学生の出願ページを探す" desc="出願方法・必要書類・英語スコアなど留学生向けの案内を検索します" url={google(`site:${host(sc.website)} international admissions`)} />
      {!sc.verified && <Text style={st.warn}>※ データ出典: 米国教育省 EADA 2024-25 / College Scorecard。奨学金・競技は年度で変わるため、出願前に必ず公式サイトで確認してください。</Text>}
    </ScrollView>
  );
}

function Compare({ list, onBack, onRemove, showCheer }: { list: School[]; onBack: () => void; onRemove: (id: string) => void; showCheer: boolean }) {
  const money = (n: number | null | undefined) => (n == null ? '—' : `$${n.toLocaleString()}`);
  const rows: { label: string; val: (x: School) => string }[] = [
    { label: '所在地', val: (x) => `${x.city}, ${x.state}` },
    { label: '種別', val: (x) => `${x.level === '4year' ? '4年制' : '短大'} / ${x.control === 'public' ? '公立' : '私立'}` },
    { label: '所属', val: (x) => `${x.division}${x.conference ? ` / ${x.conference}` : ''}` },
    { label: '学費(州内)', val: (x) => money(x.tuitionInState) },
    { label: '学費(州外・留学生)', val: (x) => money(x.tuitionOutOfState) },
    { label: '平均ネットプライス', val: (x) => money(x.avgNetPrice) },
    { label: 'アスリート奨学金(最大)', val: (x) => (x.athleticScholarshipPct == null ? '—' : x.athleticScholarshipPct === 0 ? '0%(なし)' : `最大${x.athleticScholarshipPct}%`) },
    ...(showCheer ? [{ label: 'チア', val: (x: School) => (x.sports.some((sp: { name: string }) => sp.name === 'Cheerleading') ? 'あり' : '情報なし') }] : []),
    { label: '競技数', val: (x) => `${x.sports.length}種目` },
  ];
  return (
    <ScrollView style={st.root} contentContainerStyle={{ paddingBottom: 48 }}>
      <Pressable onPress={onBack}><Text style={st.link}>← 戻る</Text></Pressable>
      <Text style={st.title}>学校を比較</Text>
      <ScrollView horizontal>
        <View>
          <View style={st.cmpRow}>
            <Text style={[st.cmpLabel, st.name]}> </Text>
            {list.map((x) => (
              <View key={x.id} style={st.cmpCell}>
                <Text style={st.name}>{x.nameJa ?? x.name}</Text>
                <Pressable onPress={() => onRemove(x.id)}><Text style={st.linkDesc}>外す</Text></Pressable>
              </View>))}
          </View>
          {rows.map((r) => (
            <View key={r.label} style={st.cmpRow}>
              <Text style={[st.cmpLabel, st.meta]}>{r.label}</Text>
              {list.map((x) => <Text key={x.id} style={[st.cmpCell, st.meta]}>{r.val(x)}</Text>)}
            </View>))}
        </View>
      </ScrollView>
      <Text style={st.warn}>※ 金額は目安です。最新は各校の公式ページで確認してください。</Text>
    </ScrollView>
  );
}

const st = StyleSheet.create({
  cmpBar: { backgroundColor: '#0a5', borderRadius: 8, padding: 10, alignItems: 'center', marginBottom: 6 },
  cmpRow: { flexDirection: 'row', borderBottomWidth: 1, borderBottomColor: '#eee', paddingVertical: 8 },
  cmpLabel: { width: 110 }, cmpCell: { width: 150, paddingRight: 8 },
  root: { flex: 1, padding: 16, paddingTop: 48, backgroundColor: '#fff' },
  title: { fontSize: 22, fontWeight: '700', marginBottom: 8 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 10, marginBottom: 8, color: '#111', backgroundColor: '#fff' },
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
