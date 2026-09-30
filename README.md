# インスタ自動投稿（insta-autopost）

`posts/` に投稿（画像と文章）を置いておくと、予定の時刻に自動でインスタに投稿される仕組みです。
GitHub Actions（無料）で毎時チェックして、時刻を過ぎた投稿を Instagram の公式APIで公開します。

```
posts/
  2026-10-05-bank/      ← 1投稿 = 1フォルダ（名前は半角英数字と - だけ）
    post.json           ← 公開日時・キャプション・画像の順番
    01.jpg 02.jpg ...   ← カルーセルの画像（JPGだけ・最大10枚）
published.json          ← 投稿済みの記録（自動で更新される。触らない）
```

---

## 初回セットアップ（30〜40分・1回だけ）

### 1. インスタをプロアカウントにする
インスタのアプリ →「設定」→「アカウントの種類とツール」→「プロアカウントに切り替える」→ **クリエイター** を選ぶ。

### 2. GitHub でリポジトリを作る
1. https://github.com でアカウントを作る
2. 右上の「＋」→「New repository」
   - 名前: `insta-autopost`
   - **Public** を選ぶ（画像をインスタに渡すため、公開リポジトリにする必要があります）
3. 「uploading an existing file」から、このフォルダの中身を全部ドラッグ＆ドロップして「Commit changes」
   - ⚠️ Macでは `.github` フォルダが見えません。Finderで **Command + Shift + .（ピリオド）** を押すと表示されます。`.github` も必ずアップしてください

### 3. Meta for Developers でアクセストークンを発行する
1. https://developers.facebook.com に Facebook アカウントでログインし、開発者として登録する
2. 「マイアプリ」→「アプリを作成」
   - ユースケース: **「Instagramでメッセージとコンテンツを管理」**（Instagram API）を選ぶ
3. アプリの画面で「Instagramログインによる API 設定」を開く
4. 「アクセストークンを生成」→「アカウントを追加」→ 自分のインスタでログインして許可する
5. 表示された **トークンをコピー**（⚠️ チャットやSNSには絶対に貼らない）

※ Meta の画面は時々変わります。詰まったらスクショを送ってください（トークンは隠して）。

### 4. トークンを GitHub に保存する
リポジトリの「Settings」→「Secrets and variables」→「Actions」→「New repository secret」

| Name | Secret |
|---|---|
| `IG_ACCESS_TOKEN` | 手順3でコピーしたトークン |

### 5. 接続テストをして、ユーザーIDを保存する
1. リポジトリの「Actions」タブ →（初回は「I understand…」を押して有効化）
2. 左の「接続テスト」→「Run workflow」
3. 結果を開くと `IG_USER_ID にはこれを入れる: 1784…` と出るので、その数字を Secret に追加

| Name | Secret |
|---|---|
| `IG_USER_ID` | 表示された数字 |

もう一度「接続テスト」を実行して **接続OK** と出れば成功です。

### 6. トークン自動更新を設定する（おすすめ）
トークンは **60日で切れます**。毎週自動で更新するための設定です。

1. GitHub 右上のアイコン →「Settings」→「Developer settings」→「Personal access tokens」→「Fine-grained tokens」→「Generate new token」
   - Repository access: **Only select repositories** → `insta-autopost`
   - Permissions →「Secrets」を **Read and write**
   - 有効期限: 最長にする（切れたら作り直し）
2. できたトークンを Secret `GH_PAT` として保存

これで毎週月曜にインスタのトークンが自動で延長されます。

---

## 投稿の追加（毎週やること・10分）

1. Canva でスライドを **JPG** で書き出す（サイズ 1080×1350）
2. ファイル名を `01.jpg`, `02.jpg` … と表示順にする
3. GitHub で `posts/<フォルダ>/` を開き、「Add file」→「Upload files」で画像を入れる
4. 同じフォルダの `post.json` を開き（鉛筆マークで編集）、`"draft": true` を **`false`** にして保存

`post.json` の書き方:
```json
{
  "draft": false,
  "publish_at": "2026-10-05 19:00",
  "caption": "キャプション本文\n改行は \\n で書く #ハッシュタグ",
  "images": ["01.jpg", "02.jpg", "03.jpg"]
}
```
- `publish_at` は **シカゴ時間**（夜7時 ＝ 日本の翌朝9〜10時）
- 画像を入れると「投稿データのチェック」が自動で動きます。✅ならOK、❌なら中のメッセージを見て直す

## 動作テスト（投稿はしない）
「Actions」→「自動投稿」→「Run workflow」→「テスト実行」にチェックが入ったまま実行。
公開される予定の投稿と画像のURLが表示されます。

---

## 知っておくこと
- **時間のズレ**：GitHub の混雑で、予定より数分〜数十分遅れて投稿されることがあります
- **24時間以上遅れた投稿は公開しません**（古い投稿が突然出るのを防ぐため）。`publish_at` を直せば公開されます
- **二重投稿の防止**：投稿済みは `published.json` に記録され、同じキャプションの投稿がすでにあればスキップします
- **失敗したとき**：GitHub から失敗のメールが届きます。Actions の結果画面の赤い × を開くと、原因が日本語で出ます
- **公開リポジトリなので**、予約中の画像と文章は誰でも見られる状態です（公開前のネタバレが気になる場合は相談してください）
- **60日間何も更新がないと**、GitHub が自動実行を止めます。毎週投稿を足していれば大丈夫です
- **PR表記**：アフィリエイトやPR案件の投稿は、キャプションの最初に「PR」「広告」などを入れる（日本のステマ規制）
