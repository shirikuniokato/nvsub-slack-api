from typing import Dict, Any
from datetime import datetime
from data.handlers import load_superchat_data, save_superchat_data
from utils.display_name import get_display_name

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
    
    # データを保存（ユーザーIDを渡して履歴に記録）
    save_superchat_data(superchat_data, user_id, "add")
    
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
