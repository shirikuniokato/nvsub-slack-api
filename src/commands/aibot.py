from fastapi import Request, Body
from typing import Dict, Any, Optional
import json
import os
import asyncio
import time
import random
from data.handlers import get_character_by_id
from utils.grok_api import call_grok_api as call_grok_api_original, call_grok_api_streaming as call_grok_api_streaming_original
from utils.openai_api import call_openai_api, call_openai_api_streaming
from utils.claude_api import call_claude_api, call_claude_api_streaming
from utils.gemini_api import call_gemini_api, call_gemini_api_streaming
from utils.ai_provider import get_current_provider
from utils.slack_api import post_message, get_thread_messages, update_message, download_and_convert_image, download_and_convert_pdf

# キャラクターのペルソナ設定ファイルのパス
DEFAULT_PERSONA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "default_persona.txt")

# ペルソナ設定ファイルを読み込む関数
def load_default_persona():
    try:
        with open(DEFAULT_PERSONA_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"ペルソナ設定ファイルの読み込みエラー: {str(e)}")
        return "ペルソナ設定ファイルが読み込めませんでした。"

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
    
    # メンションのみのメッセージ（テキストが空）の場合
    if not text:
        # スレッド内かどうかを判断
        is_in_thread = event.get("thread_ts") is not None and event.get("thread_ts") != event.get("ts")
        
        if is_in_thread:
            print("スレッド内の無言メンションのためスレッドを読み込んで返信します")
            # スレッド内の場合はスレッドを読み込んで返信
            channel = event.get("channel")
            thread_ts = event.get("thread_ts") or event.get("ts")
            # 非同期でスレッドを読み込んで返信
            asyncio.create_task(process_and_reply("このスレッドの内容について教えて", channel, thread_ts, None, bot_user_id))
        else:
            print("スレッド外の無言メンションのためおみくじを返信します")
            # スレッド外の場合はおみくじを返信
            channel = event.get("channel")
            thread_ts = event.get("thread_ts") or event.get("ts")
            # 非同期でおみくじを生成して返信
            asyncio.create_task(process_and_reply("今日のおみくじを引いて、結果と簡単な説明を教えて", channel, thread_ts, None, bot_user_id))
        
        return {"ok": True}
    
    # チャンネルとスレッド情報の取得
    channel = event.get("channel")
    thread_ts = event.get("thread_ts") or event.get("ts")
    
    # ユーザー情報の取得
    user = event.get("user")
    
    # 非同期でGrok APIを呼び出して応答を生成し、Slackに送信
    # イベントを受け取ったことを即座に応答
    asyncio.create_task(process_and_reply(text, channel, thread_ts, None, bot_user_id))
    
    # Slackイベントに対する応答（成功）
    return {"ok": True}

# プロバイダーに基づいてAPIを呼び出す関数
def call_api(prompt, character=None, conversation_history=None):
    """
    現在の設定に基づいて適切なAI APIを呼び出す関数
    """
    try:
        provider = get_current_provider()
        
        if provider == "openai":
            return call_openai_api(prompt, character, conversation_history)
        elif provider == "claude":
            return call_claude_api(prompt, character, conversation_history)
        elif provider == "gemini":
            return call_gemini_api(prompt, character, conversation_history)
        else:  # デフォルトはGrok
            return call_grok_api_original(prompt, character, conversation_history)
    except Exception as e:
        print(f"API呼び出しエラー: {str(e)}")
        # エラーが発生した場合はGrokをデフォルトとして使用
        return call_grok_api_original(prompt, character, conversation_history)

# プロバイダーに基づいてストリーミングAPIを呼び出す関数
def call_api_streaming(prompt, character=None, conversation_history=None, callback=None):
    """
    現在の設定に基づいて適切なAI APIをストリーミングモードで呼び出す関数
    """
    try:
        provider = get_current_provider()
        
        if provider == "openai":
            return call_openai_api_streaming(prompt, character, conversation_history, callback)
        elif provider == "claude":
            return call_claude_api_streaming(prompt, character, conversation_history, callback)
        elif provider == "gemini":
            return call_gemini_api_streaming(prompt, character, conversation_history, callback)
        else:  # デフォルトはGrok
            return call_grok_api_streaming_original(prompt, character, conversation_history, callback)
    except Exception as e:
        print(f"ストリーミングAPI呼び出しエラー: {str(e)}")
        # エラーが発生した場合はGrokをデフォルトとして使用
        return call_grok_api_streaming_original(prompt, character, conversation_history, callback)

async def process_and_reply(text: str, channel: str, thread_ts: str, character: Optional[Dict[str, str]] = None, bot_user_id: str = None):
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
        
        # スレッドの会話履歴を構造化されたフォーマットで構築
        conversation_messages = []
        
        # システムメッセージを追加（キャラクター設定）
        system_content = load_default_persona()
        conversation_messages.append({
            "role": "system",
            "content": [{"type": "text", "text": system_content}]
        })
        
        if thread_messages:
            for msg in thread_messages:
                # ボットのメッセージかユーザーのメッセージかを判断
                # 自分のbotのメッセージかどうかを判定
                is_self_bot = msg.get("bot_id") is not None and bot_user_id is not None and msg.get("bot_id") == bot_user_id
                
                msg_text = msg.get("text", "")
                
                # 「考え中...」や「... :neko1:」を含むメッセージはスキップ
                if "考え中..." in msg_text or "... :neko1:" in msg_text or "...(続く)" in msg_text or "(続き " in msg_text:
                    continue
                
                # メッセージの内容を構築
                content_items = []
                
                # 画像やPDFが含まれているかチェック
                if "files" in msg and msg["files"]:
                    for file in msg["files"]:
                        # 画像ファイルの処理
                        if file.get("mimetype", "").startswith("image/"):
                            # 画像URLを取得
                            image_url = file.get("url_private")
                            
                            if image_url:
                                print(f"画像を処理中: {image_url}")
                                
                                # 画像をダウンロードしてbase64に変換
                                success, mime_type, base64_data = download_and_convert_image(image_url)
                                
                                if success:
                                    # base64形式のURLを作成
                                    data_url = f"data:{mime_type};base64,{base64_data}"
                                    
                                    # 画像をコンテンツに追加
                                    content_items.append({
                                        "type": "image_url",
                                        "image_url": {
                                            "url": data_url,
                                            "detail": "high"
                                        }
                                    })
                                    print(f"画像の処理に成功しました: {file.get('name')}")
                                else:
                                    print(f"画像の処理に失敗しました: {base64_data}")
                        
                        # PDFファイルの処理
                        elif file.get("mimetype", "") == "application/pdf":
                            # PDF URLを取得
                            pdf_url = file.get("url_private")
                            
                            if pdf_url:
                                print(f"PDFを処理中: {pdf_url}")
                                
                                # PDFをダウンロードしてbase64に変換
                                success, mime_type, base64_data = download_and_convert_pdf(pdf_url)
                                
                                if success:
                                    # PDFをコンテンツに追加（画像と同じ形式）
                                    content_items.append({
                                        "type": "document",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "application/pdf",
                                            "data": base64_data
                                        }
                                    })
                                    print(f"PDFの処理に成功しました: {file.get('name')}")
                                else:
                                    print(f"PDFの処理に失敗しました: {base64_data}")
                
                # テキストをコンテンツに追加
                if msg_text:
                    content_items.append({
                        "type": "text",
                        "text": msg_text
                    })
                
                # コンテンツが空でない場合のみメッセージを追加
                if content_items:
                    if is_self_bot:
                        conversation_messages.append({
                            "role": "assistant",
                            "content": content_items
                        })
                    else:
                        conversation_messages.append({
                            "role": "user",
                            "content": content_items
                        })
            
            print(f"構造化された会話コンテキスト作成完了: {len(conversation_messages)}メッセージ")
        
        # 現在のユーザーメッセージを追加
        # 現在のメッセージには画像が含まれていないと仮定
        user_message = {
            "role": "user",
            "content": [{"type": "text", "text": text}]
        }
        
        # 最初に「考え中...」というメッセージを送信
        initial_message = "考え中..."
        initial_result = post_message(channel, initial_message, thread_ts)
        
        if not initial_result.get("ok"):
            print(f"初期メッセージ送信エラー: {initial_result.get('error')}")
            return
        
        # 送信したメッセージのタイムスタンプを取得
        message_ts = initial_result.get("ts")
        
        # 応答を蓄積する変数
        full_response = ""
        
        # 更新間隔（秒）
        update_interval = 1.0
        last_update_time = 0
        
        # 現在のメッセージ番号
        current_message_num = 1
        
        # 最大メッセージサイズ（バイト）
        MAX_MESSAGE_SIZE = 3000
        
        # ストリーミングコールバック関数
        def streaming_callback(chunk: str, is_done: bool):
            nonlocal full_response, last_update_time, message_ts, current_message_num
            
            # 応答を蓄積
            full_response += chunk
            
            # 現在の時間を取得
            current_time = time.time()
            
            # 更新間隔を超えた場合、またはストリーミングが完了した場合にメッセージを更新
            if is_done or (current_time - last_update_time >= update_interval):
                # 表示用のテキストを作成
                display_text = full_response
                
                # 入力中の場合は「... :pencil:」を追加
                if not is_done:
                    display_text += "... :neko1:"
                
                # メッセージサイズをチェック
                if len(display_text.encode('utf-8')) > MAX_MESSAGE_SIZE:
                    print(f"メッセージサイズが制限を超えました: {len(display_text.encode('utf-8'))} バイト")
                    
                    # 現在のメッセージを完了させる（続きを示す）
                    update_result = update_message(channel, message_ts, full_response[:MAX_MESSAGE_SIZE-20] + "...(続く)")
                    
                    if not update_result.get("ok"):
                        print(f"メッセージ更新エラー: {update_result.get('error')}")
                    
                    # 新しいメッセージを作成して続きを投稿
                    current_message_num += 1
                    continuation_text = f"(続き {current_message_num}) " + full_response[MAX_MESSAGE_SIZE-20:]
                    
                    # 入力中の場合は「... :neko1:」を追加
                    if not is_done:
                        continuation_text += "... :neko1:"
                    
                    # 新しいメッセージを投稿
                    new_message_result = post_message(channel, continuation_text, thread_ts)
                    
                    if not new_message_result.get("ok"):
                        print(f"新規メッセージ送信エラー: {new_message_result.get('error')}")
                    else:
                        # 新しいメッセージのタイムスタンプを更新
                        message_ts = new_message_result.get("ts")
                        # 応答を更新（新しいメッセージの内容のみに）
                        full_response = full_response[MAX_MESSAGE_SIZE-20:]
                else:
                    # 通常のメッセージ更新
                    update_result = update_message(channel, message_ts, display_text)
                    
                    if not update_result.get("ok"):
                        print(f"メッセージ更新エラー: {update_result.get('error')}")
                
                # 最終更新時間を更新
                last_update_time = current_time
        
        # ストリーミングモードでAI APIを呼び出し
        for _ in call_api_streaming(user_message, character, conversation_messages, streaming_callback):
            # ジェネレーターを消費するだけで、実際の処理はコールバック関数で行う
            pass
        
    except Exception as e:
        print(f"メッセージ処理エラー: {str(e)}")
        import traceback
        traceback.print_exc()
