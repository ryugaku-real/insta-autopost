# College Sports Finder
米国の4年制大学・短大(NCAA D1/D2/D3, NAIA, NJCAA, CCCAA, NWAC)を、スポーツ・Division・場所・奨学金で検索するスマホアプリ(Expo / React Native)。

    npm install && npx expo start     # Expo Go で実行

- データ: 米国教育省 EADA(競技・所属)+ College Scorecard(場所・学費)。`python3 scripts/build-athletics.py schools.xlsx` → `SCORECARD_API_KEY=... npm run build:data`。生成物 `src/data/schools.generated.json`(1,876校)はコミット済み。

## データの更新(アプリを出したあとも更新できる)
1. **自動更新**: `.github/workflows/update-college-data.yml` が毎週月曜に最新データ(EADA・NCAA・College Scorecard)を取得し、`public-data/schools.json` を更新します。
   - リポジトリの Settings → Secrets → Actions に `SCORECARD_API_KEY` を登録してください。
2. **アプリ側**: 起動時に `app.json` の `extra.dataUrl` からJSONを取得して表示します(失敗時は端末キャッシュ→同梱データ)。ストア審査なしで反映されます。
   - `dataUrl` はアプリから読める公開URLにしてください(リポジトリが非公開の場合は GitHub Pages などで `public-data/` を公開)。
3. **手動修正**: すぐ変わる情報(カンファレンス、奨学金ページURLなど)は `data/overrides.json` に `unitid` をキーにして書けば、次の更新でも上書きされず反映されます。
