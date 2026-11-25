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
