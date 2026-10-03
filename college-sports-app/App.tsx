import { useMemo, useState } from 'react';
import { FlatList, Linking, Pressable, SafeAreaView, StyleSheet, Text, TextInput, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { schools } from './src/data/schools';
import { Division, School } from './src/types';

const DIVISIONS: { key: Division | 'ALL'; label: string }[] = [
  { key: 'ALL', label: 'すべて' }, { key: 'D1', label: 'NCAA D1' }, { key: 'D2', label: 'NCAA D2' },
  { key: 'D3', label: 'NCAA D3' }, { key: 'NAIA', label: 'NAIA' }, { key: 'NJCAA-D1', label: 'NJCAA D1' },
  { key: 'NJCAA-D2', label: 'NJCAA D2' }, { key: 'CCCAA', label: 'CCCAA' },
];

export default function App() {
  const [query, setQuery] = useState('');
  const [division, setDivision] = useState<Division | 'ALL'>('ALL');
  const [level, setLevel] = useState<'ALL' | '4year' | '2year'>('ALL');
  const [scholarshipOnly, setScholarshipOnly] = useState(false);
  const [selected, setSelected] = useState<School | null>(null);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    return schools.filter((sc) =>
      (division === 'ALL' || sc.division === division) &&
      (level === 'ALL' || sc.level === level) &&
      (!scholarshipOnly || sc.athleticScholarship) &&
      (!q || [sc.name, sc.nameJa ?? '', sc.state, sc.city, ...sc.sports.flatMap((x) => [x.name, x.nameJa])]
        .some((t) => t.toLowerCase().includes(q))));
  }, [query, division, level, scholarshipOnly]);

  if (selected) return <Detail school={selected} onBack={() => setSelected(null)} />;

  return (
    <SafeAreaView style={st.root}>
      <StatusBar style="auto" />
      <Text style={st.title}>アメリカ大学スポーツ検索</Text>
      <TextInput style={st.input} placeholder="学校名・州・スポーツで検索 (例: 野球, CA)" value={query} onChangeText={setQuery} />
      <FlatList horizontal showsHorizontalScrollIndicator={false} data={DIVISIONS} keyExtractor={(d) => d.key}
        style={st.chips} renderItem={({ item }) => (
          <Chip label={item.label} on={division === item.key} onPress={() => setDivision(item.key)} />)} />
      <View style={st.row}>
        <Chip label="4年制" on={level === '4year'} onPress={() => setLevel(level === '4year' ? 'ALL' : '4year')} />
        <Chip label="短大" on={level === '2year'} onPress={() => setLevel(level === '2year' ? 'ALL' : '2year')} />
        <Chip label="アスリート奨学金あり" on={scholarshipOnly} onPress={() => setScholarshipOnly(!scholarshipOnly)} />
      </View>
      <Text style={st.count}>{results.length} 校</Text>
      <FlatList data={results} keyExtractor={(x) => x.id} renderItem={({ item }) => (
        <Pressable style={st.card} onPress={() => setSelected(item)}>
          <Text style={st.name}>{item.nameJa ?? item.name}</Text>
          <Text style={st.sub}>{item.name}</Text>
          <Text style={st.meta}>{item.city}, {item.state} ・ {item.level === '4year' ? '4年制' : '短大'} ・ {item.association} {item.division}</Text>
          <Text style={st.meta}>{item.sports.length ? item.sports.map((x) => x.nameJa).join('・') : '競技情報: 準備中'}</Text>
        </Pressable>)} />
    </SafeAreaView>
  );
}

function Chip({ label, on, onPress }: { label: string; on: boolean; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={[st.chip, on && st.chipOn]}>
      <Text style={on ? st.chipTextOn : st.chipText}>{label}</Text>
    </Pressable>
  );
}

function Detail({ school: sc, onBack }: { school: School; onBack: () => void }) {
  const money = (n: number | null) => (n == null ? '未確認' : `$${n.toLocaleString()}`);
  return (
    <SafeAreaView style={st.root}>
      <Pressable onPress={onBack}><Text style={st.link}>← 戻る</Text></Pressable>
      <Text style={st.title}>{sc.nameJa ?? sc.name}</Text>
      <Text style={st.sub}>{sc.name}</Text>
      <Text style={st.meta}>所在地: {sc.city}, {sc.state}</Text>
      <Text style={st.meta}>種別: {sc.level === '4year' ? '4年制' : '短大'} / {sc.control === 'public' ? '公立' : '私立'}</Text>
      <Text style={st.meta}>所属: {sc.association} / {sc.division}{sc.conference ? ` / ${sc.conference}` : ''}</Text>
      <Text style={st.meta}>学費(年): 州内 {money(sc.tuitionInState)} / 州外 {money(sc.tuitionOutOfState)}</Text>
      <Text style={st.meta}>アスリート奨学金: {sc.athleticScholarship ? 'あり' : 'なし'}</Text>
      {sc.scholarshipNote && <Text style={st.meta}>{sc.scholarshipNote}</Text>}
      <Text style={[st.name, { marginTop: 12 }]}>スポーツ</Text>
      {sc.sports.map((x) => (
        <Text key={x.name} style={st.meta}>・{x.nameJa} ({x.name}) {x.gender === 'M' ? '男子' : x.gender === 'W' ? '女子' : '男女'}</Text>))}
      <Pressable onPress={() => Linking.openURL(sc.website)}><Text style={[st.link, { marginTop: 12 }]}>公式サイト</Text></Pressable>
      {!sc.verified && <Text style={st.warn}>※ 未検証データ。出願前に必ず公式サイトで確認してください。</Text>}
    </SafeAreaView>
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
  meta: { color: '#333', marginTop: 2 }, link: { color: '#06c', fontSize: 16 }, warn: { color: '#c60', marginTop: 16 },
});
