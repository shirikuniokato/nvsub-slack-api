# Slash Commands API

Slack の Slash Commands を処理する API サーバー

## 機能

- スーパーチャットの登録と統計表示
- ユーザー表示名の管理
- Slack からのリクエストのみを許可するセキュリティ対策

## 必要条件

- Python 3.8 以上
- FastAPI
- Uvicorn
- Nginx
- SSL 証明書（Let's Encrypt など）

## インストール手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/nvsub-slack-api.git
cd nvsub-slack-api
```

### 2. 仮想環境の作成とパッケージのインストール

```bash
python -m venv venv
source venv/bin/activate  # Linuxの場合
# または
.\venv\Scripts\activate  # Windowsの場合

pip install -r requirements.txt
```

### 3. 環境変数の設定

Slack の署名シークレットを環境変数に設定します。

```bash
export SLACK_SIGNING_SECRET="your_slack_signing_secret"
```

永続的に設定するには、`~/.bashrc`または`~/.bash_profile`に追加します。

```bash
echo 'export SLACK_SIGNING_SECRET="your_slack_signing_secret"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Nginx の設定

1. Nginx をインストール

```bash
sudo apt update
sudo apt install nginx
```

2. SSL 証明書の取得（Let's Encrypt を使用）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain.com
```

3. Nginx 設定ファイルの配置

```bash
sudo cp nginx_config.conf /etc/nginx/sites-available/slack-api.conf
sudo ln -s /etc/nginx/sites-available/slack-api.conf /etc/nginx/sites-enabled/
```

4. 設定ファイルを編集して、ドメイン名と SSL 証明書のパスを変更

```bash
sudo nano /etc/nginx/sites-available/slack-api.conf
```

5. Nginx の設定をテストして再起動

```bash
sudo nginx -t
sudo systemctl restart nginx
```

### 5. アプリケーションの実行

開発環境での実行：

```bash
uvicorn src.main:app --reload
```

本番環境での実行（systemd を使用）：

1. systemd サービスファイルの作成

```bash
sudo nano /etc/systemd/system/slack-api.service
```

以下の内容を追加：

```
[Unit]
Description=Slack API Service
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/path/to/nvsub-slack-api
Environment="SLACK_SIGNING_SECRET=your_slack_signing_secret"
ExecStart=/path/to/nvsub-slack-api/venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

2. サービスの有効化と起動

```bash
sudo systemctl enable slack-api
sudo systemctl start slack-api
```

3. ステータスの確認

```bash
sudo systemctl status slack-api
```

## Slack アプリの設定

1. [Slack API](https://api.slack.com/apps)にアクセスして、新しいアプリを作成
2. 「Slash Commands」を有効化
3. 新しいコマンドを追加
   - コマンド: `/superchat`
   - リクエスト URL: `https://your_domain.com/superchat`
   - 短い説明: スーパーチャットの登録と統計表示
4. 「Basic Information」ページで「Signing Secret」を取得し、環境変数に設定

## セキュリティ対策

この API は以下のセキュリティ対策を実装しています：

1. **Slack リクエストの検証**：

   - FastAPI ミドルウェアで Slack からのリクエストを検証
   - リクエストの署名とタイムスタンプを確認

2. **Nginx による制限**：
   - Slack からのリクエストのみを許可（X-Slack-Request-Timestamp ヘッダーの確認）
   - `/superchat`エンドポイントのみを公開
   - HTTPS の強制
   - リクエストボディのサイズ制限

## 使用方法

Slack で以下のコマンドを使用できます：

### スーパーチャットの登録

```
/superchat add <金額> [-m|--message <メッセージ>] [-y|--youtube <YouTubeチャンネル>] [-d|--date <日付>]
```

例：

```
/superchat add 1000 -m こんにちは！
/superchat add 500 --message "長いメッセージもOK" --youtube https://youtube.com/channel/123
/superchat add 2000 --date 2025-04-13
```

### スーパーチャットの統計表示

```
/superchat stat [-u|--user <ユーザー名>] [-d|--days <日数>] [-a|--all] [-m|--me]
```

例：

```
/superchat stat
/superchat stat -u @username
/superchat stat --days 7
/superchat stat --all
/superchat stat --me
/superchat stat --all --me
```

### ヘルプの表示

```
/superchat help
```

## ファイル構成

- `src/main.py`: エントリーポイント（FastAPI アプリケーションのインポート）
- `src/app.py`: FastAPI アプリケーションの設定と初期化
- `src/parser.py`: コマンドパーサー
- `src/slack_verification.py`: Slack リクエスト検証ミドルウェア
- `src/data/`: データ操作関連のモジュール
  - `handlers.py`: データの読み込みと保存に関する関数
  - `superchat_data.json.template`: スーパーチャットデータのテンプレート
  - `user_display_names.json.template`: ユーザー表示名のテンプレート
- `src/utils/`: ユーティリティ関数
  - `display_name.py`: ユーザー表示名の取得関数
- `src/commands/`: コマンド処理関連のモジュール
  - `superchat.py`: スーパーチャットコマンドのエンドポイント
  - `add_command.py`: add サブコマンドの処理
  - `stat_command.py`: stat サブコマンドの処理
- `nginx_config.conf`: Nginx の設定ファイル
- `requirements.txt`: 必要な Python パッケージ
- `.gitignore`: Git 管理から除外するファイルの設定

## 初期セットアップ

新しい環境でアプリケーションを実行する前に、データファイルのテンプレートをコピーしてください：

```bash
cp src/data/superchat_data.json.template src/data/superchat_data.json
cp src/data/user_display_names.json.template src/data/user_display_names.json
```

これらのデータファイルは環境ごとに更新され、Git 管理されません。
