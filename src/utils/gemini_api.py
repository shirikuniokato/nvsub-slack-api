import os
from typing import Dict, Any, Optional, Generator, Callable, List
from google import genai
from utils.ai_provider import get_provider_info

# Gemini APIのAPIキー（環境変数から取得）
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")


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

def convert_messages_to_gemini_format(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    OpenAI形式のメッセージをGemini形式に変換する関数
    
    引数:
        messages: OpenAI形式のメッセージリスト
    
    戻り値:
        Gemini形式のメッセージリスト
    """
    gemini_messages = []
    
    for message in messages:
        role = message.get("role")
        content = message.get("content", [])
        
        # roleの変換（systemはGeminiではmodelとして扱う）
        gemini_role = "user" if role == "user" else "model"
        
        # contentの変換
        gemini_parts = []
        
        if isinstance(content, str):
            # 文字列の場合は単純にテキストとして追加
            gemini_parts.append({"text": content})
        elif isinstance(content, list):
            # リストの場合は各アイテムを変換
            for item in content:
                if isinstance(item, str):
                    gemini_parts.append({"text": item})
                elif isinstance(item, dict):
                    if item.get("type") == "text":
                        gemini_parts.append({"text": item.get("text", "")})
                    elif item.get("type") == "image_url":
                        image_url = item.get("image_url", {}).get("url", "")
                        if image_url.startswith("data:"):
                            # Base64エンコードされた画像
                            mime_type = image_url.split(";")[0].split(":")[1]
                            base64_data = image_url.split(",")[1]
                            gemini_parts.append({
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": base64_data
                                }
                            })
                        else:
                            # 通常のURL
                            gemini_parts.append({
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": image_url
                                }
                            })
        
        # メッセージを追加
        if gemini_parts:
            gemini_messages.append({
                "role": gemini_role,
                "parts": gemini_parts
            })
    
    return gemini_messages

def call_gemini_api(
    prompt: str,
    character: Optional[Dict[str, str]] = None,
    conversation_history: Optional[Any] = None
) -> str:
    """
    Gemini APIを呼び出して応答を取得する関数
    
    引数:
        prompt: ユーザーからの入力メッセージ
        character: キャラクター設定（任意）
        conversation_history: 会話履歴（任意）- 文字列、リスト、または構造化されたメッセージ
    
    戻り値:
        Gemini APIからの応答テキスト
    """
    if not GOOGLE_API_KEY:
        return "Gemini APIキーが設定されていません。環境変数GOOGLE_API_KEYを設定してください。"
    
    # Geminiクライアントの初期化
    client = genai.Client()
    # メッセージの作成（OpenAI形式）
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
        provider_info = get_provider_info("gemini")
        default_model = provider_info.get("default_model", "gemini-2.0-flash")
        vision_model = provider_info.get("vision_model", "gemini-2.0-flash-vision")
        
        # 使用するモデルを選択
        model_name = vision_model if has_image else default_model
        print(f"使用するモデル: {model_name} (画像あり: {has_image})")
        
        # Gemini形式にメッセージを変換
        gemini_messages = convert_messages_to_gemini_format(messages)
        
        # 新しいAPIの呼び出し方法
        response = client.models.generate_content(
            model=model_name,
            contents=gemini_messages
        )
        
        # 応答テキストの取得
        return response.text
    
    except Exception as e:
        return f"Gemini APIへのリクエスト中にエラーが発生しました: {str(e)}"

def call_gemini_api_streaming(
    prompt: str,
    character: Optional[Dict[str, str]] = None,
    conversation_history: Optional[Any] = None,
    callback: Optional[Callable[[str, bool], None]] = None
) -> Generator[str, None, None]:
    """
    Gemini APIをストリーミングモードで呼び出して応答を取得する関数
    
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
    if not GOOGLE_API_KEY:
        error_msg = "Gemini APIキーが設定されていません。環境変数GOOGLE_API_KEYを設定してください。"
        if callback:
            callback(error_msg, True)
        yield error_msg
        return
    
    # Geminiクライアントの初期化
    client = genai.Client()
    
    # メッセージの作成（OpenAI形式）
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
        provider_info = get_provider_info("gemini")
        default_model = provider_info.get("default_model", "gemini-2.0-flash")
        vision_model = provider_info.get("vision_model", "gemini-2.0-flash-vision")
        
        # 使用するモデルを選択
        model_name = vision_model if has_image else default_model
        print(f"使用するモデル: {model_name} (画像あり: {has_image})")
        
        # Gemini形式にメッセージを変換
        gemini_messages = convert_messages_to_gemini_format(messages)
        
        # 新しいAPIの呼び出し方法（ストリーミング）
        response = client.models.generate_content_stream(
            model=model_name,
            contents=gemini_messages
        )
        
        # 応答を逐次処理
        for chunk in response:
            if hasattr(chunk, 'text') and chunk.text:
                content = chunk.text
                if callback:
                    # 完了フラグはFalse（まだストリーミング中）
                    callback(content, False)
                yield content
        
        # ストリーミング完了を通知
        if callback:
            callback("", True)
    
    except Exception as e:
        error_msg = f"Gemini APIへのリクエスト中にエラーが発生しました: {str(e)}"
        if callback:
            callback(error_msg, True)
        yield error_msg
