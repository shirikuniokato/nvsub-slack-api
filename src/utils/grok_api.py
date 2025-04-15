import os
import requests
from typing import Dict, Any, Optional

# Grok APIのエンドポイントとAPIキー（環境変数から取得）
GROK_API_ENDPOINT = os.environ.get("GROK_API_ENDPOINT", "https://api.x.ai/v1/chat/completions")
GROK_API_KEY = os.environ.get("GROK_API_KEY")

def call_grok_api(
    prompt: str,
    character: Optional[Dict[str, str]] = None,
    conversation_history: Optional[list] = None
) -> str:
    """
    Grok APIを呼び出して応答を取得する関数
    
    引数:
        prompt: ユーザーからの入力メッセージ
        character: キャラクター設定（任意）
        conversation_history: 会話履歴（任意）
    
    戻り値:
        Grok APIからの応答テキスト
    """
    if not GROK_API_KEY:
        return "Grok APIキーが設定されていません。環境変数GROK_API_KEYを設定してください。"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}"
    }
    
    # システムメッセージの作成（キャラクター設定がある場合）
    system_message = ""
    if character:
        system_message = f"""あなたは{character['name']}というキャラクターです。
性格: {character['personality']}
話し方: {character['speaking_style']}

以下の質問に対して、{character['name']}として回答してください。
"""
    
    # メッセージの作成
    messages = []
    
    # システムメッセージがある場合は追加
    if system_message:
        messages.append({"role": "system", "content": system_message})
    
    # 会話履歴がある場合は追加
    if conversation_history:
        messages.extend(conversation_history)
    
    # ユーザーのメッセージを追加
    messages.append({"role": "user", "content": prompt})
    
    # リクエストボディ
    data = {
        "model": "grok-3-latest",  # Grokのモデル名
        "stream": False,
        "messages": messages,
        "temperature": 0,  # 応答の多様性（0.0〜1.0）
    }
    
    try:
        # APIリクエスト
        response = requests.post(GROK_API_ENDPOINT, headers=headers, json=data)
        
        # レスポンスのチェック
        response.raise_for_status()
        
        # JSONレスポンスの解析
        result = response.json()
        
        # 応答テキストの取得
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "Grok APIからの応答を解析できませんでした。"
    
    except requests.exceptions.RequestException as e:
        return f"Grok APIへのリクエスト中にエラーが発生しました: {str(e)}"
    except ValueError as e:
        return f"Grok APIからのレスポンスの解析中にエラーが発生しました: {str(e)}"
    except Exception as e:
        return f"予期せぬエラーが発生しました: {str(e)}"
