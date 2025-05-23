from fastapi import Request, Body, Form, HTTPException
from typing import Dict, Any, Optional, List
import os
import json
import difflib
from utils.slack_api import open_modal, post_message
from data.handlers import add_history_entry, PERSONA_HISTORY_FILE

# default_persona.txtのパス
DEFAULT_PERSONA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "default_persona.txt")

async def update_persona_command(
    request: Request,
    token: str = Form(...),
    team_id: str = Form(...),
    team_domain: str = Form(...),
    channel_id: str = Form(...),
    channel_name: str = Form(...),
    user_id: str = Form(...),
    user_name: str = Form(...),
    command: str = Form(...),
    text: str = Form(""),
    response_url: str = Form(...),
    trigger_id: str = Form(...)
) -> Dict[str, Any]:
    """
    Slackの /update_persona コマンドを処理するエンドポイント
    
    引数:
        request: リクエストオブジェクト
        token: Slackアプリの検証トークン
        team_id: チームID
        team_domain: チームドメイン
        channel_id: チャンネルID
        channel_name: チャンネル名
        user_id: ユーザーID
        user_name: ユーザー名
        command: コマンド（例：/update_persona）
        text: コマンドに続くテキスト
        response_url: レスポンスを送信するためのURL
        trigger_id: モーダルを表示するためのトリガーID
    
    戻り値:
        Slack応答フォーマットのJSON
    """
    try:
        # トリガーIDはすでに引数として受け取っているので、チェックは不要
        
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
            "private_metadata": json.dumps({
                "channel_id": channel_id,
                "user_id": user_id
            }),
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

async def handle_update_persona_submission(request: Request, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    ペルソナ設定の更新モーダルの送信を処理するエンドポイント
    
    引数:
        request: リクエストオブジェクト
        payload: Slackからのペイロード
    
    戻り値:
        Slack応答フォーマットのJSON
    """
    try:
        # デバッグ用にペイロードを出力
        print(f"handle_update_persona_submission received payload: {json.dumps(payload, indent=2)}")
        
        # ペイロードからビュー情報を取得
        view = payload.get("view", {})
        
        # ビューの状態から入力値を取得
        state = view.get("state", {}).get("values", {})
        print(f"State values: {json.dumps(state, indent=2)}")
        
        persona_input = state.get("persona_block", {}).get("persona_input", {}).get("value", "")
        
        # ユーザー情報を取得
        user_id = payload.get("user", {}).get("id")
        
        # チャンネル情報を取得（プライベートメタデータから）
        private_metadata = {}
        try:
            private_metadata = json.loads(view.get("private_metadata", "{}"))
        except json.JSONDecodeError:
            private_metadata = {}
        
        channel_id = private_metadata.get("channel_id", user_id)  # チャンネルIDがない場合はユーザーIDを使用（DM）
        
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
            
            # 履歴に記録（変更前後の全文も保存）
            details = {
                "diff": diff_text,
                "from_modal": True
            }
            add_history_entry(PERSONA_HISTORY_FILE, "update_persona", details, user_id, 
                             content_before=old_persona, content_after=persona_input)
            
            # 更新成功のメッセージをチャンネルに送信
            message_response = post_message(
                channel_id,
                f"<@{user_id}> がペルソナ設定を更新しました！",
            )
            
            # スレッドに差分を投稿
            if message_response.get("ok"):
                post_message(
                    channel_id,
                    f"ペルソナ設定の変更点:\n```{diff_text}```",
                    message_response.get("ts"),  # スレッドの親メッセージのタイムスタンプ
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
        print(f"Error in handle_update_persona_submission: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "response_action": "errors",
            "errors": {
                "persona_block": f"エラーが発生しました: {str(e)}"
            }
        }
