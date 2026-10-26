# Atcotify

AtCoder Junior League（AJL）の学校・生徒順位と、AtCoderコンテストの通知を行う Discord Bot です。複数の学校のサーバーで共通利用できます（1サーバー = 1校）。

## 機能

- AJL 学校順位・生徒順位の表示（`/school_rank`、`/school_student_rank`）と定期通知
- AtCoder コンテストのリマインダー（開始前通知）
- コンテスト終了後の結果画像の自動送信
- コンテスト開始前のスレッド自動作成
- AJL の perf / score 変換（`/perf_score_convert`）

## サーバーへの導入手順（サーバー管理者向け）

1. Bot をサーバーに招待します。
2. `/setup` を実行し、学校名を設定します。学校名は AJL の学校一覧から候補が出るので、自分の学校を選んでください。
   - 学校を設定しないと、学校順位の表示・通知は行われません。
3. 必要に応じて通知先チャンネルを設定します（いずれも Bot の設定権限がある人だけが実行できます）。
   - `/reminder---set_channel` リマインダー送信先
   - `/result---set_channel` コンテスト結果の自動送信先
   - `/thread---set_channel` コンテスト前スレッドの作成先
   - `/school_rank_set_ch` 学校順位の定期通知先
   - `/school_student_rank_set_ch` 生徒順位の定期通知先
4. サーバー管理者は `/admin_role_set` で「副管理者ロール」を指定できます。副管理者は Discord のサーバー管理権限なしで Bot の設定変更だけを行えます。

コマンドの一覧は `/help` で確認できます。

## 運用者向け（セルフホスト）

必要なもの: Python 3.13+、[uv](https://docs.astral.sh/uv/)、poppler（結果画像の PDF 変換用。OS のパッケージで `poppler-utils` など）

```bash
uv sync
cp env/config.ini.example env/config.ini  # 無い場合は下記の項目で作成
uv run python main.py
```

`env/config.ini` の主な項目:

- `[TOKEN]` Discord Bot のトークン
- `[SEASON]` AJL のシーズン（例: `2025_winter`）
- `[ATCODER]` AtCoder のログイン情報（順位取得用）
- `[GOOGLE]` 学校順位スプレッドシート連携用のサービスアカウントとスプレッドシート ID
- `[YEAR]` 対象年度

Intents は全て有効にして動作します（運用ツール jishaku が MESSAGE CONTENT Intent を必要とするため）。大規模に公開する場合は、特権 Intents の扱いを再検討してください。

## 開発

```bash
uv run pytest
```

設定はサーバーごとに `bot_settings.json`、配信済み状態は `asset/delivery_state.json` に保存されます（いずれも自動生成）。
