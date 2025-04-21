import os
from typing import Dict, Any, Optional, List, Tuple
from google import genai

# Gemini APIのAPIキー（環境変数から取得）
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

def generate_imagen_prompt(user_prompt: str) -> Tuple[str, Optional[str]]:
    """
    ユーザーの入力プロンプトを元に、Imagen APIに最適化された画像生成プロンプトを生成する関数
    
    引数:
        user_prompt: ユーザーからの入力プロンプト
    
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

注意事項：
- 日本語のプロンプトを生成してください
- 簡潔かつ具体的に記述してください（200-300文字程度）
- 不適切なコンテンツや過度に暴力的な表現は避けてください
- 著作権で保護されたキャラクターや商標の具体的な名前は避けてください
- プロンプトの前後に余計な説明や注釈を入れないでください
- 最適化されたプロンプトのみを出力してください

ユーザーの入力プロンプト："""
        
        # メッセージの作成
        messages = [
            {
                "role": "user", 
                "parts": [{"text": system_prompt + user_prompt}]
            }
        ]
        
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
