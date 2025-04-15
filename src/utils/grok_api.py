import os
from typing import Dict, Any, Optional
from openai import OpenAI

# Grok APIのエンドポイントとAPIキー（環境変数から取得）
GROK_API_KEY = os.environ.get("GROK_API_KEY")
GROK_API_BASE_URL = os.environ.get("GROK_API_BASE_URL", "https://api.x.ai/v1")
GROK_API_MODEL = os.environ.get("GROK_API_MODEL", "grok-3-latest")

def call_grok_api(
    prompt: str,
    character: Optional[Dict[str, str]] = None,
    conversation_history: Optional[str] = None
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
    
    # OpenAIクライアントの初期化
    client = OpenAI(
        api_key=GROK_API_KEY,
        base_url=GROK_API_BASE_URL,
    )
    
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
        if isinstance(conversation_history, list):
            messages.extend(conversation_history)
        else:
            # 文字列の場合はシステムメッセージとして追加
            messages.append({"role": "system", "content": conversation_history})
    
    # ユーザーのメッセージを追加
    messages.append({"role": "user", "content": prompt})
    
    try:
        # APIリクエスト
        completion = client.chat.completions.create(
            model=GROK_API_MODEL,
            messages=messages,
            temperature=0.7,  # 応答の多様性（0.0〜1.0）
        )
        
        # 応答テキストの取得
        return completion.choices[0].message.content
    
    except Exception as e:
        return f"Grok APIへのリクエスト中にエラーが発生しました: {str(e)}"
