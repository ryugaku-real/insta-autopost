# College Sports Finder
米国の4年制大学・短大(NCAA D1/D2/D3, NAIA, NJCAA, CCCAA, NWAC)を、スポーツ・Division・場所・奨学金で検索するスマホアプリ(Expo / React Native)。

    npm install && npx expo start     # Expo Go で実行

- `src/data/schools.ts` はサンプル6校(未検証)。
- 全校データ: `SCORECARD_API_KEY=... npm run build:data`(College Scorecardで場所・学費、`data/athletics.csv`で所属・Division・競技を結合)。
