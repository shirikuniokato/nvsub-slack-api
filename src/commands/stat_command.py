from typing import Dict, Any
from datetime import datetime, timedelta
from data.handlers import load_superchat_data, load_user_display_names
from utils.display_name import get_display_name

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
            
            # 日付と金額の一覧（日付の降順 - 最新のものから表示）
            for donation in sorted(data["donations"], key=lambda x: x["date"], reverse=True):
                stats_text += f"・{donation['date']}: {donation['amount']}円\n"
    
    # 成功の場合はチャンネルに表示
    return {
        "response_type": "in_channel",
        "text": stats_text
    }
