from fastapi import Form
from typing import Dict, Any, Optional
from parser import parse_superchat_command, validate_superchat_params, get_help_text
from commands.add_command import handle_add_command
from commands.stat_command import handle_stat_command

async def superchat_endpoint(
    text: str = Form(""),
    user_name: str = Form("ユーザー"),
    channel_name: str = Form("チャンネル"),
    user_id: str = Form(""),
    team_id: str = Form(""),
    display_name: str = Form(None),  # Slackの表示名（設定されていない場合はNone）
) -> Dict[str, Any]:
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
