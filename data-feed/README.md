# college-sports-data
College Sports Finder アプリ用の公開データ(米国の4年制大学・短大: NCAA / NAIA / NJCAA / CCCAA / NWAC)。

- 配信ファイル: `public-data/schools.json`(毎週月曜に GitHub Actions が自動更新)
- 出典: 米国教育省 EADA(競技・所属・運動奨学金総額)、College Scorecard(場所・学費)、NCAA Directory(カンファレンス)
- 手動修正: `data/overrides.json`(キーは unitid)。更新後も上書きされません
- `data/scorecard.json` は年1回、普通のPCで `node scripts/refresh-scorecard.mjs` を実行して更新(GitHubのサーバーからは配布元が403のため)

アプリ側の取得先: `https://raw.githubusercontent.com/ryugaku-real/college-sports-data/main/public-data/schools.json`
