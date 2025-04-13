#!/usr/bin/env python3
"""
パーサーのテストスクリプト
コマンドラインから直接実行して、パーサーの動作を確認できます
"""

from src.parser import parse_superchat_command, validate_superchat_params, get_help_text
import sys
from datetime import datetime, timedelta

def test_parser_with_input():
    """
    ユーザー入力でパーサーをテストする関数
    """
    print("スパチャコマンドパーサーテスト")
    print("終了するには 'exit' または 'quit' と入力してください")
    print("ヘルプを表示するには 'help' と入力してください")
    print("使用例: add 1000 -m こんにちは -y https://youtube.com/channel/123 -d 2025-04-13")
    print("使用例: stat -u @username -d 7")
    print("-" * 50)
    
    while True:
        try:
            # ユーザー入力を取得
            command = input("\nコマンドを入力してください: ")
            
            # 終了コマンドのチェック
            if command.lower() in ['exit', 'quit']:
                print("テストを終了します")
                break
            
            # ヘルプコマンドのチェック
            if command.lower() == 'help':
                print(get_help_text())
                continue
            
            # 空のコマンドはスキップ
            if not command.strip():
                continue
            
            # パース実行
            result = parse_superchat_command(command)
            is_valid, error = validate_superchat_params(result)
            
            # 結果表示
            print("\n--- パース結果 ---")
            if is_valid:
                print(f"✅ 有効なコマンド")
                print(f"サブコマンド: {result['subcommand']}")
                
                # addサブコマンドの場合
                if result['subcommand'] == 'add':
                    print(f"金額: {result['amount']}円")
                    print(f"メッセージ: {result['message'] or '(なし)'}")
                    print(f"YouTube: {result['youtube'] or '(なし)'}")
                    print(f"日付: {result['date'] or '(現在日付)'}")
                    
                    # Slack応答のシミュレーション
                    user_name = "テストユーザー"
                    message = result["message"] or "コメントなし"
                    youtube_info = f"\nYouTubeチャンネル: {result['youtube']}" if result["youtube"] else ""
                    
                    print("\n--- Slack応答シミュレーション (add) ---")
                    print(f"{user_name}さんが{result['amount']}円のスーパーチャットを送りました！")
                    print(f"「{message}」{youtube_info}")
                
                # statサブコマンドの場合
                elif result['subcommand'] == 'stat':
                    user = result.get('user')
                    days = result.get('days', 30)
                    print(f"ユーザー: {user or '(全員)'}")
                    print(f"日数: {days}日")
                    
                    # Slack応答のシミュレーション
                    filter_info = f"過去{days}日間"
                    if user:
                        # @形式の表示を維持
                        filter_info += f"、ユーザー '{user}'"
                    
                    print("\n--- Slack応答シミュレーション (stat) ---")
                    print(f"*スーパーチャット統計 ({filter_info})*")
                    print("総額: 10000円")
                    print("件数: 5件")
                    print("\n*トップ貢献者*")
                    print("1. テストユーザー1: 5000円")
                    print("2. テストユーザー2: 3000円")
                    print("3. テストユーザー3: 2000円")
            else:
                print(f"❌ 無効なコマンド: {error}")
            
        except KeyboardInterrupt:
            print("\nテストを終了します")
            break
        except Exception as e:
            print(f"エラー: {str(e)}")

def main():
    """
    メイン関数
    """
    # コマンドライン引数があれば、それをテスト
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
        print(f"コマンド: {command}")
        result = parse_superchat_command(command)
        is_valid, error = validate_superchat_params(result)
        
        if is_valid:
            subcommand = result["subcommand"]
            if subcommand == "add":
                print(f"有効なコマンド: サブコマンド={subcommand}, 金額={result['amount']}, メッセージ={result['message']}, YouTube={result['youtube']}, 日付={result['date'] or '(現在日付)'}")
            elif subcommand == "stat":
                print(f"有効なコマンド: サブコマンド={subcommand}, ユーザー={result.get('user')}, 日数={result.get('days')}")
        else:
            print(f"無効なコマンド: {error}")
    else:
        # 引数がなければ対話モード
        test_parser_with_input()

if __name__ == "__main__":
    main()
