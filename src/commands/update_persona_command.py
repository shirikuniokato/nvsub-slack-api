from fastapi import Request, Body, HTTPException
from typing import Dict, Any
import os
import json
from utils.slack_api import open_modal

# default_persona.txtのパス
DEFAULT_PERSONA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "default_persona.txt")

async def update_persona_command(request: Request, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """
    Slackの /update_persona コマンドを処理するエンドポイント
    
    引数:
        request: リクエストオブジェクト
        payload: Slackからのペイロード
    
    戻り値:
        Slack応答フォーマットのJSON
    """
    try:
        # トリガーIDを取得
        trigger_id = payload.get("trigger_id")
        
        if not trigger_id:
            return {
                "response_type": "ephemeral",
                "text": "トリガーIDが取得できませんでした。"
            }
        
        # 現在のペルソナ設定を読み込む
        try:
            with open(DEFAULT_PERSONA_PATH, "r", encoding="utf-8") as f:
                current_persona = f.read()
        except Exception as e:
            return {
                "response_type": "ephemeral",
                "text": f"ペルソナ設定ファイルの読み込みに失敗しました: {str(e)}"
            }
        
        # モーダルのビュー定義
        view = {
            "type": "modal",
            "callback_id": "update_persona_modal",
            "title": {
                "type": "plain_text",
                "text": "ペルソナ設定の編集"
            },
            "submit": {
                "type": "plain_text",
                "text": "更新"
            },
            "close": {
                "type": "plain_text",
                "text": "キャンセル"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "persona_block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "persona_input",
                        "multiline": True,
                        "initial_value": current_persona
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "ペルソナ設定"
                    },
                    "hint": {
                        "type": "plain_text",
                        "text": "ペルソナ設定を編集してください。"
                    }
                }
            ]
        }
        
        # モーダルを表示
        modal_response = open_modal(trigger_id, view)
        
        if not modal_response.get("ok"):
            return {
                "response_type": "ephemeral",
                "text": f"モーダルの表示に失敗しました: {modal_response.get('error')}"
            }
        
        # モーダルが表示されたことを通知
        return {
            "response_type": "ephemeral",
            "text": "ペルソナ設定の編集モーダルを表示しました。"
        }
    
    except Exception as e:
        # エラーが発生した場合はエラーメッセージを返す
        return {
            "response_type": "ephemeral",
            "text": f"エラーが発生しました: {str(e)}"
        }

async def handle_update_persona_submission(request: Request, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """
    ペルソナ設定の更新モーダルの送信を処理するエンドポイント
    
    引数:
        request: リクエストオブジェクト
        payload: Slackからのペイロード
    
    戻り値:
        Slack応答フォーマットのJSON
    """
    try:
        # ペイロードからビュー情報を取得
        view = payload.get("view", {})
        
        # ビューの状態から入力値を取得
        state = view.get("state", {}).get("values", {})
        persona_input = state.get("persona_block", {}).get("persona_input", {}).get("value", "")
        
        # ユーザー情報を取得
        user_id = payload.get("user", {}).get("id")
        
        # チャンネル情報を取得（プライベートメタデータから）
        # 注: モーダルを開く際にプライベートメタデータにチャンネルIDを設定する必要があります
        # 現在の実装ではこれが設定されていないため、ユーザーにDMを送信します
        
        # ペルソナ設定を更新
        try:
            with open(DEFAULT_PERSONA_PATH, "w", encoding="utf-8") as f:
                f.write(persona_input)
            
            # 更新成功のメッセージをユーザーに送信
            from utils.slack_api import post_message
            post_message(
                user_id,
                "ペルソナ設定を更新しました！\n```\n" + persona_input + "\n```"
            )
            
            return {}  # モーダルの送信に対するレスポンスは空でOK
        
        except Exception as e:
            # エラーメッセージを返す
            return {
                "response_action": "errors",
                "errors": {
                    "persona_block": f"ペルソナ設定の更新に失敗しました: {str(e)}"
                }
            }
    
    except Exception as e:
        # エラーメッセージを返す
        return {
            "response_action": "errors",
            "errors": {
                "persona_block": f"エラーが発生しました: {str(e)}"
            }
        }
