from fastapi import FastAPI, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
import json
from datetime import datetime, timedelta
import os

from parser import parse_superchat_command, validate_superchat_params, get_help_text
from slack_verification import add_slack_verification_middleware

# FastAPIのインスタンス作成
app = FastAPI(title="Slash Commands API", description="Slackのスラッシュコマンドを処理するAPI")

# Slack検証ミドルウェアを追加
add_slack_verification_middleware(app)

# ファイルパス
SUPERCHAT_DATA_FILE = "./data/superchat_data.json"
USER_DISPLAY_NAME_FILE = "./data/user_display_names.json"

def load_superchat_data() -> List[Dict[str, Any]]:
    """
    スーパーチャットデータを読み込む関数
    
    戻り値:
        スーパーチャットデータのリスト
    """
    if not os.path.exists(SUPERCHAT_DATA_FILE):
        return []
    
    try:
        with open(SUPERCHAT_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_superchat_data(data: List[Dict[str, Any]]) -> None:
    """
    スーパーチャットデータを保存する関数
    
    引数:
        data: スーパーチャットデータのリスト
    """
    with open(SUPERCHAT_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_user_display_names() -> Dict[str, str]:
    """
    ユーザーIDと表示名のマッピングを読み込む関数
    
    戻り値:
        ユーザーIDと表示名のマッピング辞書
    """
    if not os.path.exists(USER_DISPLAY_NAME_FILE):
        return {}
    
    try:
        with open(USER_DISPLAY_NAME_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_user_display_names(data: Dict[str, str]) -> None:
    """
    ユーザーIDと表示名のマッピングを保存する関数
    
    引数:
        data: ユーザーIDと表示名のマッピング辞書
    """
    with open(USER_DISPLAY_NAME_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_display_name(user_id: str, user_name: str, display_name: str = None) -> str:
    """
    ユーザーの表示名を取得する関数
    
    引数:
        user_id: ユーザーID
        user_name: ユーザー名
        display_name: 表示名（設定されていない場合はNone）
    
    戻り値:
        表示名
    """
    # マッピングを読み込む
    user_display_names = load_user_display_names()
    
    # 表示名が指定されている場合は、マッピングを更新して返す
    if display_name:
        user_display_names[user_id] = display_name
        save_user_display_names(user_display_names)
        return display_name
    
    # マッピングに存在する場合は、マッピングから取得
    if user_id in user_display_names:
        return user_display_names[user_id]
    
    # マッピングに存在しない場合は、ユーザー名を返す
    return user_name

@app.post("/superchat")
async def superchat(
    text: str = Form(""),
    user_name: str = Form("ユーザー"),
    channel_name: str = Form("チャンネル"),
    user_id: str = Form(""),
    team_id: str = Form(""),
    display_name: str = Form(None),  # Slackの表示名（設定されていない場合はNone）
):
    """
    スーパーチャットコマンドを処理するエンドポイント
    
    引数:
        text: コマンドテキスト（例: "add 1000 -m こんにちは -y https://youtube.com/channel/123"）
        user_name: コマンドを実行したユーザー名
        channel_name: コマンドが実行されたチャンネル名
        user_id: コマンドを実行したユーザーID
        team_id: チームID
        display_name: Slackの表示名（設定されていない場合はuser_nameを使用）
    
    戻り値:
        Slack応答フォーマットのJSON
    """
    # コマンドが空または "help" の場合はヘルプを表示
    if not text.strip() or text.strip() == "help":
        return {
            "response_type": "ephemeral",  # 実行者のみに表示
            "text": get_help_text()
        }
    
    # コマンドテキストをパース
    parsed_result = parse_superchat_command(text)
    
    # バリデーション
    is_valid, error_message = validate_superchat_params(parsed_result)
    
    if not is_valid:
        # エラーの場合はエフェメラルメッセージ（実行者のみに表示）
        return {
            "response_type": "ephemeral",
            "text": f"コマンドエラー: {error_message}"
        }
    
    # サブコマンドに応じた処理
    subcommand = parsed_result["subcommand"]
    
    # addサブコマンド - スパチャの登録
    if subcommand == "add":
        return handle_add_command(parsed_result, user_name, user_id, channel_name, team_id, display_name)
    
    # statサブコマンド - スパチャの統計表示
    elif subcommand == "stat":
        return handle_stat_command(parsed_result, user_name, user_id, channel_name, display_name)
    
    # 未知のサブコマンド
    return {
        "response_type": "ephemeral",
        "text": f"未知のサブコマンド: {subcommand}\n{get_help_text()}"
    }

def handle_add_command(
    parsed_result: Dict[str, Any],
    user_name: str,
    user_id: str,
    channel_name: str,
    team_id: str,
    display_name: str = None
) -> Dict[str, Any]:
    """
    addサブコマンドを処理する関数
    
    引数:
        parsed_result: パース結果
        user_name: ユーザー名
        user_id: ユーザーID
        channel_name: チャンネル名
        team_id: チームID
        display_name: Slackの表示名（設定されていない場合はuser_nameを使用）
    
    戻り値:
        Slack応答フォーマットのJSON
    """
    # 金額
    amount = parsed_result["amount"]
    
    # メッセージ（指定がなければデフォルト）
    message = parsed_result["message"] or "コメントなし"
    
    # YouTubeチャンネル情報
    youtube = parsed_result["youtube"]
    
    # スーパーチャットデータを読み込む
    superchat_data = load_superchat_data()
    
    # 日付の処理（指定がなければ現在日付）
    date_str = parsed_result.get("date")
    if date_str:
        # 日付が指定されている場合はその日付を使用
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        # 現在の時刻情報を追加
        now = datetime.now()
        date_obj = date_obj.replace(hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)
        timestamp = date_obj.isoformat()
    else:
        # 指定がない場合は現在日時
        timestamp = datetime.now().isoformat()
    
    # 新しいスーパーチャットデータを追加
    new_superchat = {
        "user_name": user_name,
        "user_id": user_id,
        "channel_name": channel_name,
        "team_id": team_id,
        "amount": amount,
        "message": message,
        "youtube": youtube,
        "timestamp": timestamp
    }
    
    superchat_data.append(new_superchat)
    
    # データを保存
    save_superchat_data(superchat_data)
    
    # YouTubeチャンネル情報（あれば表示）
    youtube_info = ""
    if youtube:
        youtube_info = f"\n配信URL: {youtube}"
    
    # 表示名を取得
    shown_name = get_display_name(user_id, user_name, display_name)
    
    # 成功の場合はチャンネルに表示
    # 日付を y-m-d 形式に変換
    ymd_str = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d")
    return {
        "response_type": "in_channel",
        "text": f"{shown_name}さんが{ymd_str}に{amount}円のスーパーチャットを送りました！\n「{message}」{youtube_info}"
    }

def handle_stat_command(
    parsed_result: Dict[str, Any],
    user_name: str,
    user_id: str,
    channel_name: str,
    display_name: str = None
) -> Dict[str, Any]:
    """
    statサブコマンドを処理する関数
    
    引数:
        parsed_result: パース結果
        user_name: ユーザー名
        user_id: ユーザーID
        channel_name: チャンネル名
        display_name: Slackの表示名（設定されていない場合はuser_nameを使用）
    
    戻り値:
        Slack応答フォーマットのJSON
    """
    # スーパーチャットデータを読み込む
    superchat_data = load_superchat_data()
    
    if not superchat_data:
        return {
            "response_type": "ephemeral",
            "text": "スーパーチャットのデータがありません。"
        }
    
    # フィルタリング条件
    target_user = parsed_result.get("user")
    days = parsed_result.get("days", 30)
    all_period = parsed_result.get("all", False)
    me_only = parsed_result.get("me", False)
    
    # 日付でフィルタリング（--allオプションが指定されている場合は全期間）
    if all_period:
        filtered_data = superchat_data.copy()
        # 期間の表示用に最古と最新の日付を取得
        if filtered_data:
            from_date = min(sc["timestamp"] for sc in filtered_data)
            to_date = max(sc["timestamp"] for sc in filtered_data)
        else:
            from_date = datetime.now().isoformat()
            to_date = datetime.now().isoformat()
    else:
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        filtered_data = [
            sc for sc in superchat_data
            if sc["timestamp"] >= cutoff_date
        ]
        # 期間の表示用に日付を設定
        from_date = cutoff_date
        to_date = datetime.now().isoformat()
    
    # ユーザーでフィルタリング
    if me_only and target_user:
        # --me と --user の両方が指定されている場合は --me を優先
        filtered_data = [
            sc for sc in filtered_data
            if sc["user_id"] == user_id
        ]
        # ユーザー情報の表示用
        user_filter_type = "me_and_user"
    elif me_only:
        # 自分のユーザーIDでフィルタリング
        filtered_data = [
            sc for sc in filtered_data
            if sc["user_id"] == user_id
        ]
        # ユーザー情報の表示用
        user_filter_type = "me_only"
    elif target_user:
        # Slackのメンション形式（@username）の処理
        if target_user.startswith('@'):
            # @を除去してユーザー名を取得
            username = target_user[1:]
            filtered_data = [
                sc for sc in filtered_data
                if username.lower() in sc["user_name"].lower()
            ]
        else:
            # 通常の検索
            filtered_data = [
                sc for sc in filtered_data
                if target_user.lower() in sc["user_name"].lower()
            ]
        # ユーザー情報の表示用
        user_filter_type = "target_user"
    else:
        # ユーザー情報の表示用
        user_filter_type = "all_users"
    
    if not filtered_data:
        filter_info = f"過去{days}日間"
        if target_user:
            filter_info += f"、ユーザー '{target_user}'"
        
        return {
            "response_type": "ephemeral",
            "text": f"{filter_info} のスーパーチャットデータはありません。"
        }
    
    # 日付を表示用にフォーマット
    from_date_str = datetime.fromisoformat(from_date).strftime("%Y-%m-%d")
    to_date_str = datetime.fromisoformat(to_date).strftime("%Y-%m-%d")
    
    # 統計情報を計算
    total_amount = sum(sc["amount"] for sc in filtered_data)
    
    # ユーザーIDと表示名のマッピングを読み込む
    user_display_names = load_user_display_names()
    
    # ユーザー別のデータを集計
    user_data = {}
    for sc in filtered_data:
        user_id = sc["user_id"]
        user_name = sc["user_name"]
        
        # 表示名を取得
        display_name = user_display_names.get(user_id, user_name)
        
        # ユーザーデータを初期化（存在しない場合）
        if display_name not in user_data:
            user_data[display_name] = {
                "total": 0,
                "donations": []
            }
        
        # 金額を加算
        amount = sc["amount"]
        user_data[display_name]["total"] += amount
        
        # 日付をフォーマット
        date_str = datetime.fromisoformat(sc["timestamp"]).strftime("%Y-%m-%d")
        
        # 寄付情報を追加
        user_data[display_name]["donations"].append({
            "date": date_str,
            "amount": amount,
            "message": sc.get("message", "コメントなし")
        })
    
    # ユーザーを金額順にソート
    sorted_users = sorted(
        user_data.items(),
        key=lambda x: x[1]["total"],
        reverse=True
    )
    
    # 統計情報のテキストを作成
    if all_period:
        period_info = f"全期間 ({from_date_str} 〜 {to_date_str})"
    else:
        period_info = f"期間: {from_date_str} 〜 {to_date_str}"
    
    # ユーザー情報の表示用テキスト
    if me_only:
        # 自分の表示名を取得
        my_display_name = get_display_name(user_id, user_name, display_name)
        user_info = f"{my_display_name}のみ"
    elif target_user:
        # ターゲットユーザーの表示名を取得
        if target_user.startswith('@'):
            # @を除去してユーザー名を取得
            username = target_user[1:]
            # ユーザーIDを検索
            target_user_id = None
            target_user_name = None
            for sc in superchat_data:
                if username.lower() in sc["user_name"].lower():
                    target_user_id = sc["user_id"]
                    target_user_name = sc["user_name"]
                    break
            
            if target_user_id:
                # 表示名を取得
                target_display_name = get_display_name(target_user_id, target_user_name)
                user_info = f"{target_display_name}"
            else:
                user_info = f"ユーザー '{target_user}'"
        else:
            user_info = f"ユーザー '{target_user}'"
    else:
        user_info = "全ユーザー"
    
    stats_text = f"*スーパーチャット統計 ({user_info}, {period_info})*\n\n"
    stats_text += f"総額: {total_amount}円\n"
    stats_text += f"件数: {len(filtered_data)}件\n\n"
    
    # ユーザー別の詳細情報
    if sorted_users:
        stats_text += "*ユーザー別詳細*\n"
        for user_name, data in sorted_users:
            stats_text += f"\n*{user_name}* - 合計: {data['total']}円\n"
            
            # 日付と金額の一覧
            for donation in sorted(data["donations"], key=lambda x: x["date"]):
                stats_text += f"・{donation['date']}: {donation['amount']}円\n"
    
    # 成功の場合はチャンネルに表示
    return {
        "response_type": "in_channel",
        "text": stats_text
    }

@app.get("/")
async def root():
    """
    ルートエンドポイント - APIが稼働していることを確認
    """
    return {"status": "API is running", "endpoints": ["/superchat"]}
