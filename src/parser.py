import shlex
import argparse
from typing import Dict, Any, Optional, Tuple, List
import re
from datetime import datetime

def parse_superchat_command(command_text: str) -> Dict[str, Any]:
    """
    スパチャコマンドをパースする関数
    
    引数:
        command_text: コマンドテキスト（例: "add 1000 -m こんにちは -y https://youtube.com/channel/123"）
    
    戻り値:
        パース結果を含む辞書
        {
            "subcommand": str,  # サブコマンド（"add"または"stat"）
            "amount": int,      # スパチャの金額（addの場合は必須）
            "message": str,     # スパチャ時のコメント（任意）
            "youtube": str,     # YouTubeチャンネルURLやID（任意）
            "date": str,        # 日付（YYYY-MM-DD形式、任意）
            "errors": list      # パースエラーがあれば格納
        }
    """
    # 結果を格納する辞書
    result = {
        "subcommand": None,
        "amount": None,
        "message": None,
        "youtube": None,
        "date": None,
        "errors": []
    }
    
    try:
        # コマンドテキストをshlexでトークン分割
        tokens = shlex.split(command_text)
        
        if not tokens:
            result["errors"].append("コマンドが空です")
            return result
        
        # argparseでパーサーを設定
        parser = argparse.ArgumentParser(description='スパチャコマンドパーサー')
        subparsers = parser.add_subparsers(dest='subcommand', help='サブコマンド')
        
        # addサブコマンド - スパチャの登録
        add_parser = subparsers.add_parser('add', help='スパチャを登録')
        add_parser.add_argument('amount', type=int, help='スパチャの金額')
        add_parser.add_argument('-m', '--message', type=str, help='スパチャ時のコメント')
        add_parser.add_argument('-y', '--youtube', type=str, help='YouTubeチャンネルURLやID')
        add_parser.add_argument('-d', '--date', type=str, help='日付（YYYY-MM-DD形式、指定しない場合は現在日付）')
        
        # statサブコマンド - スパチャの閲覧
        stat_parser = subparsers.add_parser('stat', help='スパチャの統計を表示')
        stat_parser.add_argument('-u', '--user', type=str, help='特定ユーザーの統計を表示')
        stat_parser.add_argument('-d', '--days', type=int, default=30, help='過去X日間の統計を表示（デフォルト: 30日）')
        stat_parser.add_argument('-a', '--all', action='store_true', help='全期間の統計を表示')
        stat_parser.add_argument('-m', '--me', action='store_true', help='自分の統計のみを表示')
        
        # パース実行
        args = parser.parse_args(tokens)
        
        # サブコマンドが指定されていない場合
        if not args.subcommand:
            result["errors"].append("サブコマンド（add または stat）を指定してください")
            return result
        
        # 結果を辞書に格納
        result["subcommand"] = args.subcommand
        
        # addサブコマンドの場合
        if args.subcommand == 'add':
            result["amount"] = args.amount
            result["message"] = args.message
            result["youtube"] = args.youtube
            result["date"] = args.date
        
        # statサブコマンドの場合
        elif args.subcommand == 'stat':
            result["user"] = args.user
            result["days"] = args.days
            result["all"] = args.all
            result["me"] = args.me
        
    except argparse.ArgumentError as e:
        result["errors"].append(f"引数エラー: {str(e)}")
    except ValueError as e:
        result["errors"].append(f"値エラー: {str(e)}")
    except Exception as e:
        result["errors"].append(f"予期せぬエラー: {str(e)}")
    
    return result

def validate_superchat_params(params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    スパチャパラメータのバリデーション
    
    引数:
        params: パース結果の辞書
    
    戻り値:
        (バリデーション結果, エラーメッセージ)
    """
    # エラーがある場合
    if params["errors"]:
        return False, "\n".join(params["errors"])
    
    # サブコマンドが必須
    if not params["subcommand"]:
        return False, "サブコマンド（add または stat）を指定してください"
    
    # addサブコマンドの場合
    if params["subcommand"] == "add":
        # 金額が必須
        if params["amount"] is None:
            return False, "金額は必須です"
        
        # 金額が正の整数であることを確認
        if params["amount"] <= 0:
            return False, "金額は正の整数である必要があります"
        # 金額が5万円以下であることを確認
        if params["amount"] > 50000:
            return False, "金額は5万円以下である必要があります"
            
        # 日付形式のチェック（指定されている場合）
        if params["date"]:
            date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
            if not date_pattern.match(params["date"]):
                return False, "日付はYYYY-MM-DD形式で指定してください（例: 2025-04-13）"
            
            try:
                # 日付が有効かチェック
                datetime.strptime(params["date"], "%Y-%m-%d")
            except ValueError:
                return False, "無効な日付です。正しい日付を指定してください"
    
    # statサブコマンドの場合
    elif params["subcommand"] == "stat":
        # daysが正の整数であることを確認
        if params.get("days", 0) <= 0:
            return False, "days は正の整数である必要があります"
    
    return True, None

def get_help_text() -> str:
    """
    ヘルプテキストを取得する関数
    
    戻り値:
        ヘルプテキスト
    """
    return """
スパチャコマンドの使用方法:

1. スパチャの登録:
   /superchat add <金額> [-m|--message <メッセージ>] [-y|--youtube <URL(証跡として残すくらい)>] [-d|--date <日付>]
   
   例:
   /superchat add 1000 -m こんにちは！
   /superchat add 500 --message "長いメッセージもOK" --youtube https://youtube.com/watch?v=123456
   /superchat add 2000 --date 2025-04-13  # 特定の日付を指定（YYYY-MM-DD形式）
   
   注意:
   - 日付を指定しない場合は現在の日付が使用されます
   - 日付はYYYY-MM-DD形式で指定してください（例: 2025-04-13）

2. スパチャの統計表示:
   /superchat stat [-u|--user <ユーザー名>] [-d|--days <日数>] [-a|--all] [-m|--me]
   
   例:
   /superchat stat                # 過去30日間の統計を表示
   /superchat stat -u @username   # 特定ユーザーの統計を表示（Slackのメンション形式）
   /superchat stat --days 7       # 過去7日間の統計を表示
   /superchat stat --all          # 全期間の統計を表示
   /superchat stat --me           # 自分の統計のみを表示
   
   注意:
   - ユーザー名は@usernameのようにSlackのメンション形式で指定することを推奨
   - --all オプションを指定すると、--days オプションは無視されます
   - --me オプションを指定すると、--user オプションは無視されます
   - 複数のオプションを組み合わせて使用できます（例: --all --me）
    """

# 使用例
if __name__ == "__main__":
    # テスト用コマンド
    test_commands = [
        "1000 -m こんにちは -y https://youtube.com/channel/123",
        "500",
        "1000 --message 'これはテストです' --youtube youtube.com/user/test",
        "-m コメントのみ",  # エラーケース: 金額がない
        "abc",  # エラーケース: 金額が数値でない
    ]
    
    for cmd in test_commands:
        print(f"\nコマンド: {cmd}")
        result = parse_superchat_command(cmd)
        is_valid, error = validate_superchat_params(result)
        
        if is_valid:
            print(f"有効なコマンド: 金額={result['amount']}, メッセージ={result['message']}, YouTube={result['youtube']}")
        else:
            print(f"無効なコマンド: {error}")
