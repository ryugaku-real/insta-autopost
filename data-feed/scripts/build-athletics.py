"""Convert the U.S. Dept. of Education EADA dataset into data/athletics.json (keyed by unitid).

Source: https://ope.ed.gov/athletics/#/datafile/list  -> "Data for academic year 2024-25" (EADA_2024-2025.zip)
Usage:  python3 scripts/build-athletics.py path/to/schools.xlsx path/to/instLevel.xlsx
Covers NCAA D1/D2/D3, NAIA, NJCAA D1-D3, CCCAA, NWAC (sports + men/women participation).
"""
import json, sys, openpyxl

CLASS = {1: ('NCAA', 'D1'), 2: ('NCAA', 'D1'), 3: ('NCAA', 'D1'), 4: ('NCAA', 'D2'), 5: ('NCAA', 'D2'),
         6: ('NCAA', 'D3'), 7: ('NCAA', 'D3'), 9: ('NAIA', 'NAIA'), 10: ('NAIA', 'NAIA'),
         12: ('NJCAA', 'NJCAA-D1'), 13: ('NJCAA', 'NJCAA-D2'), 14: ('NJCAA', 'NJCAA-D3'),
         17: ('CCCAA', 'CCCAA'), 19: ('NWAC', 'NWAC')}
JA = {'Basketball': 'バスケットボール', 'Volleyball': 'バレーボール', 'Soccer': 'サッカー', 'Baseball': '野球',
      'Softball': 'ソフトボール', 'Golf': 'ゴルフ', 'Tennis': 'テニス', 'Football': 'アメリカンフットボール',
      'Track and Field and Cross Country (combined)': '陸上・クロスカントリー', 'Cross Country': 'クロスカントリー',
      'Lacrosse': 'ラクロス', 'Track and Field (Outdoor)': '陸上(屋外)', 'Wrestling': 'レスリング',
      'Swimming and Diving (combined)': '水泳・飛込', 'Swimming': '水泳', 'Track and Field (Indoor)': '陸上(室内)',
      'Field Hockey': 'フィールドホッケー', 'Beach Volleyball': 'ビーチバレー', 'Bowling': 'ボウリング',
      'Ice Hockey': 'アイスホッケー', 'Rowing': 'ボート', 'Water Polo': '水球', 'Gymnastics': '体操',
      'Rodeo': 'ロデオ', 'Equestrian': '馬術', 'Fencing': 'フェンシング', 'Rifle': 'ライフル', 'Skiing': 'スキー',
      'Squash': 'スカッシュ', 'Sailing': 'セーリング', 'Weight Lifting': 'ウエイトリフティング',
      'Archery': 'アーチェリー', 'Badminton': 'バドミントン', 'Table Tennis': '卓球', 'Diving': '飛込',
      'Synchronized Swimming': 'アーティスティックスイミング'}

ws = openpyxl.load_workbook(sys.argv[1], read_only=True).active
it = ws.iter_rows(values_only=True)
ix = {k: i for i, k in enumerate(next(it))}
out = {}
for r in it:
    cls = CLASS.get(r[ix['ClassificationCode']])
    sport = r[ix['Sports']]
    if not cls or sport not in JA:
        continue
    n = lambda k: r[ix[k]] or 0
    men, women = n('PARTIC_MEN') + n('PARTIC_COED_MEN') > 0, n('PARTIC_WOMEN') + n('PARTIC_COED_WOMEN') > 0
    if not (men or women):
        continue
    e = out.setdefault(str(r[ix['unitid']]), {'association': cls[0], 'division': cls[1], 'sports': []})
    e['sports'].append({'name': sport, 'nameJa': JA[sport], 'gender': 'Both' if men and women else 'M' if men else 'W'})
# athletic student aid (USD, institution level) from instLevel.xlsx
ws2 = openpyxl.load_workbook(sys.argv[2], read_only=True).active
it2 = ws2.iter_rows(values_only=True)
ix2 = {k: i for i, k in enumerate(next(it2))}
for r in it2:
    e = out.get(str(r[ix2['unitid']]))
    if not e:
        continue
    g = lambda k: r[ix2[k]] or 0
    e['athleticAid'] = {'total': g('STUDENTAID_TOTAL'), 'men': g('STUDENTAID_MEN'), 'women': g('STUDENTAID_WOMEN'), 'coed': g('STUDENTAID_COED')}
json.dump(out, open('data/athletics.json', 'w'), ensure_ascii=False, indent=0)
print(len(out), 'schools')
