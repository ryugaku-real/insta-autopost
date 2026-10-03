# College Sports Finder
米国の4年制大学・短大(NCAA D1/D2/D3, NAIA, NJCAA, CCCAA, NWAC)を、スポーツ・Division・場所・奨学金で検索するスマホアプリ(Expo / React Native)。

    npm install && npx expo start     # Expo Go で実行

- データ: 米国教育省 EADA(競技・所属)+ College Scorecard(場所・学費)。`python3 scripts/build-athletics.py schools.xlsx` → `npm run build:data`。生成物 `src/data/schools.generated.json`(1,876校)はコミット済み。

## データの更新(アプリを出したあとも更新できる)
- 配信データは公開リポジトリ [ryugaku-real/college-sports-data](https://github.com/ryugaku-real/college-sports-data) にあり、毎週月曜に GitHub Actions が最新データ(EADA・NCAA・College Scorecard)で自動更新します。
- アプリは起動時に `app.json` の `extra.dataUrl`(上記リポジトリの `public-data/schools.json`)を取得して表示します。失敗時は端末キャッシュ→同梱データを使うので、ストア審査なしで反映されます。
- すぐ変わる情報(カンファレンス、奨学金ページURLなど)は、データ側リポジトリの `data/overrides.json` に `unitid` をキーにして書けば、自動更新後も反映されます。
- このリポジトリ内の `scripts/` `data/` は同じ仕組みの控えで、アプリの同梱データ(`src/data/schools.generated.json`)を作るのに使います。
