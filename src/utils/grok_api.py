import os
from typing import Dict, Any, Optional, Generator, Callable
from openai import OpenAI
from utils.ai_provider import get_provider_info

# Grok APIのエンドポイントとAPIキー（環境変数から取得）
GROK_API_KEY = os.environ.get("GROK_API_KEY")
GROK_API_BASE_URL = os.environ.get("GROK_API_BASE_URL", "https://api.x.ai/v1")

def contains_image(messages: list) -> bool:
    """
    メッセージリストに画像が含まれているかどうかを判定する関数
    
    引数:
        messages: メッセージのリスト
    
    戻り値:
        画像が含まれている場合はTrue、そうでない場合はFalse
    """
    for message in messages:
        if "content" in message and isinstance(message["content"], list):
            for item in message["content"]:
                if item.get("type") == "image_url":
                    return True
    return False

def call_grok_api(
    prompt: str,
    character: Optional[Dict[str, str]] = None,
    conversation_history: Optional[Any] = None
) -> str:
    """
    Grok APIを呼び出して応答を取得する関数
    
    引数:
        prompt: ユーザーからの入力メッセージ
        character: キャラクター設定（任意）
        conversation_history: 会話履歴（任意）- 文字列、リスト、または構造化されたメッセージ
    
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
    
    # メッセージの作成
    messages = []
    
    # キャラクター設定がある場合はシステムメッセージを作成
    if character:
        system_content = f"""あなたは{character['name']}というキャラクターです。
性格: {character['personality']}
話し方: {character['speaking_style']}

以下の質問に対して、{character['name']}として回答してください。
"""
        messages.append({
            "role": "system", 
            "content": [{"type": "text", "text": system_content}]
        })
    
    # 会話履歴がある場合は追加
    if conversation_history:
        # 既に構造化されたメッセージリストの場合
        if isinstance(conversation_history, list) and all(isinstance(msg, dict) and "role" in msg for msg in conversation_history):
            messages.extend(conversation_history)
        # 文字列の場合はシステムメッセージとして追加
        elif isinstance(conversation_history, str):
            messages.append({
                "role": "system", 
                "content": [{"type": "text", "text": conversation_history}]
            })
    
    # ユーザーのメッセージを追加
    if isinstance(prompt, dict) and "role" in prompt:
        # 既に構造化されたメッセージの場合
        messages.append(prompt)
    else:
        # 文字列の場合は構造化
        messages.append({
            "role": "user", 
            "content": [{"type": "text", "text": prompt}]
        })
    
    try:
        # 画像が含まれているかどうかを判定
        has_image = contains_image(messages)
        
        # プロバイダー情報からモデルを取得
        provider_info = get_provider_info("grok")
        default_model = provider_info.get("default_model", "grok-3-latest")
        vision_model = provider_info.get("vision_model", "grok-2-vision-latest")
        
        # 使用するモデルを選択
        model = vision_model if has_image else default_model
        print(f"使用するモデル: {model} (画像あり: {has_image})")
        
        # APIリクエスト
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=1.0,  # 応答の多様性（0.0〜1.0）
        )
        
        # 応答テキストの取得
        return completion.choices[0].message.content
    
    except Exception as e:
        return f"Grok APIへのリクエスト中にエラーが発生しました: {str(e)}"

def call_grok_api_streaming(
    prompt: str,
    character: Optional[Dict[str, str]] = None,
    conversation_history: Optional[Any] = None,
    callback: Optional[Callable[[str, bool], None]] = None
) -> Generator[str, None, None]:
    """
    Grok APIをストリーミングモードで呼び出して応答を取得する関数
    
    引数:
        prompt: ユーザーからの入力メッセージ
        character: キャラクター設定（任意）
        conversation_history: 会話履歴（任意）- 文字列、リスト、または構造化されたメッセージ
        callback: 各チャンクを受け取るコールバック関数（任意）
            - 引数1: チャンクのテキスト
            - 引数2: 完了フラグ（最後のチャンクの場合はTrue）
    
    戻り値:
        応答チャンクのジェネレーター
    """
    if not GROK_API_KEY:
        error_msg = "Grok APIキーが設定されていません。環境変数GROK_API_KEYを設定してください。"
        if callback:
            callback(error_msg, True)
        yield error_msg
        return
    
    # OpenAIクライアントの初期化
    client = OpenAI(
        api_key=GROK_API_KEY,
        base_url=GROK_API_BASE_URL,
    )
    
    # メッセージの作成
    messages = []
    
    # キャラクター設定がある場合はシステムメッセージを作成
    if character:
        system_content = f"""あなたは{character['name']}というキャラクターです。
性格: {character['personality']}
話し方: {character['speaking_style']}

以下の質問に対して、{character['name']}として回答してください。
"""
        messages.append({
            "role": "system", 
            "content": [{"type": "text", "text": system_content}]
        })
    
    # 会話履歴がある場合は追加
    if conversation_history:
        # 既に構造化されたメッセージリストの場合
        if isinstance(conversation_history, list) and all(isinstance(msg, dict) and "role" in msg for msg in conversation_history):
            messages.extend(conversation_history)
        # 文字列の場合はシステムメッセージとして追加
        elif isinstance(conversation_history, str):
            messages.append({
                "role": "system", 
                "content": [{"type": "text", "text": conversation_history}]
            })
    
    # ユーザーのメッセージを追加
    if isinstance(prompt, dict) and "role" in prompt:
        # 既に構造化されたメッセージの場合
        messages.append(prompt)
    else:
        # 文字列の場合は構造化
        messages.append({
            "role": "user", 
            "content": [{"type": "text", "text": prompt}]
        })
    
    try:
        # 画像が含まれているかどうかを判定
        has_image = contains_image(messages)
        
        # プロバイダー情報からモデルを取得
        provider_info = get_provider_info("grok")
        default_model = provider_info.get("default_model", "grok-3-latest")
        vision_model = provider_info.get("vision_model", "grok-2-vision-latest")
        
        # 使用するモデルを選択
        model = vision_model if has_image else default_model
        print(f"使用するモデル: {model} (画像あり: {has_image})")
        
        # ストリーミングモードでAPIリクエスト
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=1.0,  # 応答の多様性（0.0〜1.0）
            stream=True,  # ストリーミングモードを有効化
        )
        
        # 応答を逐次処理
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                if callback:
                    # 完了フラグはFalse（まだストリーミング中）
                    callback(content, False)
                yield content
        
        # ストリーミング完了を通知
        if callback:
            callback("", True)
    
    except Exception as e:
        error_msg = f"Grok APIへのリクエスト中にエラーが発生しました: {str(e)}"
        if callback:
            callback(error_msg, True)
        yield error_msg
