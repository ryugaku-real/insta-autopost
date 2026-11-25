# AI文章チェッカー

文章を貼ると、AI生成の可能性を推定するWebアプリ。

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # 無くても文体統計だけは動く
python app.py                          # http://localhost:5000
```

- `stats.py` : APIキー不要の文体統計(文長のばらつき・語彙多様性)
- `llm.py`   : Claudeによる文ごとの判定(モデルは環境変数 `DETECTOR_MODEL` で変更)
- 結果は**目安であり証拠ではない**(誤判定あり)。UIにも注意書きを表示している。

## 公開(Render)
1. このリポジトリを Render に接続し、Blueprint として `render.yaml` を読み込む
2. 環境変数 `ANTHROPIC_API_KEY`(APIキー)と `APP_PASSWORD`(合言葉)を画面で入力
3. デプロイ後、URLを開くと合言葉(ユーザー名は何でもOK)を聞かれる

`APP_PASSWORD` を設定しないと誰でも使え、API料金があなたに掛かります。必ず設定してください。
`RATE_PER_MIN` でIPごとの1分あたり上限を調整できます(既定10)。
