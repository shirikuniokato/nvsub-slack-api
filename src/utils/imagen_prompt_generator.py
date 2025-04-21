import os
from typing import Dict, Any, Optional, List, Tuple
from google import genai
from openai import OpenAI
from utils.ai_provider import get_provider_info

# APIキー（環境変数から取得）
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def generate_imagen_prompt(user_prompt: List[Dict[str, Any]], provider: str = "gemini") -> Tuple[str, Optional[str]]:
    """
    ユーザーの入力プロンプトを元に、画像生成APIに最適化されたプロンプトを生成する関数
    
    引数:
        user_prompt: メッセージ形式のリスト
        provider: 使用するプロバイダー（"gemini", "openai", または "grok"）
    
    戻り値:
        (最適化されたプロンプト, エラーメッセージ) のタプル
        成功時は (最適化されたプロンプト, None)
        失敗時は ("", エラーメッセージ)
    """
    if provider == "openai":
        return generate_imagen_prompt_openai(user_prompt)
    elif provider == "grok":
        return generate_imagen_prompt_grok(user_prompt)
    else:  # デフォルトはGemini
        return generate_imagen_prompt_gemini(user_prompt)

def generate_imagen_prompt_openai(user_prompt: List[Dict[str, Any]]) -> Tuple[str, Optional[str]]:
    """
    ユーザーの入力プロンプトを元に、DALL-E 3に最適化された画像生成プロンプトを生成する関数
    
    引数:
        user_prompt: OpenAI形式のメッセージリスト
    
    戻り値:
        (最適化されたプロンプト, エラーメッセージ) のタプル
        成功時は (最適化されたプロンプト, None)
        失敗時は ("", エラーメッセージ)
    """
    if not OPENAI_API_KEY:
        return "", "OpenAI APIキーが設定されていません。環境変数OPENAI_API_KEYを設定してください。"
    
    try:
        # OpenAIクライアントの初期化
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # プロンプト最適化のためのシステムプロンプト
        system_prompt = """
あなたは画像生成AIのためのプロンプトを最適化する専門家です。
ユーザーの簡潔な入力を、DALL-E 3で高品質な画像を生成するための詳細なプロンプトに変換してください。

以下の要素を含めて、プロンプトを強化してください：
1. 主題の詳細な説明
2. 背景や環境の説明
3. 照明、色調、雰囲気
4. 視点やカメラアングル
5. アートスタイル（写実的、アニメ調、水彩画風など）
6. 画像の品質に関する指定（高解像度、詳細、鮮明さなど）

DALL-E 3 プロンプトの作成に関するヒント:

- 具体的な形容詞や副詞を使用して、明確な画像を描写する
- 必要に応じて背景情報を含める
- 特定のアーティストやスタイルを参照すると効果的
- 人物の表情や姿勢、服装などの詳細を指定する
- 光の当たり方や色調など、雰囲気を表現する言葉を使う
- 「photorealistic」「8K」「detailed」などの品質を表す言葉を含める

注意事項：
- 日本語のプロンプトを生成してください
- 簡潔かつ具体的に記述してください（200-300文字程度）
- プロンプトの前後に余計な説明や注釈を入れないでください
- 最適化されたプロンプトのみを出力してください
"""
        
        # ユーザーメッセージからテキスト部分を抽出
        user_text = ""
        for message in user_prompt:
            if message.get("role") == "user":
                if isinstance(message.get("content"), list):
                    for content in message.get("content", []):
                        if isinstance(content, dict) and content.get("type") == "text":
                            user_text += content.get("text", "") + " "
                elif isinstance(message.get("content"), str):
                    user_text += message.get("content", "") + " "
        
        user_text = user_text.strip()
        if not user_text:
            user_text = "画像を生成してください"
        
        # APIリクエスト用のメッセージを構築
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ]
        
        # プロバイダー情報からモデルを取得
        provider_info = get_provider_info("openai")
        model_name = provider_info.get("default_model", "gpt-3.5-turbo")
        
        # APIの呼び出し
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,  # 創造性と一貫性のバランス
        )
        
        # 応答テキストの取得
        optimized_prompt = response.choices[0].message.content.strip()
        
        print(f"元のプロンプト: {user_text}")
        print(f"DALL-E用に最適化されたプロンプト: {optimized_prompt}")
        
        return optimized_prompt, None
    
    except Exception as e:
        error_msg = f"DALL-E用プロンプト最適化中にエラーが発生しました: {str(e)}"
        print(error_msg)
        return "", error_msg

def generate_imagen_prompt_grok(user_prompt: List[Dict[str, Any]]) -> Tuple[str, Optional[str]]:
    """
    ユーザーの入力プロンプトを元に、Grok画像生成APIに最適化されたプロンプトを生成する関数
    
    引数:
        user_prompt: OpenAI/Grok形式のメッセージリスト
    
    戻り値:
        (最適化されたプロンプト, エラーメッセージ) のタプル
        成功時は (最適化されたプロンプト, None)
        失敗時は ("", エラーメッセージ)
    """
    # Grok APIのエンドポイントとAPIキー（環境変数から取得）
    GROK_API_KEY = os.environ.get("GROK_API_KEY")
    GROK_API_BASE_URL = os.environ.get("GROK_API_BASE_URL", "https://api.x.ai/v1")
    
    if not GROK_API_KEY:
        return "", "Grok APIキーが設定されていません。環境変数GROK_API_KEYを設定してください。"
    
    try:
        # OpenAIクライアントの初期化（Grok APIはOpenAI互換）
        client = OpenAI(
            api_key=GROK_API_KEY,
            base_url=GROK_API_BASE_URL,
        )
        
        # プロンプト最適化のためのシステムプロンプト
        system_prompt = """
あなたは画像生成AIのためのプロンプトを最適化する専門家です。
ユーザーの簡潔な入力を、Grok画像生成APIで高品質な画像を生成するための詳細なプロンプトに変換してください。

以下の要素を含めて、プロンプトを強化してください：
1. 主題の詳細な説明
2. 背景や環境の説明
3. 照明、色調、雰囲気
4. 視点やカメラアングル
5. アートスタイル（写実的、アニメ調、水彩画風など）
6. 画像の品質に関する指定（高解像度、詳細、鮮明さなど）

Grok画像生成プロンプトの作成に関するヒント:

- 具体的な形容詞や副詞を使用して、明確な画像を描写する
- 必要に応じて背景情報を含める
- 特定のアーティストやスタイルを参照すると効果的
- 人物の表情や姿勢、服装などの詳細を指定する
- 光の当たり方や色調など、雰囲気を表現する言葉を使う
- 「photorealistic」「8K」「detailed」などの品質を表す言葉を含める

注意事項：
- 日本語のプロンプトを生成してください
- 簡潔かつ具体的に記述してください（200-300文字程度）
- プロンプトの前後に余計な説明や注釈を入れないでください
- 最適化されたプロンプトのみを出力してください
"""
        
        # ユーザーメッセージからテキスト部分を抽出
        user_text = ""
        for message in user_prompt:
            if message.get("role") == "user":
                if isinstance(message.get("content"), list):
                    for content in message.get("content", []):
                        if isinstance(content, dict) and content.get("type") == "text":
                            user_text += content.get("text", "") + " "
                elif isinstance(message.get("content"), str):
                    user_text += message.get("content", "") + " "
        
        user_text = user_text.strip()
        if not user_text:
            user_text = "画像を生成してください"
        
        # APIリクエスト用のメッセージを構築
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ]
        
        # プロバイダー情報からモデルを取得
        provider_info = get_provider_info("grok")
        model_name = provider_info.get("default_model", "grok-3-latest")
        
        # APIの呼び出し
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,  # 創造性と一貫性のバランス
        )
        
        # 応答テキストの取得
        optimized_prompt = response.choices[0].message.content.strip()
        
        print(f"元のプロンプト: {user_text}")
        print(f"Grok用に最適化されたプロンプト: {optimized_prompt}")
        
        return optimized_prompt, None
    
    except Exception as e:
        error_msg = f"Grok用プロンプト最適化中にエラーが発生しました: {str(e)}"
        print(error_msg)
        return "", error_msg

def generate_imagen_prompt_gemini(user_prompt: List[Dict[str, Any]]) -> Tuple[str, Optional[str]]:
    """
    ユーザーの入力プロンプトを元に、Imagen APIに最適化された画像生成プロンプトを生成する関数
    
    引数:
        user_prompt: gemini_messages 形式のリスト
    
    戻り値:
        (最適化されたプロンプト, エラーメッセージ) のタプル
        成功時は (最適化されたプロンプト, None)
        失敗時は ("", エラーメッセージ)
    """
    if not GOOGLE_API_KEY:
        return "", "Gemini APIキーが設定されていません。環境変数GOOGLE_API_KEYを設定してください。"
    
    try:
        # Geminiクライアントの初期化
        client = genai.Client()
        
        # プロンプト最適化のためのシステムプロンプト
        system_prompt = """
あなたは画像生成AIのためのプロンプトを最適化する専門家です。
ユーザーの簡潔な入力を、Gemini Image 3で高品質な画像を生成するための詳細なプロンプトに変換してください。

以下の要素を含めて、プロンプトを強化してください：
1. 主題の詳細な説明
2. 背景や環境の説明
3. 照明、色調、雰囲気
4. 視点やカメラアングル
5. アートスタイル（写実的、アニメ調、水彩画風など）
6. 画像の品質に関する指定（高解像度、詳細、鮮明さなど）

Imagen 3 プロンプトの作成に関するその他のヒント:

わかりやすい表現を使用する: 具体的な形容詞や副詞を使用して、Imagen 3 の明確な画像を描きます。
コンテキストを提供する: 必要に応じて、AI の理解を助けるために背景情報を含めます。
特定のアーティストやスタイルを参照する: 特定の美学を念頭に置いている場合は、特定のアーティストや芸術運動を参照すると役に立ちます。
プロンプト エンジニアリング ツールを使用する: プロンプトを改良して最適な結果を得るために、プロンプト エンジニアリング ツールやリソースを検討してください。
個人写真やグループ写真の顔の細部を補正する:
写真の焦点として顔の詳細を指定します（たとえば、プロンプトで「ポートレート」という単語を使用します）。

注意事項：
- 日本語のプロンプトを生成してください
- 簡潔かつ具体的に記述してください（200-300文字程度）
- プロンプトの前後に余計な説明や注釈を入れないでください
- 最適化されたプロンプトのみを出力してください

ユーザーの入力プロンプト："""
        
        # システムプロンプトをユーザーメッセージとして追加し、その後にuser_promptを結合
        system_message = {
            "role": "user",
            "parts": [{"text": system_prompt}]
        }
        messages = [system_message] + user_prompt
        
        # プロバイダー情報からモデルを取得
        provider_info = get_provider_info("gemini")
        model_name = provider_info.get("default_model", "gemini-1.5-flash")
        
        # APIの呼び出し
        response = client.models.generate_content(
            model=model_name,
            contents=messages
        )
        
        # 応答テキストの取得
        optimized_prompt = response.text.strip()
        
        print(f"元のプロンプト: {user_prompt}")
        print(f"最適化されたプロンプト: {optimized_prompt}")
        
        return optimized_prompt, None
    
    except Exception as e:
        error_msg = f"プロンプト最適化中にエラーが発生しました: {str(e)}"
        print(error_msg)
        return "", error_msg
