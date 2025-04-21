import os
import base64
from typing import Dict, Any, Optional, Generator, Callable, List, Tuple, Union
from io import BytesIO
from PIL import Image
from openai import OpenAI
from utils.ai_provider import get_provider_info
from utils.imagen_prompt_generator import generate_imagen_prompt

# Grok APIのエンドポイントとAPIキー（環境変数から取得）
GROK_API_KEY = os.environ.get("GROK_API_KEY")
GROK_API_BASE_URL = os.environ.get("GROK_API_BASE_URL", "https://api.x.ai/v1")

def generate_image_with_grok(prompt: List[Dict[str, Any]], number_of_images: int = 1) -> Tuple[Optional[List[Image.Image]], Optional[str]]:
    """
    Grok APIを使用して画像を生成する関数
    
    引数:
        prompt: 画像生成のためのメッセージ形式のリスト
        number_of_images: 生成する画像の数（デフォルト: 1）
    
    戻り値:
        (生成された画像オブジェクトのリスト, エラーメッセージ) のタプル
        成功時は ([画像オブジェクト1, 画像オブジェクト2, ...], None)
        失敗時は (None, エラーメッセージ)
    """
    if not GROK_API_KEY:
        return None, "Grok APIキーが設定されていません。環境変数GROK_API_KEYを設定してください。"
    
    try:
        # プロンプトを最適化（Grok用）
        optimized_prompt, error = generate_imagen_prompt(prompt, provider="grok")
        if error:
            print(f"プロンプト最適化エラー: {error}")
            print("最適化に失敗したため、最後のユーザーメッセージを使用します")
            # 最後のユーザーメッセージのテキスト部分を取得
            user_text = ""
            for message in prompt:
                if message.get("role") == "user":
                    for part in message.get("parts", []):
                        if "text" in part:
                            user_text += part["text"] + " "
            
            optimized_prompt = user_text.strip()
            if not optimized_prompt:
                optimized_prompt = "画像を生成してください"
        else:
            print(f"プロンプトを最適化しました")
            print(f"元のプロンプト: {prompt}")
            print(f"最適化されたプロンプト: {optimized_prompt}")
        
        # OpenAIクライアントの初期化（Grok APIはOpenAI互換）
        client = OpenAI(
            api_key=GROK_API_KEY,
            base_url=GROK_API_BASE_URL,
        )
        
        # プロバイダー情報から画像生成モデルを取得
        provider_info = get_provider_info("grok")
        image_model = provider_info.get("image_model", "grok-image-latest")
        
        # モデルが設定されていない場合はデフォルトを使用
        if not image_model:
            image_model = "grok-image-latest"
            print(f"画像生成モデルが設定されていないため、デフォルトを使用します: {image_model}")
        else:
            print(f"使用する画像生成モデル: {image_model}")
        
        # 画像生成リクエスト
        response = client.images.generate(
            model=image_model,
            prompt=optimized_prompt,
            n=number_of_images,
            # size="1024x1024",  # デフォルトサイズ
            # quality="standard",
            response_format="b64_json"  # Base64形式で画像を取得
        )
        
        # 応答から画像を取得
        if response.data:
            # 画像オブジェクトのリストを作成
            images = []
            for data in response.data:
                # Base64データからPIL Imageオブジェクトを作成
                image_data = data.b64_json
                image = Image.open(BytesIO(base64.b64decode(image_data)))
                images.append(image)
            
            return images, None
        else:
            return None, "画像が生成されませんでした。"
    
    except Exception as e:
        error_msg = f"Grok APIによる画像生成中にエラーが発生しました: {str(e)}"
        print(error_msg)
        return None, error_msg

def should_generate_image(prompt: str) -> bool:
    """
    メッセージが画像生成を要求しているかどうかを判定する関数
    
    引数:
        prompt: ユーザーからの入力メッセージ
    
    戻り値:
        画像生成を要求している場合はTrue、そうでない場合はFalse
    """
    if not GROK_API_KEY:
        print("Grok APIキーが設定されていないため、画像生成判定ができません")
        return False
    
    try:
        # OpenAIクライアントの初期化（Grok APIはOpenAI互換）
        client = OpenAI(
            api_key=GROK_API_KEY,
            base_url=GROK_API_BASE_URL,
        )
        
        # 判定用のプロンプト
        instruction = """
あなたはユーザーのメッセージが画像生成を要求しているかどうかを判定するシステムです。
以下のルールに従って判定してください：

1. ユーザーが明示的に「画像を生成して」「イラストを作って」「絵を描いて」などと依頼している場合は画像生成要求です
2. ユーザーが「〜の画像」「〜のイラスト」「〜の絵」などを求めている場合は画像生成要求です
3. ユーザーが「想像して」「ビジュアライズして」などと視覚的な表現を求めている場合も画像生成要求です
4. 単なる質問や情報提供の依頼は画像生成要求ではありません

判定結果は「YES」または「NO」のみで回答してください。
「YES」= 画像生成要求である
「NO」 = 画像生成要求ではない

以下のメッセージを判定してください: """ + prompt
        
        # 判定用のメッセージ
        messages = [
            {
                "role": "user",
                "content": instruction
            }
        ]
        
        # プロバイダー情報からモデルを取得
        provider_info = get_provider_info("grok")
        default_model = provider_info.get("default_model", "grok-3-latest")
        
        # APIの呼び出し
        response = client.chat.completions.create(
            model=default_model,
            messages=messages,
            temperature=0.0  # 決定論的な応答を得るために低い温度を設定
        )
        
        # 応答テキストの取得と判定
        result = response.choices[0].message.content.strip().upper()
        
        # 「YES」または「Y」が含まれている場合は画像生成要求と判定
        is_image_request = "YES" in result or result == "Y"
        
        print(f"画像生成判定: {prompt} -> {result} -> {is_image_request}")
        
        return is_image_request
    
    except Exception as e:
        print(f"画像生成判定エラー: {str(e)}")
        return False

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
    conversation_history: Optional[Any] = None,
    generate_image: bool = False
) -> Union[str, Tuple[str, Optional[Image.Image]]]:
    """
    Grok APIを呼び出して応答を取得する関数
    
    引数:
        prompt: ユーザーからの入力メッセージ
        character: キャラクター設定（任意）
        conversation_history: 会話履歴（任意）- 文字列、リスト、または構造化されたメッセージ
        generate_image: 画像生成モードを有効にするかどうか（デフォルト: False）
    
    戻り値:
        generate_image=False の場合: Grok APIからの応答テキスト
        generate_image=True の場合: (応答テキスト, 生成された画像) のタプル
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
        # 画像生成モードが有効な場合
        if generate_image:
            print("Grok APIを使用して画像を生成します")
            
            # Grok APIを使用して画像を生成（1枚のみ）
            images, error = generate_image_with_grok(messages, number_of_images=1)
            
            if error:
                return f"画像生成エラー: {error}"
            
            # 画像が生成されたか確認
            if not images or len(images) == 0:
                return "画像を生成できませんでした。", None
            
            # 最初の画像を取得
            image = images[0]
            
            # テキスト応答を生成
            # 画像が含まれているかどうかを判定
            has_image = contains_image(messages)
            
            # プロバイダー情報からモデルを取得
            provider_info = get_provider_info("grok")
            default_model = provider_info.get("default_model", "grok-3-latest")
            vision_model = provider_info.get("vision_model", "grok-2-vision-latest")
            
            # 使用するモデルを選択
            model = vision_model if has_image else default_model
            print(f"テキスト応答用モデル: {model}")
            
            # APIリクエスト
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=1.0,  # 応答の多様性（0.0〜1.0）
            )
            
            # 応答テキストの取得
            generated_text = completion.choices[0].message.content
            
            return generated_text, image
        else:
            # 通常のテキスト生成モード
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
