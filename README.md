# nvsub-slack-api

Slack のスラッシュコマンドを処理する API サーバー。スーパーチャット機能を実装しています。
※ 全て Cline で作ってみた（claude-3.7-sonnet）

## 機能

- `/superchat` コマンドの処理
- shlex と argparse を使用したコマンドパーサー
- サブコマンド:
  - `add`: スーパーチャットの登録
  - `stat`: スーパーチャットの統計表示

### add サブコマンドのオプション

- 金額（位置引数、int 型、必須）: スパチャの金額
- `-m` / `--message`（str 型、任意）: スパチャ時のコメント（スペース含め OK）
- `-y` / `--youtube`（str 型、任意）: YouTube チャンネル URL や ID（将来の分析用）

### stat サブコマンドのオプション

- `-u` / `--user`（str 型、任意）: 特定ユーザーの統計を表示
- `-d` / `--days`（int 型、任意、デフォルト: 30）: 過去 X 日間の統計を表示

## セットアップ

1. 依存パッケージのインストール:

```bash
pip install -r requirements.txt
```

2. API サーバーの起動:

```bash
uvicorn src.main:app --reload
```

サーバーは http://localhost:8000 で起動します。

## 使用方法

### API エンドポイント

- `POST /superchat`: スーパーチャットコマンドを処理
  - フォームパラメータ:
    - `text`: コマンドテキスト（例: `1000 -m こんにちは -y https://youtube.com/channel/123`）
    - `user_name`: コマンドを実行したユーザー名
    - `channel_name`: コマンドが実行されたチャンネル名

### コマンド例

```
# スーパーチャットの登録
/superchat add 1000 -m こんにちは！
/superchat add 500 --message "長いメッセージもOK" --youtube https://youtube.com/channel/123
/superchat add 2000

# スーパーチャットの統計表示
/superchat stat
/superchat stat -u @username
/superchat stat -d 7
/superchat stat --user @username --days 14

# ヘルプの表示
/superchat help
```

### パーサーのテスト

コマンドパーサーの動作を確認するには、以下のコマンドを実行します:

```bash
python -m src.t.test_parser
```

または、コマンドライン引数を直接渡してテスト:

```bash
python -m src.t.test_parser add 1000 -m "テストメッセージ" -y youtube.com/user/test
python -m src.t.test_parser stat -u @username -d 7
```

## 開発

- `src/parser.py`: コマンドパーサーの実装
- `src/main.py`: FastAPI アプリケーション
- `src/t/test_parser.py`: パーサーのテストスクリプト
