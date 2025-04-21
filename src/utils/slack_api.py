import os
import requests
import base64
from typing import Dict, Any, Optional, List, Tuple
import time
import io
import json

# SlackのAPIトークン（環境変数から取得）
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

def post_message(
    channel: str,
    text: str,
    thread_ts: Optional[str] = None
) -> Dict[str, Any]:
    """
    Slackにメッセージを投稿する関数
    
    引数:
        channel: チャンネルID
        text: 投稿するテキスト
        thread_ts: スレッドのタイムスタンプ（スレッド内の返信の場合）
    
    戻り値:
        Slackからのレスポンス
    """
    if not SLACK_BOT_TOKEN:
        return {"ok": False, "error": "SLACK_BOT_TOKENが設定されていません"}
    
    # APIエンドポイント
    url = "https://slack.com/api/chat.postMessage"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }
    
    # リクエストボディ
    data = {
        "channel": channel,
        "text": text
    }
    
    # スレッドの指定がある場合は追加
    if thread_ts:
        data["thread_ts"] = thread_ts
    
    try:
        # APIリクエスト
        response = requests.post(url, headers=headers, json=data)
        
        # レスポンスのチェック
        response.raise_for_status()
        
        # JSONレスポンスの解析
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"APIリクエストエラー: {str(e)}"}
    except ValueError as e:
        return {"ok": False, "error": f"JSONパースエラー: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": f"予期せぬエラー: {str(e)}"}

def publish_home_view(
    user_id: str,
    view: Dict[str, Any]
) -> Dict[str, Any]:
    """
    ユーザーのApp Homeビューを公開する関数
    
    引数:
        user_id: ユーザーID
        view: App Homeのビュー定義
    
    戻り値:
        Slackからのレスポンス
    """
    if not SLACK_BOT_TOKEN:
        return {"ok": False, "error": "SLACK_BOT_TOKENが設定されていません"}
    
    # APIエンドポイント
    url = "https://slack.com/api/views.publish"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }
    
    # リクエストボディ
    data = {
        "user_id": user_id,
        "view": view
    }
    
    try:
        # APIリクエスト
        response = requests.post(url, headers=headers, json=data)
        
        # レスポンスのチェック
        response.raise_for_status()
        
        # JSONレスポンスの解析
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"APIリクエストエラー: {str(e)}"}
    except ValueError as e:
        return {"ok": False, "error": f"JSONパースエラー: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": f"予期せぬエラー: {str(e)}"}

def download_and_convert_image(file_url: str) -> Tuple[bool, str, str]:
    """
    Slackの画像URLから画像をダウンロードし、base64に変換する関数
    
    引数:
        file_url: Slackの画像URL
    
    戻り値:
        成功フラグ、MIMEタイプ、base64エンコードされた画像データのタプル
    """
    if not SLACK_BOT_TOKEN:
        return False, "", "SLACK_BOT_TOKENが設定されていません"
    
    try:
        # ヘッダーにトークンを設定
        headers = {
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
        }
        
        # 画像をダウンロード
        response = requests.get(file_url, headers=headers)
        
        # レスポンスのチェック
        response.raise_for_status()
        
        # MIMEタイプを取得
        mime_type = response.headers.get("Content-Type", "image/jpeg")
        
        # 画像データをbase64にエンコード
        image_data = response.content
        base64_data = base64.b64encode(image_data).decode("utf-8")
        
        return True, mime_type, base64_data
    
    except requests.exceptions.RequestException as e:
        return False, "", f"画像ダウンロードエラー: {str(e)}"
    except Exception as e:
        return False, "", f"予期せぬエラー: {str(e)}"

def download_and_convert_pdf(file_url: str) -> Tuple[bool, str, str]:
    """
    SlackのPDF URLからPDFをダウンロードし、base64に変換する関数
    
    引数:
        file_url: SlackのPDF URL
    
    戻り値:
        成功フラグ、MIMEタイプ、base64エンコードされたPDFデータのタプル
    """
    if not SLACK_BOT_TOKEN:
        return False, "", "SLACK_BOT_TOKENが設定されていません"
    
    try:
        # ヘッダーにトークンを設定
        headers = {
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
        }
        
        # PDFをダウンロード
        response = requests.get(file_url, headers=headers)
        
        # レスポンスのチェック
        response.raise_for_status()
        
        # MIMEタイプを取得
        mime_type = response.headers.get("Content-Type", "application/pdf")
        
        # PDFデータをbase64にエンコード
        pdf_data = response.content
        base64_data = base64.b64encode(pdf_data).decode("utf-8")
        
        return True, mime_type, base64_data
    
    except requests.exceptions.RequestException as e:
        return False, "", f"PDFダウンロードエラー: {str(e)}"
    except Exception as e:
        return False, "", f"予期せぬエラー: {str(e)}"

def update_message(
    channel: str,
    ts: str,
    text: str
) -> Dict[str, Any]:
    """
    Slackのメッセージを更新する関数
    
    引数:
        channel: チャンネルID
        ts: 更新するメッセージのタイムスタンプ
        text: 新しいテキスト
    
    戻り値:
        Slackからのレスポンス
    """
    if not SLACK_BOT_TOKEN:
        return {"ok": False, "error": "SLACK_BOT_TOKENが設定されていません"}
    
    # APIエンドポイント
    url = "https://slack.com/api/chat.update"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }
    
    # リクエストボディ
    data = {
        "channel": channel,
        "ts": ts,
        "text": text
    }
    
    try:
        # APIリクエスト
        response = requests.post(url, headers=headers, json=data)
        
        # レスポンスのチェック
        response.raise_for_status()
        
        # JSONレスポンスの解析
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"APIリクエストエラー: {str(e)}"}
    except ValueError as e:
        return {"ok": False, "error": f"JSONパースエラー: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": f"予期せぬエラー: {str(e)}"}

def get_thread_messages(
    channel: str,
    thread_ts: str
) -> Dict[str, Any]:
    """
    Slackのスレッドメッセージを取得する関数
    
    引数:
        channel: チャンネルID
        thread_ts: スレッドのタイムスタンプ
    
    戻り値:
        Slackからのレスポンス（messagesキーにスレッドメッセージのリストが含まれる）
    """
    if not SLACK_BOT_TOKEN:
        return {"ok": False, "error": "SLACK_BOT_TOKENが設定されていません"}
    
    # APIエンドポイント
    url = "https://slack.com/api/conversations.replies"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }
    
    # リクエストパラメータ
    params = {
        "channel": channel,
        "ts": thread_ts
    }
    
    try:
        # APIリクエスト
        response = requests.get(url, headers=headers, params=params)
        
        # レスポンスのチェック
        response.raise_for_status()
        
        # JSONレスポンスの解析
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"APIリクエストエラー: {str(e)}"}
    except ValueError as e:
        return {"ok": False, "error": f"JSONパースエラー: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": f"予期せぬエラー: {str(e)}"}

def open_modal(
    trigger_id: str,
    view: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Slackのモーダルを開く関数
    
    引数:
        trigger_id: トリガーID
        view: モーダルのビュー定義
    
    戻り値:
        Slackからのレスポンス
    """
    if not SLACK_BOT_TOKEN:
        return {"ok": False, "error": "SLACK_BOT_TOKENが設定されていません"}
    
    # APIエンドポイント
    url = "https://slack.com/api/views.open"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }
    
    # リクエストボディ
    data = {
        "trigger_id": trigger_id,
        "view": view
    }
    
    try:
        # APIリクエスト
        response = requests.post(url, headers=headers, json=data)
        
        # レスポンスのチェック
        response.raise_for_status()
        
        # JSONレスポンスの解析
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"APIリクエストエラー: {str(e)}"}
    except ValueError as e:
        return {"ok": False, "error": f"JSONパースエラー: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": f"予期せぬエラー: {str(e)}"}

def update_modal(
    view_id: str,
    view: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Slackのモーダルを更新する関数
    
    引数:
        view_id: 更新するビューのID
        view: 新しいモーダルのビュー定義
    
    戻り値:
        Slackからのレスポンス
    """
    if not SLACK_BOT_TOKEN:
        return {"ok": False, "error": "SLACK_BOT_TOKENが設定されていません"}
    
    # APIエンドポイント
    url = "https://slack.com/api/views.update"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }
    
    # リクエストボディ
    data = {
        "view_id": view_id,
        "view": view
    }
    
    try:
        # APIリクエスト
        response = requests.post(url, headers=headers, json=data)
        
        # レスポンスのチェック
        response.raise_for_status()
        
        # JSONレスポンスの解析
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"APIリクエストエラー: {str(e)}"}
    except ValueError as e:
        return {"ok": False, "error": f"JSONパースエラー: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": f"予期せぬエラー: {str(e)}"}

def upload_file(
    channels: str,
    file: Any,
    filename: str = "file",
    filetype: str = "auto",
    thread_ts: Optional[str] = None,
    title: Optional[str] = None,
    initial_comment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Slackにファイルをアップロードする関数
    
    引数:
        channels: チャンネルID（カンマ区切りで複数指定可能）
        file: アップロードするファイル（ファイルパス、バイトデータ、またはファイルオブジェクト）
        filename: ファイル名（デフォルト: "file"）
        filetype: ファイルタイプ（デフォルト: "auto"）
        thread_ts: スレッドのタイムスタンプ（スレッド内の返信の場合）
        title: ファイルのタイトル
        initial_comment: ファイルと一緒に投稿するコメント
    
    戻り値:
        Slackからのレスポンス
    """
    if not SLACK_BOT_TOKEN:
        return {"ok": False, "error": "SLACK_BOT_TOKENが設定されていません"}
    
    # メッセージテキスト
    message_text = title if title else "画像"
    if initial_comment:
        message_text = f"{initial_comment}\n{message_text}"
    
    try:
        # 画像データを直接メッセージに添付する方法
        # APIエンドポイント
        url = "https://slack.com/api/chat.postMessage"
        
        # リクエストヘッダー
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
        }
        
        # リクエストボディ
        data = {
            "channel": channels,
            "text": message_text,
            "thread_ts": thread_ts if thread_ts else None
        }
        
        # メッセージを投稿
        response = requests.post(url, headers=headers, json=data)
        
        # レスポンスのチェック
        if not response.ok or not response.json().get("ok"):
            return {"ok": False, "error": f"メッセージ投稿エラー: {response.json().get('error')}"}
        
        # 投稿したメッセージのタイムスタンプを取得
        message_ts = response.json().get("ts")
        
        # 画像データを準備
        if hasattr(file, 'read'):
            # ファイルオブジェクトの場合
            file.seek(0)
            file_data = file.read()
        elif isinstance(file, bytes):
            # バイトデータの場合
            file_data = file
        else:
            # その他の場合（ファイルパスなど）
            with open(file, 'rb') as f:
                file_data = f.read()
        
        # 画像をBase64エンコード
        import base64
        base64_data = base64.b64encode(file_data).decode('utf-8')
        
        # 画像をメッセージに添付
        # APIエンドポイント
        url = "https://slack.com/api/files.upload"
        
        # マルチパートフォームデータを作成
        import io
        files = {
            'file': (filename, io.BytesIO(file_data), f"image/{filetype}" if filetype != "auto" else "image/png")
        }
        
        data = {
            'channels': channels,
            'thread_ts': thread_ts if thread_ts else message_ts,
            'initial_comment': '',  # 既にメッセージを投稿しているので空にする
            'title': filename
        }
        
        # ヘッダー
        headers = {
            'Authorization': f'Bearer {SLACK_BOT_TOKEN}'
        }
        
        # リクエスト送信
        upload_response = requests.post(url, headers=headers, data=data, files=files)
        
        # レスポンスのチェック
        if not upload_response.ok or not upload_response.json().get("ok"):
            error_msg = upload_response.json().get('error', 'Unknown error')
            print(f"画像アップロードエラー: {error_msg}")
            
            # エラーメッセージを追加
            update_message(channels, message_ts, f"{message_text}\n(画像のアップロードに失敗しました: {error_msg})")
            return {"ok": False, "error": f"画像アップロードエラー: {error_msg}"}
        
        return {"ok": True, "message": response.json(), "file": upload_response.json()}
    
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"APIリクエストエラー: {str(e)}"}
    except ValueError as e:
        return {"ok": False, "error": f"JSONパースエラー: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": f"予期せぬエラー: {str(e)}"}
