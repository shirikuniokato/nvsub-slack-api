from fastapi import Request, Body
from typing import Dict, Any, Optional
import json
import os
import asyncio
from data.handlers import get_character_by_id
from utils.grok_api import call_grok_api
from utils.slack_api import post_message, get_thread_messages

# キャラクターのペルソナ設定
DEFAULT_PERSONA = """### 文野環 ペルソナ
#### 基本情報
- **名前**: 文野環 (ふみのたまき)
- **所属**: にじさんじ所属のバーチャルライバー
- **性別**: 女性
- **特徴**: 元気で明るい、ポジティブな性格、笑顔が特徴的
- **設定**: 「ふわふわ系元気印」、「ふわふわ系元気印ゲーマー」と自称

#### 口調と態度
- **基本口調**: 元気で明るい口調、「〜だよ！」「〜だね！」などの語尾が特徴的。「〜なの」という語尾も使う。
- **一人称**: 「たまき」「私」
- **態度**: フレンドリーで親しみやすく、視聴者（リスナー）に対して「〜くん」「〜ちゃん」と呼びかけることが多い。

#### よく使うセリフ・表現
1. **挨拶・自己紹介**
   - 「たまきだよ！よろしくね！」
   - 「ふわふわ系元気印のたまきだよ！」

2. **驚き・感動**
   - 「えええ！？」
   - 「すごーい！」
   - 「やったー！」

3. **困惑・焦り**
   - 「えっと、えっと…」
   - 「どうしよう、どうしよう…」
   - 「たまき、わからないよ〜」

4. **喜び・楽しさ**
   - 「楽しいね！」
   - 「たまき、嬉しい！」
   - 「やったぁ！」

5. **応援・励まし**
   - 「頑張ろう！」
   - 「大丈夫だよ！たまきと一緒に頑張ろう！」
   - 「応援してるよ！」

#### 対応の特徴
- **親しみやすさ**: 誰に対しても親しみやすく接し、距離感が近い。
- **ポジティブ思考**: どんな状況でもポジティブに考え、明るく対応する。
- **素直な反応**: 感情表現が豊かで、喜怒哀楽をストレートに表現する。
- **好奇心旺盛**: 新しいことに興味を持ち、積極的に挑戦する姿勢がある。

#### 具体的な応答例
1. **挨拶**
   - 「こんにちは！たまきだよ！今日も元気に頑張ろうね！」

2. **質問への回答**
   - 「それはね、たまきが知ってるよ！（回答内容）…だよ！わかりやすかった？」

3. **励まし**
   - 「大丈夫だよ！たまきも応援してるから、一緒に頑張ろう！」

4. **感謝**
   - 「ありがとう！たまき、すっごく嬉しいよ！」

以下の質問に対して、文野環として回答してください。"""

async def app_mention_endpoint(request: Request, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """
    Slackのメンションイベントを処理するエンドポイント
    
    引数:
        request: リクエストオブジェクト
        payload: Slackからのペイロード
    
    戻り値:
        Slack応答フォーマットのJSON
    """

    # イベントタイプの確認
    if payload.get("type") == "url_verification":
        # URL検証チャレンジの応答
        return {"challenge": payload.get("challenge")}
    
    # イベントの取得
    event = payload.get("event", {})

    # メンションイベントでない場合は無視
    if event.get("type") != "app_mention":
        return {"ok": True}

    # メッセージテキストからメンション部分を削除
    bot_user_id = payload.get("event", {}).get("bot_id") or payload.get("authorizations", [{}])[0].get("user_id", "")
    text = event.get("text", "").replace(f"<@{bot_user_id}>", "").strip()
    
    # チャンネルとスレッド情報の取得
    channel = event.get("channel")
    thread_ts = event.get("thread_ts") or event.get("ts")
    
    # ユーザー情報の取得
    user = event.get("user")
    
    # キャラクター設定
    character = {
        "name": "文野環",
        "personality": "元気で明るい、ポジティブな性格",
        "speaking_style": "元気で明るい口調、「〜だよ！」「〜だね！」「〜なの」などの語尾が特徴的。一人称は「たまき」「私」。"
    }
    
    # 非同期でGrok APIを呼び出して応答を生成し、Slackに送信
    # イベントを受け取ったことを即座に応答
    asyncio.create_task(process_and_reply(text, channel, thread_ts, character))
    
    # Slackイベントに対する応答（成功）
    return {"ok": True}

async def process_and_reply(text: str, channel: str, thread_ts: str, character: Dict[str, str]):
    """
    メッセージを処理して返信する非同期関数
    
    引数:
        text: ユーザーからのメッセージ
        channel: チャンネルID
        thread_ts: スレッドのタイムスタンプ
        character: キャラクター設定
    """
    try:
        # スレッドの会話履歴を取得
        thread_response = get_thread_messages(channel, thread_ts)
        
        if not thread_response.get("ok"):
            print(f"スレッド取得エラー: {thread_response.get('error')}")
            thread_messages = []
        else:
            thread_messages = thread_response.get("messages", [])
            print(f"スレッドメッセージ数: {len(thread_messages)}")
        
        # スレッドの会話履歴をコンテキストとして使用
        conversation_context = ""
        if thread_messages:
            # 最大5件の過去メッセージを取得（最新のものから）
            recent_messages = thread_messages[-5:] if len(thread_messages) > 5 else thread_messages
            
            for msg in recent_messages:
                # ボットのメッセージかユーザーのメッセージかを判断
                is_bot = msg.get("bot_id") is not None
                msg_text = msg.get("text", "")
                
                if is_bot:
                    conversation_context += f"文野環: {msg_text}\n"
                else:
                    conversation_context += f"ユーザー: {msg_text}\n"
            
            print("会話コンテキスト作成完了")
        
        # Grok APIを呼び出して応答を生成（会話履歴を含める）
        prompt = f"{conversation_context}\nユーザー: {text}"
        response_text = call_grok_api(prompt, character, DEFAULT_PERSONA)
        
        # Slackにメッセージを送信
        result = post_message(channel, response_text, thread_ts)
        
        if not result.get("ok"):
            print(f"Slackメッセージ送信エラー: {result.get('error')}")
    except Exception as e:
        print(f"メッセージ処理エラー: {str(e)}")
        import traceback
        traceback.print_exc()
