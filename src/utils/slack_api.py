import os
import requests
from typing import Dict, Any, Optional, List

# SlackのAPIトークン（環境変数から取得）
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

def post_message(
    channel: str,
    text: str,
    thread_ts: Optional[str] = None
) -> Dict[str, Any]:
    """
    Slackにメッセージを投稿する関数
    
    引数:
        channel: チャンネルID
        text: 投稿するテキスト
        thread_ts: スレッドのタイムスタンプ（スレッド内の返信の場合）
    
    戻り値:
        Slackからのレスポンス
    """
    if not SLACK_BOT_TOKEN:
        return {"ok": False, "error": "SLACK_BOT_TOKENが設定されていません"}
    
    # APIエンドポイント
    url = "https://slack.com/api/chat.postMessage"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }
    
    # リクエストボディ
    data = {
        "channel": channel,
        "text": text
    }
    
    # スレッドの指定がある場合は追加
    if thread_ts:
        data["thread_ts"] = thread_ts
    
    try:
        # APIリクエスト
        response = requests.post(url, headers=headers, json=data)
        
        # レスポンスのチェック
        response.raise_for_status()
        
        # JSONレスポンスの解析
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"APIリクエストエラー: {str(e)}"}
    except ValueError as e:
        return {"ok": False, "error": f"JSONパースエラー: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": f"予期せぬエラー: {str(e)}"}

def get_thread_messages(
    channel: str,
    thread_ts: str
) -> Dict[str, Any]:
    """
    Slackのスレッドメッセージを取得する関数
    
    引数:
        channel: チャンネルID
        thread_ts: スレッドのタイムスタンプ
    
    戻り値:
        Slackからのレスポンス（messagesキーにスレッドメッセージのリストが含まれる）
    """
    if not SLACK_BOT_TOKEN:
        return {"ok": False, "error": "SLACK_BOT_TOKENが設定されていません"}
    
    # APIエンドポイント
    url = "https://slack.com/api/conversations.replies"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }
    
    # リクエストパラメータ
    params = {
        "channel": channel,
        "ts": thread_ts
    }
    
    try:
        # APIリクエスト
        response = requests.get(url, headers=headers, params=params)
        
        # レスポンスのチェック
        response.raise_for_status()
        
        # JSONレスポンスの解析
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"APIリクエストエラー: {str(e)}"}
    except ValueError as e:
        return {"ok": False, "error": f"JSONパースエラー: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": f"予期せぬエラー: {str(e)}"}
