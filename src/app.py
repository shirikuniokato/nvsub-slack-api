from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse
import json
from typing import Dict, Any

from slack_verification import add_slack_verification_middleware
from commands.superchat import superchat_endpoint
from commands.aibot import app_mention_endpoint
from commands.update_persona_command import update_persona_command, handle_update_persona_submission

# FastAPIのインスタンス作成
app = FastAPI(title="Slash Commands API", description="Slackのスラッシュコマンドを処理するAPI")

# Slack検証ミドルウェアを追加
add_slack_verification_middleware(app)

# スーパーチャットコマンドのエンドポイントを登録
app.post("/superchat")(superchat_endpoint)

# ペルソナ更新コマンドのエンドポイントを登録
app.post("/update_persona")(update_persona_command)

# Slackイベントを処理するエンドポイントを登録
app.post("/events")(app_mention_endpoint)

@app.post("/interactions")
async def interactions_endpoint(request: Request, payload: str = Body(..., embed=False)):
    """
    Slackのインタラクティブコンポーネント（モーダルの送信など）を処理するエンドポイント
    
    引数:
        request: リクエストオブジェクト
        payload: Slackからのペイロード（JSON文字列）
    
    戻り値:
        適切なレスポンス
    """
    try:
        # ペイロードをJSONとしてパース
        payload_json = json.loads(payload)
        
        # ペイロードのタイプを確認
        payload_type = payload_json.get("type")
        
        if payload_type == "view_submission":
            # モーダルの送信
            callback_id = payload_json.get("view", {}).get("callback_id")
            
            if callback_id == "update_persona_modal":
                # ペルソナ更新モーダルの送信
                return await handle_update_persona_submission(request, payload_json)
        
        # 未知のペイロードタイプの場合は空のレスポンスを返す
        return {}
    
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON payload"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Internal server error: {str(e)}"})

@app.get("/")
async def root():
    """
    ルートエンドポイント - APIが稼働していることを確認
    """
    return {"status": "API is running", "endpoints": ["/superchat", "/update_persona", "/events", "/interactions"]}
