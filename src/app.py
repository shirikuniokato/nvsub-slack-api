from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse
import json
from typing import Dict, Any

from slack_verification import add_slack_verification_middleware
from commands.superchat import superchat_endpoint
from commands.aibot import app_mention_endpoint
from commands.update_persona_command import update_persona_command, handle_update_persona_submission
from commands.app_home import handle_app_home_opened, handle_app_home_interaction
from commands.nai_command import nai_command

# FastAPIのインスタンス作成
app = FastAPI(title="Slash Commands API", description="Slackのスラッシュコマンドを処理するAPI")

# Slack検証ミドルウェアを追加
add_slack_verification_middleware(app)

# スーパーチャットコマンドのエンドポイントを登録
app.post("/superchat")(superchat_endpoint)

# ペルソナ更新コマンドのエンドポイントを登録
app.post("/update_persona")(update_persona_command)

# 野良猫AIプロバイダー管理コマンドのエンドポイントを登録
app.post("/ai_provider")(nai_command)

# Slackイベントを処理するエンドポイント
@app.post("/events")
async def events_endpoint(request: Request):
    """
    Slackのイベントを処理するエンドポイント
    
    引数:
        request: リクエストオブジェクト
    
    戻り値:
        適切なレスポンス
    """
    try:
        # リクエストボディをJSONとして解析
        payload = await request.json()
        
        # イベントタイプを確認
        event_type = payload.get("event", {}).get("type")
        
        # イベントタイプに基づいて適切な関数を呼び出す
        if event_type == "app_mention":
            # アプリがメンションされた場合
            return await app_mention_endpoint(request, payload)
        elif event_type == "app_home_opened":
            # App Homeが開かれた場合
            return await handle_app_home_opened(request, payload)
        
        # 未知のイベントタイプの場合は空のレスポンスを返す
        return {}
    
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        return JSONResponse(status_code=400, content={"error": f"Invalid JSON payload: {str(e)}"})
    except Exception as e:
        print(f"Error in events_endpoint: {str(e)}")
        print(f"Payload: {payload}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Internal server error: {str(e)}"})

@app.post("/interactions")
async def interactions_endpoint(request: Request):
    """
    Slackのインタラクティブコンポーネント（モーダルの送信など）を処理するエンドポイント
    
    引数:
        request: リクエストオブジェクト
    
    戻り値:
        適切なレスポンス
    """
    try:
        # フォームデータを取得
        form_data = await request.form()
        
        # payloadフィールドを取得
        payload_str = form_data.get("payload", "{}")
        
        # ペイロードをJSONとしてパース
        payload_json = json.loads(payload_str)
        
        # ペイロードのタイプを確認
        payload_type = payload_json.get("type")
        
        if payload_type == "view_submission":
            # モーダルの送信
            callback_id = payload_json.get("view", {}).get("callback_id")
            
            if callback_id == "update_persona_modal":
                # ペルソナ更新モーダルの送信
                return await handle_update_persona_submission(request, payload_json)
        elif payload_type == "block_actions":
            # ブロックアクション（ボタンクリックなど）
            action_id = payload_json.get("actions", [{}])[0].get("action_id", "")
            
            if action_id in ["update_persona_button", "select_provider"]:
                # App Homeでのインタラクション（ペルソナ更新ボタンクリックまたはAIプロバイダー選択）
                return await handle_app_home_interaction(request, payload_json)
        
        # 未知のペイロードタイプの場合は空のレスポンスを返す
        return {}
    
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        return JSONResponse(status_code=400, content={"error": f"Invalid JSON payload: {str(e)}"})
    except Exception as e:
        print(f"Error in interactions_endpoint: {str(e)}")
        print(f"Payload: {payload_json}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Internal server error: {str(e)}"})

@app.get("/")
async def root():
    """
    ルートエンドポイント - APIが稼働していることを確認
    """
    return {"status": "API is running", "endpoints": ["/superchat", "/update_persona", "/ai_provider", "/events", "/interactions"]}
