from fastapi import Request, Body
from typing import Dict, Any, Optional, List
import os
import json
import difflib
from utils.slack_api import publish_home_view, post_message

# default_persona.txtのパス
DEFAULT_PERSONA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "default_persona.txt")

async def handle_app_home_opened(request: Request, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    App Homeが開かれたときのイベントを処理する関数
    
    引数:
        request: リクエストオブジェクト
        payload: Slackからのペイロード
    
    戻り値:
        Slack応答フォーマットのJSON
    """
    try:
        # ユーザーIDを取得
        user_id = payload.get("event", {}).get("user")
        
        if not user_id:
            print("ユーザーIDが見つかりません")
            return {}
        
        # 現在のペルソナ設定を読み込む
        try:
            with open(DEFAULT_PERSONA_PATH, "r", encoding="utf-8") as f:
                current_persona = f.read()
        except Exception as e:
            print(f"ペルソナ設定ファイルの読み込みに失敗しました: {str(e)}")
            current_persona = "ペルソナ設定ファイルの読み込みに失敗しました"
        
        # App Homeのビュー定義
        view = {
            "type": "home",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "ペルソナ設定の編集",
                        "emoji": True
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "以下のテキストエリアでペルソナ設定を編集できます。編集が完了したら「更新」ボタンをクリックしてください。"
                    }
                },
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
                        "text": "ペルソナ設定",
                        "emoji": True
                    }
                },
                {
                    "type": "actions",
                    "block_id": "persona_actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "更新",
                                "emoji": True
                            },
                            "style": "primary",
                            "value": "update_persona",
                            "action_id": "update_persona_button"
                        }
                    ]
                }
            ]
        }
        
        # App Homeビューを公開
        response = publish_home_view(user_id, view)
        
        if not response.get("ok"):
            print(f"App Homeビューの公開に失敗しました: {response.get('error')}")
        
        return {}
    
    except Exception as e:
        print(f"Error in handle_app_home_opened: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

async def handle_app_home_interaction(request: Request, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    App Homeでのインタラクションを処理する関数
    
    引数:
        request: リクエストオブジェクト
        payload: Slackからのペイロード
    
    戻り値:
        Slack応答フォーマットのJSON
    """
    try:
        # アクションIDを取得
        action_id = payload.get("actions", [{}])[0].get("action_id")
        print(payload)
        
        if action_id == "update_persona_button":
            # ユーザーIDを取得
            user_id = payload.get("user", {}).get("id")
            
            # ビューの状態から入力値を取得
            state = payload.get("view", {}).get("state", {}).get("values", {})
            print(state)
            persona_input = state.get("persona_block", {}).get("persona_input", {}).get("value", "")
            
            # ペルソナ設定を更新
            try:
                # 更新前のペルソナ設定を読み込む
                try:
                    with open(DEFAULT_PERSONA_PATH, "r", encoding="utf-8") as f:
                        old_persona = f.read()
                except Exception as e:
                    old_persona = ""
                    print(f"Warning: Could not read old persona: {str(e)}")
                
                # 差分を計算
                diff_lines = list(difflib.unified_diff(
                    old_persona.splitlines(),
                    persona_input.splitlines(),
                    fromfile="旧ペルソナ",
                    tofile="新ペルソナ",
                    lineterm=""
                ))
                
                # 差分がない場合のメッセージ
                if not diff_lines:
                    diff_text = "変更はありません。"
                else:
                    diff_text = "\n".join(diff_lines)
                
                # ペルソナ設定を更新
                with open(DEFAULT_PERSONA_PATH, "w", encoding="utf-8") as f:
                    f.write(persona_input)
                
                print(f"ペルソナ設定を更新しました")
                
                # 更新成功のメッセージをDMで送信
                message_response = post_message(
                    user_id,
                    f"ペルソナ設定を更新しました！\nペルソナ設定の変更点:\n```{diff_text}```",
                )

                # App Homeを更新して成功メッセージを表示
                await handle_app_home_opened(request, {"event": {"user": user_id}})
                
                return {}
            
            except Exception as e:
                print(f"ペルソナ設定の更新に失敗しました: {str(e)}")
                
                # エラーメッセージをDMで送信
                post_message(
                    user_id,
                    f"ペルソナ設定の更新に失敗しました: {str(e)}"
                )
                
                return {}
        
        return {}
    
    except Exception as e:
        print(f"Error in handle_app_home_interaction: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}
