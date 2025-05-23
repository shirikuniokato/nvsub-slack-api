import os
import base64
from io import BytesIO
from typing import Dict, Any, Optional, Generator, Callable, List, Tuple, Union, Literal
from PIL import Image
from google import genai
from google.genai import types
from utils.ai_provider import get_provider_info
from utils.imagen_prompt_generator import generate_imagen_prompt

# Gemini APIのAPIキー（環境変数から取得）
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

def generate_image(prompt: Union[str, List[Dict[str, Any]]], number_of_images: int = 1, model_name: str = "imagen-3.0-generate-002") -> Tuple[Optional[Union[Image.Image, List[Image.Image]]], Optional[str]]:
    """
    画像を生成する関数
    
    引数:
        prompt: 画像生成のためのプロンプト（文字列またはGeminiメッセージ形式のリスト）
        number_of_images: 生成する画像の数（デフォルト: 1）
        model_name: 使用する画像生成モデル名（デフォルト: "imagen-3.0-generate-002"）
    
    戻り値:
        (生成された画像オブジェクト(単体または複数), エラーメッセージ) のタプル
        成功時は (画像オブジェクト, None) または ([画像オブジェクト1, 画像オブジェクト2, ...], None)
        失敗時は (None, エラーメッセージ)
    """
    if not GOOGLE_API_KEY:
        return None, "Gemini APIキーが設定されていません。環境変数GOOGLE_API_KEYを設定してください。"
    
    try:
        # Geminiクライアントの初期化
        client = genai.Client()
        
        # 使用するモデル名を表示
        print(f"使用する画像生成モデル: {model_name}")
        
        # プロンプトの準備
        # 文字列の場合はそのまま使用
        if isinstance(prompt, str):
            text_prompt = prompt
            # プロンプトを最適化（Gemini用）
            optimized_prompt, error = generate_imagen_prompt([{"role": "user", "parts": [{"text": text_prompt}]}], provider="gemini")
            if error:
                print(f"プロンプト最適化エラー: {error}")
                optimized_prompt = text_prompt
            else:
                print(f"プロンプトを最適化しました")
                print(f"元のプロンプト: {text_prompt}")
                print(f"最適化されたプロンプト: {optimized_prompt}")
        else:
            # プロンプトを最適化（Gemini用）
            optimized_prompt, error = generate_imagen_prompt(prompt, provider="gemini")
            if error:
                print(f"プロンプト最適化エラー: {error}")
                print("最適化に失敗したため、最後のユーザーメッセージを使用します")
                # 最後のユーザーメッセージのテキスト部分を取得
                text_prompt = ""
                for message in prompt:
                    if message.get("role") == "user":
                        for part in message.get("parts", []):
                            if "text" in part:
                                text_prompt += part["text"] + " "
                
                optimized_prompt = text_prompt.strip()
                if not optimized_prompt:
                    optimized_prompt = "画像を生成してください"
            else:
                print(f"プロンプトを最適化しました")
                print(f"元のプロンプト: {prompt}")
                print(f"最適化されたプロンプト: {optimized_prompt}")
                text_prompt = optimized_prompt
        
        # モデル名に基づいて適切なメソッドを選択
        if model_name == "gemini-2.0-flash-exp-image-generation":
            # gemini-2.0-flash-exp-image-generation モデルの場合は generate_content を使用
            
            # 画像生成リクエスト
            response = client.models.generate_content(
                model=model_name,
                contents=text_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE']
                )
            )
            
            # 応答から画像を取得
            print(response.candidates[0].content)
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    print(part.text)
                elif part.inline_data is not None:
                    # バイトデータからPIL Imageオブジェクトを作成
                    image = Image.open(BytesIO(part.inline_data.data))
                    return image, None
            
            return None, "画像が生成されませんでした。"
        else:
            # その他のモデル（imagen-3.0-generate-002など）の場合は generate_images を使用
            
            # 画像生成の設定
            config = types.GenerateImagesConfig(
                number_of_images=number_of_images,
                # 必要に応じて追加パラメータを設定
                # aspect_ratio="1:1",
                # resolution="1024x1024"
            )
            
            # 画像生成リクエスト
            response = client.models.generate_images(
                model=model_name,
                prompt=optimized_prompt,
                config=config
            )
            
            # 応答から画像を取得
            if response.generated_images:
                # 画像オブジェクトのリストを作成
                images = []
                for generated_image in response.generated_images:
                    # バイトデータからPIL Imageオブジェクトを作成
                    image = Image.open(BytesIO(generated_image.image.image_bytes))
                    images.append(image)
                
                return images, None
            else:
                return None, "画像が生成されませんでした。"
    
    except Exception as e:
        error_msg = f"画像生成中にエラーが発生しました: {str(e)}"
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
    if not GOOGLE_API_KEY:
        print("Gemini APIキーが設定されていないため、画像生成判定ができません")
        return False
    
    try:
        # 軽量なGeminiモデルを使用
        client = genai.Client()
        
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
        
        # 判定用のメッセージ（システムロールを使わない）
        messages = [
            {
                "role": "user",
                "parts": [{"text": instruction}]
            }
        ]
        
        # 軽量モデルを使用
        model_name = "gemini-1.5-flash"
        
        # APIの呼び出し
        response = client.models.generate_content(
            model=model_name,
            contents=messages
        )
        
        # 応答テキストの取得と判定
        result = response.text.strip().upper()
        
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

def convert_messages_to_gemini_format(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    OpenAI形式のメッセージをGemini形式に変換する関数
    
    引数:
        messages: OpenAI形式のメッセージリスト
    
    戻り値:
        Gemini形式のメッセージリスト（role:systemは除外）
    """
    gemini_messages = []
    
    for message in messages:
        role = message.get("role")
        content = message.get("content", [])
        
        # roleの変換
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
    conversation_history: Optional[Any] = None,
    should_generate_image: bool = False,
    image_model: str = "imagen"
) -> Union[str, Tuple[str, Optional[Image.Image]]]:
    """
    Gemini APIを呼び出して応答を取得する関数
    
    引数:
        prompt: ユーザーからの入力メッセージ
        character: キャラクター設定（任意）
        conversation_history: 会話履歴（任意）- 文字列、リスト、または構造化されたメッセージ
        should_generate_image: 画像生成モードを有効にするかどうか（デフォルト: False）
        image_model: 使用する画像生成モデル（"imagen" または "gemini_native"）（デフォルト: "imagen"）
    
    戻り値:
        should_generate_image=False の場合: Gemini APIからの応答テキスト
        should_generate_image=True の場合: (応答テキスト, 生成された画像) のタプル
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
        
        # 画像生成モードが有効な場合
        if should_generate_image:
            # 使用するモデルを決定
            if image_model == "gemini_native":
                model_name = "gemini-2.0-flash-exp-image-generation"
                print(f"Gemini Native Image Generation APIを使用して画像を生成します: {model_name}")
            else:
                # プロバイダー情報からモデルを取得
                provider_info = get_provider_info("gemini")
                model_name = provider_info.get("image_model", "imagen-3.0-generate-002")
                
                # モデルが設定されていない場合はデフォルトを使用
                if not model_name:
                    model_name = "imagen-3.0-generate-002"
                
                print(f"Imagen APIを使用して画像を生成します: {model_name}")
            
            # プロンプトの準備
            if isinstance(prompt, dict) and "role" in prompt:
                # Gemini形式にメッセージを変換（role:systemは除外される）
                gemini_messages = convert_messages_to_gemini_format(messages)
                result, error = generate_image(gemini_messages, number_of_images=1, model_name=model_name)
            else:
                # 文字列の場合はそのまま使用
                result, error = generate_image(prompt, number_of_images=1, model_name=model_name)
            
            if error:
                return f"画像生成エラー: {error}"
            
            # 画像が生成されたか確認
            if not result:
                return "画像を生成できませんでした。", None
            
            # 結果が単一の画像かリストかを判断
            if isinstance(result, list):
                # リストの場合は最初の画像を取得
                image = result[0]
            else:
                # 単一の画像の場合はそのまま使用
                image = result
            
            # テキスト応答を生成
            # 通常のテキスト生成モード
            model_name = vision_model if has_image else default_model
            print(f"テキスト応答用モデル: {model_name}")
            
            # Gemini形式にメッセージを変換
            gemini_messages = convert_messages_to_gemini_format(messages)
            
            # APIの呼び出し
            response = client.models.generate_content(
                model=model_name,
                contents=gemini_messages
            )
            
            # 応答テキストの取得
            generated_text = response.text
            
            return generated_text, image
        else:
            # 通常のテキスト生成モード
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
