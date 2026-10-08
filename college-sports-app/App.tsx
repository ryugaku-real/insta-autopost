import { useEffect, useMemo, useState } from 'react';
import { FlatList, Linking, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { StatusBar } from 'expo-status-bar';
import { useSchools } from './src/data/useSchools';
import { Division, School } from './src/types';
import { aidRules } from './src/data/aidRules';
import { stateJa } from './src/data/states';
import { detectLang, getLang, Lang, setLang, stateEn, tr } from './src/i18n';
import { engText } from './src/engText';
import { dt, engData, noteEn, sectionTitleEn } from './src/engData';
import { CHEER_AID_NOTE, limitHeader, sportLimits } from './src/data/athleticLimits';

const DIVISIONS: { key: Division | 'ALL'; label: string }[] = [
  { key: 'ALL', label: 'ALL' }, { key: 'D1', label: 'NCAA D1' }, { key: 'D2', label: 'NCAA D2' },
  { key: 'D3', label: 'NCAA D3' }, { key: 'NAIA', label: 'NAIA' }, { key: 'NJCAA-D1', label: 'NJCAA D1' },
  { key: 'NJCAA-D2', label: 'NJCAA D2' }, { key: 'NJCAA-D3', label: 'NJCAA D3' },
  { key: 'CCCAA', label: 'CCCAA(CA)' }, { key: 'NWAC', label: 'NWAC' },
];

const FREE_FAVS = 3;
const FREE_CMP = 2;
const PAID_CMP = 4;

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
  const [premium, setPremium] = useState(false);
  const [lang, setLangState] = useState<Lang>(detectLang());
  setLang(lang);
  useEffect(() => { AsyncStorage.getItem('lang').then((v) => { if (v === 'ja' || v === 'en') setLangState(v); }).catch(() => {}); }, []);
  const switchLang = () => { const n: Lang = lang === 'ja' ? 'en' : 'ja'; setLang(n); setLangState(n); AsyncStorage.setItem('lang', n).catch(() => {}); };
  const stName = (c: string) => (lang === 'en' ? stateEn[c] : stateJa[c]) ?? c;
  const spName = (name: string, ja?: string) => (lang === 'en' ? name : ja ?? name);
  const [showPlan, setShowPlan] = useState(false);
  const [lockHint, setLockHint] = useState<string | null>(null);
  const [cmp, setCmp] = useState<string[]>([]);
  const [showCmp, setShowCmp] = useState(false);
  const toggleIn = <T,>(set: (f: (c: T[]) => T[]) => void, v: T) => set((c) => (c.includes(v) ? c.filter((x) => x !== v) : [...c, v]));
  // cheer details are shown only while a cheer-type sport is selected in the sport filter
  const cheerSelected = sportSel.some((n) => ['Cheerleading', 'Dance', 'STUNT', 'Acrobatics & Tumbling'].includes(n));
  const cmpLimit = premium ? PAID_CMP : FREE_CMP;
  const toggleCmp = (id: string) => {
    if (!cmp.includes(id) && cmp.length >= cmpLimit) { setLockHint(premium ? tr(`比較は${PAID_CMP}校までです。`, `You can compare up to ${PAID_CMP} schools.`) : tr(`比較は${FREE_CMP}校まで。${FREE_CMP + 1}校以上は有料プランです。`, `Free plan: compare up to ${FREE_CMP} schools. ${FREE_CMP + 1}+ needs the paid plan.`)); return; }
    setCmp((c) => (c.includes(id) ? c.filter((x) => x !== id) : [...c, id]));
  };
  // free plan: one value per filter (state / league / sport); premium: several at once
  const pickToggle = (list: string[], setter: (v: string[]) => void, item: string) => {
    if (list.includes(item)) { setter(list.filter((x) => x !== item)); return; }
    if (premium || list.length === 0) { setter([...list, item]); return; }
    setter([item]);
    setLockHint(tr('無料プランでは各項目1つまで。2つ以上を同時に選ぶには有料プランです。', 'Free plan: one value per filter. Selecting several at once needs the paid plan.'));
  };
  useEffect(() => { AsyncStorage.getItem('premium').then((v) => { if (v === '1') setPremium(true); }).catch(() => {}); }, []);
  const setPremiumSaved = (v: boolean) => { setPremium(v); AsyncStorage.setItem('premium', v ? '1' : '0').catch(() => {}); };
  useEffect(() => { AsyncStorage.getItem('favs').then((v) => { if (v) setFavs(JSON.parse(v)); }).catch(() => {}); }, []);
  const toggleFav = (id: string) => {
    if (!favs.includes(id) && !premium && favs.length >= FREE_FAVS) { setLockHint(tr(`お気に入りは無料プランでは${FREE_FAVS}校まで。無制限は有料プランです。`, `Free plan: up to ${FREE_FAVS} favorites. Unlimited needs the paid plan.`)); return; }
    toggleFavRaw(id);
  };
  const toggleFavRaw = (id: string) => setFavs((cur) => {
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

  if (showPlan) return <PlanScreen premium={premium} onSet={setPremiumSaved} onBack={() => setShowPlan(false)} />;
  if (showCmp) return <Compare showCheer={cheerSelected} list={schools.filter((x) => cmp.includes(x.id))} onBack={() => setShowCmp(false)} onRemove={toggleCmp} />;
  if (selected) return <Detail school={selected} premium={premium} onPlan={() => setShowPlan(true)} showCheer={cheerSelected} onBack={() => setSelected(null)} fav={favs.includes(selected.id)} onFav={() => toggleFav(selected.id)} />;

  return (
    <View style={st.root}>
      <StatusBar style="auto" />
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text style={st.title}>{tr('アメリカ大学検索', 'US College Search')}</Text>
        <View style={{ flexDirection: 'row' }}><Pressable onPress={switchLang}><Text style={[st.link, { marginRight: 14 }]}>{lang === 'ja' ? 'English' : '日本語'}</Text></Pressable><Pressable onPress={() => setShowPlan(true)}><Text style={st.link}>{premium ? tr('👑 有料プラン', '👑 Paid plan') : tr('無料プラン ▸', 'Free plan ▸')}</Text></Pressable></View>
      </View>
      {lockHint && (
        <Pressable onPress={() => { setLockHint(null); setShowPlan(true); }} style={st.lockBar}>
          <Text style={st.lockText}>🔒 {lockHint}{tr('(タップでプランを見る)', ' (tap to see plans)')}</Text>
        </Pressable>)}
      <TextInput style={st.input} placeholder={tr('学校名・州・スポーツ・区分で検索 (例: 野球, CA, NCAA D1, NWAC)', 'Search school, state, sport, division (e.g. baseball, CA, NCAA D1, NWAC)')} placeholderTextColor="#888" value={query} onChangeText={setQuery} />
      <View style={st.row}>
        {DIVISIONS.map((item) => (
          <Chip key={item.key} label={item.key === 'ALL' ? tr('すべて', 'All') : item.label} on={item.key === 'ALL' ? divisions.length === 0 : divisions.includes(item.key as Division)}
            onPress={() => { if (item.key === 'ALL') setDivisions([]); else toggleIn<Division>(setDivisions, item.key as Division); setConfSel([]); }} />))}
      </View>
      <View style={st.row}>
        <Chip label={tr('4年制', '4-year')} on={level === '4year'} onPress={() => setLevel(level === '4year' ? 'ALL' : '4year')} />
        <Chip label={tr('短大', 'Junior college')} on={level === '2year'} onPress={() => setLevel(level === '2year' ? 'ALL' : '2year')} />
        <Chip label={tr('アスリート奨学金あり', 'Athletic scholarships')} on={scholarshipOnly} onPress={() => setScholarshipOnly(!scholarshipOnly)} />
      </View>
      <View style={st.row}>
        <Chip label={tr('★お気に入り', '★ Favorites')} on={favOnly} onPress={() => setFavOnly(!favOnly)} />
        {[15000, 25000, 40000].map((c) => (
          <Chip key={c} label={tr(`州外学費 $${c / 1000}K以下`, `Out-of-state ≤ $${c / 1000}K`)} on={maxCost === c} onPress={() => setMaxCost(maxCost === c ? null : c)} />))}
      </View>
      <View style={st.row}>
        <Text style={[st.sub, { alignSelf: 'center', marginRight: 6 }]}>{tr('並び替え:', 'Sort:')}</Text>
        <Chip label={tr('名前順', 'Name')} on={sortKey === 'name'} onPress={() => setSortKey('name')} />
        <Chip label={tr('学費が安い順', 'Lowest cost')} on={sortKey === 'cost'} onPress={() => setSortKey('cost')} />
        <Chip label={tr('アスリート奨学金%が高い順', 'Highest athletic aid %')} on={sortKey === 'pct'} onPress={() => setSortKey('pct')} />
      </View>
      <View style={st.row}>
        <Chip label={stateSel.length ? `${tr('州', 'State')}: ${stateSel.map(stName).join(tr('・', ', '))}` : tr('州で絞る ▾', 'Filter by state ▾')} on={stateSel.length > 0} onPress={() => setPicker('state')} />
        <Chip label={confSel.length ? tr(`リーグ: ${confSel.length}件`, `Conference: ${confSel.length}`) : tr('リーグ(カンファレンス)で絞る ▾', 'Filter by conference ▾')} on={confSel.length > 0} onPress={() => setPicker('conf')} />
        <Chip label={sportSel.length ? `${tr('競技', 'Sport')}: ${sportSel.map((n) => spName(n, sportList.find((x) => x.name === n)?.ja)).join(tr('・', ', '))}` : tr('競技で絞る(チア含む) ▾', 'Filter by sport (incl. cheer) ▾')} on={sportSel.length > 0} onPress={() => setPicker('sport')} />
      </View>
      <Modal visible={picker !== null} animationType="slide" onRequestClose={() => setPicker(null)}>
        <View style={st.root}>
          <Text style={st.title}>{(picker === 'state' ? tr('州を選ぶ', 'Choose a state') : picker === 'sport' ? tr('競技を選ぶ', 'Choose a sport') : tr('リーグを選ぶ', 'Choose a conference')) + (premium ? tr('(複数可)', ' (multiple OK)') : tr('(無料プランは1つ)', ' (free plan: one)'))}</Text>
          {picker === 'conf' && <Text style={st.sub}>{tr('※ リーグ名はNCAA加盟校のみ。', '* Conferences are listed for NCAA schools only. ')}{divisions.length === 0 ? '' : tr(`${divisions.join('・')}のリーグを表示中。`, `Showing ${divisions.join(', ')} conferences.`)}</Text>}
          <FlatList
            data={picker === 'state' ? states : picker === 'sport' ? sportList.map((x) => x.name) : conferences}
            keyExtractor={(x) => x}
            renderItem={({ item }) => {
              const sel = picker === 'state' ? stateSel : picker === 'sport' ? sportSel : confSel;
              const on = sel.includes(item);
              return (
                <Pressable style={st.pickRow} onPress={() => (picker === 'state' ? pickToggle(stateSel, setStateSel, item) : picker === 'sport' ? pickToggle(sportSel, setSportSel, item) : pickToggle(confSel, setConfSel, item))}>
                  <Text style={[st.name, on && { color: '#0a5' }]}>{on ? '✓ ' : ''}{picker === 'state' ? `${stName(item)} (${item})` : picker === 'sport' && lang === 'ja' ? `${sportList.find((x) => x.name === item)?.ja ?? item} (${item})` : item}</Text>
                </Pressable>);
            }} />
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', paddingTop: 8 }}>
            <Pressable onPress={() => (picker === 'state' ? setStateSel([]) : picker === 'sport' ? setSportSel([]) : setConfSel([]))}><Text style={st.link}>{tr('選択をクリア', 'Clear')}</Text></Pressable>
            <Pressable onPress={() => setPicker(null)}><Text style={st.link}>{tr('完了', 'Done')}</Text></Pressable>
          </View>
        </View>
      </Modal>
      {cmp.length > 0 && <Pressable onPress={() => setShowCmp(true)} style={st.cmpBar}><Text style={st.chipTextOn}>{tr(`比較する(${cmp.length}校) →`, `Compare (${cmp.length}) →`)}</Text></Pressable>}
      {(() => {
        const pts = results.filter((x) => x.lat != null && x.lng != null).slice(0, 10);
        return pts.length >= 2 ? (
          <Pressable onPress={() => Linking.openURL(`https://www.google.com/maps/dir/${pts.map((x) => `${x.lat},${x.lng}`).join('/')}`)}>
            <Text style={st.link}>🗺️ {tr(`上位${pts.length}校を地図で見る(Googleマップ)`, `Map the top ${pts.length} results (Google Maps)`)}</Text>
          </Pressable>) : null;
      })()}
      <Text style={st.count}>{results.length} {tr('校', 'schools')} ・ {tr('データ更新', 'Data updated')}: {updatedAt ? updatedAt.slice(0, 10) : tr('同梱版', 'bundled')}{source === 'remote' ? tr('(最新)', ' (latest)') : ''}</Text>
      <FlatList data={results} keyExtractor={(x) => x.id} renderItem={({ item }) => (
        <Pressable style={st.card} onPress={() => setSelected(item)}>
          <Text style={st.name}>{favs.includes(item.id) ? '★ ' : ''}{lang === 'en' ? item.name : item.nameJa ?? item.name}</Text>
          {lang === 'ja' && <Text style={st.sub}>{item.name}</Text>}
          <Text style={st.meta}>{item.city}, {item.state} ・ {item.level === '4year' ? tr('4年制', '4-year') : tr('短大', 'Junior college')} ・ {item.division.startsWith(item.association) ? item.division : `${item.association} ${item.division}`}</Text>
          <Text style={st.meta}>{tr('州外学費', 'Out-of-state')} {item.tuitionOutOfState != null ? `$${item.tuitionOutOfState.toLocaleString()}` : '—'}{tr('/年', '/yr')} ・ {tr('アスリート奨学金', 'Athletic aid')} {item.athleticScholarshipPct == null ? '—' : tr(`最大${item.athleticScholarshipPct}%`, `up to ${item.athleticScholarshipPct}%`)}</Text>
          <Pressable onPress={() => toggleCmp(item.id)}><Text style={st.link}>{cmp.includes(item.id) ? tr('✓ 比較に追加済み(タップで外す)', '✓ Added to compare (tap to remove)') : cmp.length >= cmpLimit ? tr(`比較は${cmpLimit}校まで`, `Compare limit: ${cmpLimit}`) : tr('＋ 比較に追加', '+ Add to compare')}</Text></Pressable>
          <Text style={st.meta}>{item.sports.length ? item.sports.map((x) => spName(x.name, x.nameJa)).join(tr('・', ', ')) : tr('競技情報: 準備中', 'Sports: coming soon')}</Text>
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

const LEVEL_EXPLAIN: Record<string, [string, string]> = {
  D1: ['NCAAで最も競技レベルが高いクラス', 'the highest competition level in the NCAA'],
  D2: ['NCAAの中間クラスで、奨学金が分割で出やすい', 'the middle NCAA tier; scholarships are usually split into partial awards'],
  D3: ['NCAAの学業重視クラス(運動奨学金は出ません)', 'the academics-first NCAA tier (no athletic scholarships)'],
  NAIA: ['NCAAとは別の大学リーグで、小規模校が中心', 'a separate college league, mostly smaller schools'],
  'NJCAA-D1': ['短大リーグの最上位でフル奨学金も可能。4年制への編入ルートにもなる', 'the top junior-college league; full scholarships possible and a transfer path to 4-year schools'],
  'NJCAA-D2': ['短大リーグの中位(授業料までの奨学金)', 'mid-tier junior-college league (aid up to tuition)'],
  'NJCAA-D3': ['短大リーグ(運動奨学金なし)', 'junior-college league (no athletic scholarships)'],
  CCCAA: ['カリフォルニア州の公立短大リーグ(運動奨学金なし)', 'California public community-college league (no athletic scholarships)'],
  NWAC: ['北西部(ワシントン・オレゴン等)の短大リーグ', 'Northwest (WA, OR, etc.) community-college league'],
};

function summarize(sc: School) {
  const en = tr('', 'x') === 'x';
  const sp = (x: { name: string; nameJa: string }) => (en ? x.name : x.nameJa);
  const sports = sc.sports.slice(0, 5).map(sp).join(tr('・', ', '));
  const div = sc.division.startsWith(sc.association) ? sc.division : `${sc.association} ${sc.division}`;
  const k = Math.round((sc.athleticAid?.total ?? 0) / 1000).toLocaleString();
  const hasAid = !!sc.athleticAid && sc.athleticAid.total > 0;
  const expl = tr(LEVEL_EXPLAIN[sc.division][0], LEVEL_EXPLAIN[sc.division][1]);
  if (en) {
    return `A ${sc.control === 'public' ? 'public' : 'private'} ${sc.level === '4year' ? '4-year college' : 'junior college'} in ${stateEn[sc.state] ?? sc.state}. ` +
      `Member of ${div} (${expl}). ` +
      `${sports ? `Sports include ${sports}${sc.sports.length > 5 ? ' and more' : ''} (${sc.sports.length} total). ` : ''}` +
      `Athletic scholarships: ${sc.athleticScholarship ? 'yes' : 'no'}. ${hasAid ? `About $${k}K per year in aid to athletes.` : ''}`;
  }
  return `${sc.state}州の${sc.control === 'public' ? '公立' : '私立'}${sc.level === '4year' ? '4年制大学' : '短大'}。` +
    `${div}所属(${expl})。` +
    `${sports ? `競技は${sports}など${sc.sports.length}種目。` : ''}` +
    `運動奨学金は${sc.athleticScholarship ? 'あり' : 'なし'}。${hasAid ? `運動部への奨学金は年間およそ$${k}K。` : ''}`;
}

function Chip({ label, on, onPress }: { label: string; on: boolean; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={[st.chip, on && st.chipOn]}>
      <Text style={on ? st.chipTextOn : st.chipText}>{label}</Text>
    </Pressable>
  );
}

function Detail({ school: sc, onBack, fav, onFav, showCheer, premium, onPlan }: { school: School; onBack: () => void; fav: boolean; onFav: () => void; showCheer: boolean; premium: boolean; onPlan: () => void }) {
  const money = (n: number | null) => (n == null ? '—' : `$${n.toLocaleString()}`);
  const miss = { n: 0 };
  if (getLang() === 'en') {
    if (sc.cheerNote) dt(sc.cheerNote, miss);
    [sc.verifyNote, ...(sc.tuitionLines ?? []), ...(sc.scholarshipSections ?? []).map((x) => x.text), sc.division === 'NWAC' ? sc.athleticScholarshipMax : undefined]
      .forEach((t) => { if (t && !(sc.intlAidNote && noteEn(sc.intlAidNote))) dt(t, miss); });
    if (sc.intlAidNote && !noteEn(sc.intlAidNote)) miss.n++;
  }
  const noteBox = getLang() === 'en' && sc.intlAidNote ? noteEn(sc.intlAidNote) : null;
  const showMiss = miss.n > 0;
  const body = (
    <ScrollView style={st.root} contentContainerStyle={{ paddingBottom: 48 }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
        <Pressable onPress={onBack}><Text style={st.link}>{tr('← 戻る', '← Back')}</Text></Pressable>
        <Pressable onPress={onFav}><Text style={st.link}>{fav ? tr('★ お気に入り済み', '★ Favorited') : tr('☆ お気に入りに追加', '☆ Add to favorites')}</Text></Pressable>
      </View>
      {showMiss && <Text style={st.warn}>Some research notes on this page are in Japanese only for now.</Text>}
      <Text style={st.title}>{getLang() === 'en' ? sc.name : sc.nameJa ?? sc.name}</Text>
      {getLang() === 'ja' && <Text style={st.sub}>{sc.name}</Text>}
      <View style={st.summary}>
        <Text style={st.name}>{tr('ひとことで言うと', 'At a glance')}</Text>
        <Text style={st.meta}>{summarize(sc)}</Text>
      </View>
            <Text style={st.meta}>{tr('所在地', 'Location')}: {sc.city}, {sc.state}</Text>
      <Text style={st.meta}>{tr('種別', 'Type')}: {sc.level === '4year' ? tr('4年制', '4-year') : tr('短大', 'Junior college')} / {sc.control === 'public' ? tr('公立', 'Public') : tr('私立', 'Private')}</Text>
      <Text style={st.meta}>{tr('所属', 'Affiliation')}: {sc.association} / {sc.division}{sc.conference ? ` / ${sc.conference}` : ''}</Text>
      <Text style={st.meta}>{tr('学費(年)', 'Tuition (yr)')}: {tr('州内', 'In-state')} {money(sc.tuitionInState)} / {tr('州外', 'Out-of-state')} {money(sc.tuitionOutOfState)}</Text>
      <Text style={st.meta}>{tr('アスリート奨学金', 'Athletic scholarships')}: {sc.athleticScholarship ? tr('あり', 'Yes') : tr('なし', 'No')}</Text>
      <View style={st.summary}>
        <Text style={st.name}>{tr('英語スコアの目安(留学生の出願)', 'English test scores (international applicants)')}</Text>
        {premium ? (
          <>
            <Text style={st.meta}>{sc.englishReq ? engText(sc.englishReq) : tr('この学校は未調査です(順次追加中)。', 'Not researched yet (being added gradually).')}</Text>
            {!!sc.englishReq && <Text style={st.linkDesc}>{tr('確認日', 'Checked')}: {sc.englishCheckedAt ?? tr('不明', 'unknown')} ・ {tr('年度や学部で変わるため、出願前に公式サイトで確認してください。', 'Requirements vary by year and program; confirm on the official site before applying.')}</Text>}
          </>
        ) : (
          <Pressable onPress={onPlan}>
            <Text style={st.meta}>{tr('🔒 有料プランで、公式サイトを開かなくてもTOEFL・IELTSなどの目安をここで見られます。', '🔒 With the paid plan, see TOEFL/IELTS guidance here without opening the school site.')}</Text>
            <Text style={st.link}>{tr('プランを見る ▸', 'See plans ▸')}</Text>
          </Pressable>)}
      </View>
      {(
        <View style={st.summary}>
          <Text style={st.name}>{tr('アスリート奨学金の最大割合', 'Max athletic scholarship share')}</Text>
          <Text style={st.meta}>{sc.athleticScholarshipPct == null ? '—' : sc.athleticScholarshipPct === 0 ? tr('0%(運動奨学金なし)', '0% (no athletic scholarships)') : tr(`最大 ${sc.athleticScholarshipPct}%まで(総費用に対して)`, `Up to ${sc.athleticScholarshipPct}% (of total cost)`)}</Text>
          {sc.division === 'NWAC' && !!sc.athleticScholarshipMax && <Text style={st.linkDesc}>{dt(sc.athleticScholarshipMax, miss)}</Text>}
          {sc.athleticScholarshipPct != null && sc.athleticScholarshipPct > 0 && (
            <Text style={st.linkDesc}>{sc.division === 'NJCAA-D2' ? tr('授業料・教材のみが対象のため、総費用に対する目安の割合です。', 'Covers tuition and materials only, so this is a rough share of total cost.') : sc.athleticScholarshipPct === 100 ? tr('全額まで可能ですが、実際はチームの上限内で選手ごとに異なり、部分奨学金が多いです。', 'Full rides are possible, but awards vary by athlete within team limits and partial awards are common.') : ''}</Text>)}
        </View>)}
      {showCheer && (
      <View style={st.summary}>
        <Text style={st.name}>{tr('チア・ダンス・スタント', 'Cheer / Dance / Stunt')}</Text>
        <Text style={st.meta}>{sc.cheerNote ? dt(sc.cheerNote, miss) : tr('チーム情報なし(未確認)', 'No team info (unconfirmed)')}</Text>
        {!!sc.cheerNote && getLang() === 'ja' && <Text style={st.linkDesc}>{CHEER_AID_NOTE}</Text>}
      </View>)}
      <Text style={st.meta}>{tr('平均ネットプライス(奨学金差引後・米国学生)', 'Average net price (after grants, US students)')}: {money(sc.avgNetPrice ?? null)}{tr('/年', '/yr')}</Text>
      {sc.tuitionLines && sc.tuitionLines.length > 0 && (
        <View style={st.summary}>
          <Text style={st.name}>{tr('学費・費用(留学生の目安)', 'Costs (guide for international students)')}</Text>
          {sc.tuitionLines.map((t) => <Text key={t} style={st.meta}>・{dt(t, miss)}</Text>)}
          {!!sc.tuitionResearch && !noteBox && <Text style={[st.meta, { marginTop: 6 }]}>{dt(sc.tuitionResearch, miss)}</Text>}
          <Text style={st.linkDesc}>{tr('数値は米国教育省(College Scorecard)ベースの概算と個別調査メモです。最新は学校の公式ページで確認してください。', 'Figures are estimates based on US Dept. of Education (College Scorecard) data plus per-school research notes. Confirm the latest on the official site.')}</Text>
        </View>)}
      {!!noteBox && (
        <View style={st.summary}>
          <Text style={st.name}>International-student research notes</Text>
          <Text style={st.meta}>{noteBox}</Text>
          <Text style={st.linkDesc}>Checked: {sc.intlAidCheckedAt ?? 'unknown'} ・ Always confirm the latest on the official site</Text>
        </View>)}
      {sc.scholarshipSections && sc.scholarshipSections.length > 0 ? (
        <View style={st.summary}>
          <Text style={st.name}>{tr('奨学金制度', 'Scholarships')}</Text>
          {sc.scholarshipSections.filter((x) => !noteBox || engData(x.text) != null).map((x) => (
            <View key={x.title} style={{ marginTop: 6 }}>
              <Text style={st.meta}>■ {getLang() === 'en' ? sectionTitleEn[x.title] ?? x.title : x.title}</Text>
              <Text style={st.meta}>{dt(x.text, miss)}</Text>
            </View>))}
          <Text style={st.linkDesc}>{tr('確認日', 'Checked')}: {sc.intlAidCheckedAt ?? tr('不明', 'unknown')} ・ {tr('最新は必ず学校の公式ページで確認してください', 'Always confirm the latest on the official site')}</Text>
          {!!sc.verifyNote && <Text style={st.linkDesc}>{tr('検証', 'Verification')}: {dt(sc.verifyNote, miss)}</Text>}
        </View>
      ) : sc.intlAidNote ? (
        <View style={st.summary}>
          <Text style={st.name}>{sc.intlAidAuto ? tr('留学生向け情報(個別調査前の目安)', 'International-student info (rough estimate, not yet individually researched)') : tr('留学生向け情報(調査メモ)', 'International-student info (research notes)')}</Text>
          <Text style={st.meta}>{dt(sc.intlAidNote, miss)}</Text>
          <Text style={st.linkDesc}>{sc.intlAidAuto ? tr('個別の調査は順次進めています', 'Individual research is ongoing') : `${tr('確認日', 'Checked')}: ${sc.intlAidCheckedAt ?? tr('不明', 'unknown')}`} ・ {tr('最新は必ず学校の公式ページで確認してください', 'Always confirm the latest on the official site')}</Text>
        </View>) : null}
      <Text style={[st.name, { marginTop: 12 }]}>{tr('奨学金ルール', 'Scholarship rules')} ({aidRules[sc.division].title})</Text>
      {aidRules[sc.division].points.map((t, i) => <Text key={t} style={st.meta}>・{getLang() === 'en' ? aidRules[sc.division].pointsEn[i] ?? t : t}</Text>)}
      <Text style={[st.name, { marginTop: 12 }]}>{tr('スポーツ', 'Sports')}</Text>
      {sc.sports.map((x) => (
        <Text key={x.name} style={st.meta}>・{getLang() === 'en' ? x.name : `${x.nameJa} (${x.name})`} {x.gender === 'M' ? tr('男子', "Men's") : x.gender === 'W' ? tr('女子', "Women's") : tr('男女', 'Co-ed')}</Text>))}
      <Text style={[st.name, { marginTop: 12 }]}>{tr('リンク(タップで開く)', 'Links (tap to open)')}</Text>
      {sc.lat != null && sc.lng != null && <LinkRow icon="🗺️" label={tr('地図で見る(Googleマップ)', 'View on map (Google Maps)')} desc={tr(`${sc.city}, ${sc.state} の場所を開きます`, `Open ${sc.city}, ${sc.state}`)} url={`https://www.google.com/maps/search/?api=1&query=${sc.lat},${sc.lng}`} />}
      <LinkRow icon="🏫" label={tr('学校の公式サイト', 'Official school website')} desc={tr('学部・学費・キャンパスなど学校全体の情報', 'Programs, tuition, campus and general info')} url={sc.website} />
      <LinkRow icon="🏅" label={tr('運動部(アスレチックス)サイト', 'Athletics website')} desc={sc.athleticsUrl ? tr('チームのスケジュール・コーチ・選手募集の連絡先', 'Schedules, coaches and recruiting contacts') : tr('運動部の公式サイトをGoogleで探します', 'Search Google for the athletics site')} url={sc.athleticsUrl ?? google(`${sc.name} athletics official site`)} />
      <LinkRow icon="💰" label={sc.scholarshipUrl ? tr('スカラーシップ(奨学金)ページ', 'Scholarship page') : tr('スカラーシップ(奨学金)を探す', 'Find scholarships')} desc={sc.scholarshipUrl ? tr('運動奨学金・留学生向け奨学金の案内ページ', 'Athletic and international scholarship info') : tr('この学校のサイト内から、運動奨学金・留学生向け奨学金のページを検索します', 'Search this school\'s site for athletic / international scholarships')} url={sc.scholarshipUrl ?? google(`site:${host(sc.website)} athletic scholarship international student`)} />
      <LinkRow icon="✈️" label={tr('留学生の出願ページを探す', 'Find international admissions page')} desc={tr('出願方法・必要書類・英語スコアなど留学生向けの案内を検索します', 'Search for how to apply, documents and English score requirements')} url={google(`site:${host(sc.website)} international admissions`)} />
      {!sc.verified && <Text style={st.warn}>{tr('※ データ出典: 米国教育省 EADA 2024-25 / College Scorecard。奨学金・競技は年度で変わるため、出願前に必ず公式サイトで確認してください。', '* Data sources: US Dept. of Education EADA 2024-25 / College Scorecard. Scholarships and sports change yearly; always confirm on the official site before applying.')}</Text>}
    </ScrollView>
  );
  return body;
}

function PlanScreen({ premium, onSet, onBack }: { premium: boolean; onSet: (v: boolean) => void; onBack: () => void }) {
  const rows: [string, string, string][] = [
    [tr('検索・区分(NCAA/NAIAなど)の絞り込み', 'Search & division filters (NCAA/NAIA etc.)'), '○', '○'],
    [tr('州・リーグ・競技の絞り込み', 'State / conference / sport filters'), tr('各1つ', '1 each'), tr('複数同時', 'Multiple')],
    [tr('お気に入り', 'Favorites'), tr(`${FREE_FAVS}校`, `${FREE_FAVS}`), tr('無制限', 'Unlimited')],
    [tr('学校の比較', 'Compare schools'), tr(`${FREE_CMP}校`, `${FREE_CMP}`), tr(`${PAID_CMP}校`, `${PAID_CMP}`)],
    [tr('英語スコア(TOEFL等)の目安をアプリ内で表示', 'English test scores (TOEFL etc.) shown in-app'), '—', '○'],
  ];
  return (
    <ScrollView style={st.root} contentContainerStyle={{ paddingBottom: 48 }}>
      <Pressable onPress={onBack}><Text style={st.link}>{tr('← 戻る', '← Back')}</Text></Pressable>
      <Text style={st.title}>{tr('プラン', 'Plans')}</Text>
      <View style={st.summary}>
        <Text style={st.name}>{tr('有料プラン 月額 ¥500(仮)', 'Paid plan ¥500/month (provisional)')}</Text>
        <Text style={st.meta}>{tr('年額 ¥3,900(仮)・最初の7日間は無料(予定)', '¥3,900/year (provisional) ・ 7-day free trial (planned)')}</Text>
        <Text style={st.linkDesc}>{tr('価格は検討中の仮の金額です。まだ決済はつながっていません。', 'Prices are provisional. Payments are not connected yet.')}</Text>
      </View>
      {rows.map(([label, a, b]) => (
        <View key={label} style={st.cmpRow}>
          <Text style={[st.meta, { flex: 1 }]}>{label}</Text>
          <Text style={[st.meta, { width: 64, textAlign: 'center' }]}>{a}</Text>
          <Text style={[st.name, { width: 72, textAlign: 'center', color: '#0a5' }]}>{b}</Text>
        </View>))}
      <View style={[st.cmpRow, { borderBottomWidth: 0 }]}>
        <Text style={[st.linkDesc, { flex: 1 }]}> </Text>
        <Text style={[st.linkDesc, { width: 64, textAlign: 'center' }]}>{tr('無料', 'Free')}</Text>
        <Text style={[st.linkDesc, { width: 72, textAlign: 'center' }]}>{tr('有料', 'Paid')}</Text>
      </View>
      <Pressable style={st.cmpBar} onPress={() => onSet(!premium)}>
        <Text style={st.chipTextOn}>{premium ? tr('無料プランに戻す(試用)', 'Back to free plan (trial switch)') : tr('有料プランを試す(試用スイッチ・無料)', 'Try the paid plan (free trial switch)')}</Text>
      </Pressable>
      <Text style={st.warn}>{tr('※ これは動作確認用の試用スイッチです。正式版では決済後に自動で有料になります。', '* This is a test switch. In the final version the paid plan turns on automatically after payment.')}</Text>
    </ScrollView>
  );
}

function Compare({ list, onBack, onRemove, showCheer }: { list: School[]; onBack: () => void; onRemove: (id: string) => void; showCheer: boolean }) {
  const money = (n: number | null | undefined) => (n == null ? '—' : `$${n.toLocaleString()}`);
  const rows: { label: string; val: (x: School) => string }[] = [
    { label: tr('所在地', 'Location'), val: (x) => `${x.city}, ${x.state}` },
    { label: tr('種別', 'Type'), val: (x) => `${x.level === '4year' ? tr('4年制', '4-year') : tr('短大', 'Junior college')} / ${x.control === 'public' ? tr('公立', 'Public') : tr('私立', 'Private')}` },
    { label: tr('所属', 'Affiliation'), val: (x) => `${x.division}${x.conference ? ` / ${x.conference}` : ''}` },
    { label: tr('学費(州内)', 'Tuition (in-state)'), val: (x) => money(x.tuitionInState) },
    { label: tr('学費(州外・留学生)', 'Tuition (out-of-state / intl)'), val: (x) => money(x.tuitionOutOfState) },
    { label: tr('平均ネットプライス', 'Avg. net price'), val: (x) => money(x.avgNetPrice) },
    { label: tr('アスリート奨学金(最大)', 'Athletic aid (max)'), val: (x) => (x.athleticScholarshipPct == null ? '—' : x.athleticScholarshipPct === 0 ? tr('0%(なし)', '0% (none)') : tr(`最大${x.athleticScholarshipPct}%`, `up to ${x.athleticScholarshipPct}%`)) },
    ...(showCheer ? [{ label: tr('チア', 'Cheer'), val: (x: School) => (x.sports.some((sp: { name: string }) => sp.name === 'Cheerleading') ? tr('あり', 'Yes') : tr('情報なし', 'No info')) }] : []),
    { label: tr('競技数', 'Sports'), val: (x) => tr(`${x.sports.length}種目`, `${x.sports.length}`) },
  ];
  return (
    <ScrollView style={st.root} contentContainerStyle={{ paddingBottom: 48 }}>
      <Pressable onPress={onBack}><Text style={st.link}>{tr('← 戻る', '← Back')}</Text></Pressable>
      <Text style={st.title}>{tr('学校を比較', 'Compare schools')}</Text>
      <ScrollView horizontal>
        <View>
          <View style={st.cmpRow}>
            <Text style={[st.cmpLabel, st.name]}> </Text>
            {list.map((x) => (
              <View key={x.id} style={st.cmpCell}>
                <Text style={st.name}>{getLang() === 'en' ? x.name : x.nameJa ?? x.name}</Text>
                <Pressable onPress={() => onRemove(x.id)}><Text style={st.linkDesc}>{tr('外す', 'Remove')}</Text></Pressable>
              </View>))}
          </View>
          {rows.map((r) => (
            <View key={r.label} style={st.cmpRow}>
              <Text style={[st.cmpLabel, st.meta]}>{r.label}</Text>
              {list.map((x) => <Text key={x.id} style={[st.cmpCell, st.meta]}>{r.val(x)}</Text>)}
            </View>))}
        </View>
      </ScrollView>
      <Text style={st.warn}>{tr('※ 金額は目安です。最新は各校の公式ページで確認してください。', '* Amounts are estimates. Confirm the latest on each official site.')}</Text>
    </ScrollView>
  );
}

const st = StyleSheet.create({
  lockBar: { backgroundColor: '#fff4e5', borderRadius: 8, padding: 10, marginBottom: 8 },
  lockText: { color: '#8a4b00' },
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
