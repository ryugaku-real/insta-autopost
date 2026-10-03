# College Sports Finder
米国の4年制大学・短大(NCAA D1/D2/D3, NAIA, NJCAA, CCCAA, NWAC)を、スポーツ・Division・場所・奨学金で検索するスマホアプリ(Expo / React Native)。

    npm install && npx expo start     # Expo Go で実行

- データ: 米国教育省 EADA(競技・所属)+ College Scorecard(場所・学費)。`python3 scripts/build-athletics.py schools.xlsx` → `SCORECARD_API_KEY=... npm run build:data`。生成物 `src/data/schools.generated.json`(1,876校)はコミット済み。
