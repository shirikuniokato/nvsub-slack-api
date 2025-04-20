import os
from typing import Dict, Any, Optional, Generator, Callable
from anthropic import Anthropic
from utils.ai_provider import get_provider_info

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

def contains_document(messages: list) -> bool:
    """
    メッセージリストにPDFドキュメントが含まれているかどうかを判定する関数
    
    引数:
        messages: メッセージのリスト
    
    戻り値:
        PDFドキュメントが含まれている場合はTrue、そうでない場合はFalse
    """
    for message in messages:
        if "content" in message and isinstance(message["content"], list):
            for item in message["content"]:
                if item.get("type") == "document":
                    return True
    return False

def convert_to_claude_messages(messages: list) -> list:
    """
    OpenAI形式のメッセージをClaude形式に変換する関数
    
    引数:
        messages: OpenAI形式のメッセージリスト
    
    戻り値:
        Claude形式のメッセージリスト
    """
    claude_messages = []
    
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        
        # システムメッセージの場合
        if role == "system":
            # Claudeではシステムメッセージは特別な形式
            if isinstance(content, list):
                # リスト形式の場合はテキスト部分のみを抽出
                system_content = ""
                for item in content:
                    if item.get("type") == "text":
                        system_content += item.get("text", "")
            else:
                system_content = content
            
            claude_messages.append({
                "role": "assistant",
                "content": system_content
            })
        
        # ユーザーまたはアシスタントのメッセージの場合
        elif role in ["user", "assistant"]:
            # コンテンツがリスト形式の場合
            if isinstance(content, list):
                claude_content = []
                
                for item in content:
                    item_type = item.get("type")
                    
                    # テキストの場合
                    if item_type == "text":
                        claude_content.append({
                            "type": "text",
                            "text": item.get("text", "")
                        })
                    
                    # 画像の場合
                    elif item_type == "image_url":
                        image_url = item.get("image_url", {}).get("url", "")
                        
                        # data:image形式のURLの場合
                        if image_url.startswith("data:"):
                            # MIMEタイプとbase64データを分離
                            mime_type = image_url.split(";")[0].split(":")[1]
                            base64_data = image_url.split(",")[1]
                            
                            claude_content.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": base64_data
                                }
                            })
                        else:
                            # 通常のURLの場合
                            claude_content.append({
                                "type": "image",
                                "source": {
                                    "type": "url",
                                    "url": image_url
                                }
                            })
                    
                    # PDFドキュメントの場合（URL）
                    elif item_type == "document" and item.get("source", {}).get("type") == "url":
                        pdf_url = item.get("source", {}).get("url", "")
                        claude_content.append({
                            "type": "document",
                            "source": {
                                "type": "url",
                                "url": pdf_url
                            }
                        })
                    
                    # PDFドキュメントの場合（Base64）
                    elif item_type == "document" and item.get("source", {}).get("type") == "base64":
                        media_type = item.get("source", {}).get("media_type", "application/pdf")
                        base64_data = item.get("source", {}).get("data", "")
                        claude_content.append({
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_data
                            }
                        })
                
                claude_messages.append({
                    "role": role,
                    "content": claude_content
                })
            
            # コンテンツが文字列の場合
            else:
                claude_messages.append({
                    "role": role,
                    "content": content
                })
    
    return claude_messages

def call_claude_api(
    prompt: str,
    character: Optional[Dict[str, str]] = None,
    conversation_history: Optional[Any] = None
) -> str:
    """
    Claude APIを呼び出して応答を取得する関数
    
    引数:
        prompt: ユーザーからの入力メッセージ
        character: キャラクター設定（任意）
        conversation_history: 会話履歴（任意）- 文字列、リスト、または構造化されたメッセージ
    
    戻り値:
        Claude APIからの応答テキスト
    """
    try:
        # Anthropicクライアントの初期化（環境変数ANTHROPIC_API_KEYから自動的に取得）
        client = Anthropic()
    except Exception as e:
        return f"Claude APIクライアントの初期化に失敗しました: {str(e)}。環境変数ANTHROPIC_API_KEYが設定されているか確認してください。"
    
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
        # 画像またはPDFが含まれているかどうかを判定
        has_image = contains_image(messages)
        has_document = contains_document(messages)
        
        # プロバイダー情報からモデルを取得
        provider_info = get_provider_info("claude")
        default_model = provider_info.get("default_model", "claude-3-opus-20240229")
        vision_model = provider_info.get("vision_model", "claude-3-opus-20240229")
        
        # 使用するモデルを選択（画像またはPDFが含まれている場合はvision_modelを使用）
        model = vision_model if (has_image or has_document) else default_model
        print(f"使用するモデル: {model} (画像あり: {has_image}, PDFあり: {has_document})")
        
        # OpenAI形式のメッセージをClaude形式に変換
        claude_messages = convert_to_claude_messages(messages)
        
        # APIリクエスト
        message = client.messages.create(
            model=model,
            messages=claude_messages,
            temperature=1.0,  # 応答の多様性（0.0〜1.0）
            max_tokens=4096,  # 最大トークン数
        )
        
        # 応答テキストの取得
        return message.content[0].text
    
    except Exception as e:
        return f"Claude APIへのリクエスト中にエラーが発生しました: {str(e)}"

def call_claude_api_streaming(
    prompt: str,
    character: Optional[Dict[str, str]] = None,
    conversation_history: Optional[Any] = None,
    callback: Optional[Callable[[str, bool], None]] = None
) -> Generator[str, None, None]:
    """
    Claude APIをストリーミングモードで呼び出して応答を取得する関数
    
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
    try:
        # Anthropicクライアントの初期化（環境変数ANTHROPIC_API_KEYから自動的に取得）
        client = Anthropic()
    except Exception as e:
        error_msg = f"Claude APIクライアントの初期化に失敗しました: {str(e)}。環境変数ANTHROPIC_API_KEYが設定されているか確認してください。"
        if callback:
            callback(error_msg, True)
        yield error_msg
        return
    
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
        # 画像またはPDFが含まれているかどうかを判定
        has_image = contains_image(messages)
        has_document = contains_document(messages)
        
        # プロバイダー情報からモデルを取得
        provider_info = get_provider_info("claude")
        default_model = provider_info.get("default_model", "claude-3-opus-20240229")
        vision_model = provider_info.get("vision_model", "claude-3-opus-20240229")
        
        # 使用するモデルを選択（画像またはPDFが含まれている場合はvision_modelを使用）
        model = vision_model if (has_image or has_document) else default_model
        print(f"使用するモデル: {model} (画像あり: {has_image}, PDFあり: {has_document})")
        
        # OpenAI形式のメッセージをClaude形式に変換
        claude_messages = convert_to_claude_messages(messages)
        
        # ストリーミングモードでAPIリクエスト
        with client.messages.stream(
            model=model,
            messages=claude_messages,
            temperature=1.0,  # 応答の多様性（0.0〜1.0）
            max_tokens=4096,  # 最大トークン数
        ) as stream:
            # 応答を逐次処理
            for text in stream.text_stream:
                if callback:
                    # 完了フラグはFalse（まだストリーミング中）
                    callback(text, False)
                yield text
            
            # ストリーミング完了を通知
            if callback:
                callback("", True)
    
    except Exception as e:
        error_msg = f"Claude APIへのリクエスト中にエラーが発生しました: {str(e)}"
        if callback:
            callback(error_msg, True)
        yield error_msg
