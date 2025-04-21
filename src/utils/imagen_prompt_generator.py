import os
from typing import Dict, Any, Optional, List, Tuple
from google import genai

# Gemini APIのAPIキー（環境変数から取得）
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

def generate_imagen_prompt(user_prompt: List[Dict[str, Any]]) -> Tuple[str, Optional[str]]:
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
ユーザーの簡潔な入力を、Imagen APIで高品質な画像を生成するための詳細なプロンプトに変換してください。

以下の要素を含めて、プロンプトを強化してください：
1. 主題の詳細な説明（人物、物体、風景など）
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
        
        # モデルの選択（軽量なモデルを使用）
        model_name = "gemini-1.5-flash"
        
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
