from fastapi import FastAPI
from fastapi.responses import JSONResponse

from slack_verification import add_slack_verification_middleware
from commands.superchat import superchat_endpoint
from commands.sql_command import sql_endpoint
from commands.aibot import app_mention_endpoint

# FastAPIのインスタンス作成
app = FastAPI(title="Slash Commands API", description="Slackのスラッシュコマンドを処理するAPI")

# Slack検証ミドルウェアを追加
add_slack_verification_middleware(app)

# スーパーチャットコマンドのエンドポイントを登録
app.post("/superchat")(superchat_endpoint)

# SQLクエリコマンドのエンドポイントを登録
app.post("/sql")(sql_endpoint)

# Slackイベントを処理するエンドポイントを登録
app.post("/events")(app_mention_endpoint)

@app.get("/")
async def root():
    """
    ルートエンドポイント - APIが稼働していることを確認
    """
    return {"status": "API is running", "endpoints": ["/superchat", "/sql", "/events"]}
