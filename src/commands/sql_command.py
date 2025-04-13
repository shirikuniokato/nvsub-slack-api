from fastapi import Form
from typing import Dict, Any, Optional
import re
from utils.db import execute_query

async def sql_endpoint(
    text: str = Form(""),
    user_name: str = Form("ユーザー"),
    channel_name: str = Form("チャンネル"),
    user_id: str = Form(""),
    team_id: str = Form(""),
    display_name: str = Form(None),  # Slackの表示名（設定されていない場合はNone）
) -> Dict[str, Any]:
    """
    SQLクエリを実行するエンドポイント
    
    引数:
        text: 実行するSQLクエリ
        user_name: コマンドを実行したユーザー名
        channel_name: コマンドが実行されたチャンネル名
        user_id: コマンドを実行したユーザーID
        team_id: チームID
        display_name: Slackの表示名（設定されていない場合はuser_nameを使用）
    
    戻り値:
        Slack応答フォーマットのJSON
    """
    # クエリが空の場合はヘルプを表示
    if not text.strip():
        return {
            "response_type": "ephemeral",  # 実行者のみに表示
            "text": get_help_text()
        }
    
    # 特殊コマンドの処理
    text_lower = text.strip().lower()
    if text_lower == "tables" or text_lower == "list tables":
        return await handle_tables_command()
    elif text_lower == "schemas" or text_lower == "list schemas":
        return await handle_schemas_command()
    elif text_lower.startswith("describe ") or text_lower.startswith("desc "):
        table_name = text.strip().split(" ", 1)[1].strip()
        return await handle_describe_command(table_name)
    
    # 通常のSQLクエリを実行
    try:
        # 危険なSQLコマンドをチェック
        if is_dangerous_query(text):
            return {
                "response_type": "ephemeral",
                "text": "セキュリティ上の理由により、このクエリは実行できません。データベースの変更を伴うクエリ（CREATE, DROP, ALTER, TRUNCATE, DELETE, UPDATE, INSERT）は許可されていません。"
            }
        
        # クエリを実行
        results = execute_query(text)
        
        # 結果をフォーマット
        formatted_result = format_query_results(results)
        
        # 成功の場合はチャンネルに表示
        return {
            "response_type": "in_channel",
            "text": f"*SQLクエリ実行結果*\n```{text}```\n\n{formatted_result}"
        }
    
    except Exception as e:
        # エラーの場合はエフェメラルメッセージ（実行者のみに表示）
        return {
            "response_type": "ephemeral",
            "text": f"クエリ実行エラー: {str(e)}"
        }

async def handle_tables_command() -> Dict[str, Any]:
    """
    テーブル一覧を取得するコマンドを処理する関数
    
    戻り値:
        Slack応答フォーマットのJSON
    """
    try:
        # テーブル一覧を取得するクエリを実行
        query = """
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema') 
        ORDER BY table_schema, table_name
        """
        results = execute_query(query)
        
        # 結果をフォーマット
        formatted_result = format_query_results(results)
        
        # 成功の場合はチャンネルに表示
        return {
            "response_type": "in_channel",
            "text": f"*テーブル一覧*\n\n{formatted_result}"
        }
    
    except Exception as e:
        # エラーの場合はエフェメラルメッセージ（実行者のみに表示）
        return {
            "response_type": "ephemeral",
            "text": f"テーブル一覧取得エラー: {str(e)}"
        }

async def handle_schemas_command() -> Dict[str, Any]:
    """
    スキーマ一覧を取得するコマンドを処理する関数
    
    戻り値:
        Slack応答フォーマットのJSON
    """
    try:
        # スキーマ一覧を取得するクエリを実行
        query = """
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast') 
        ORDER BY schema_name
        """
        results = execute_query(query)
        
        # 結果をフォーマット
        formatted_result = format_query_results(results)
        
        # 成功の場合はチャンネルに表示
        return {
            "response_type": "in_channel",
            "text": f"*スキーマ一覧*\n\n{formatted_result}"
        }
    
    except Exception as e:
        # エラーの場合はエフェメラルメッセージ（実行者のみに表示）
        return {
            "response_type": "ephemeral",
            "text": f"スキーマ一覧取得エラー: {str(e)}"
        }

async def handle_describe_command(table_name: str) -> Dict[str, Any]:
    """
    テーブル構造を取得するコマンドを処理する関数
    
    引数:
        table_name: テーブル名
    
    戻り値:
        Slack応答フォーマットのJSON
    """
    try:
        # テーブル名にスキーマが含まれているかチェック
        if "." in table_name:
            schema_name, table_only = table_name.split(".", 1)
            schema_condition = f"AND table_schema = '{schema_name}'"
        else:
            table_only = table_name
            schema_condition = ""
        
        # テーブル構造を取得するクエリを実行
        query = f"""
        SELECT 
            column_name, 
            data_type, 
            character_maximum_length, 
            column_default, 
            is_nullable
        FROM 
            information_schema.columns 
        WHERE 
            table_name = '{table_only}' 
            {schema_condition}
        ORDER BY 
            ordinal_position
        """
        results = execute_query(query)
        
        if not results:
            return {
                "response_type": "ephemeral",
                "text": f"テーブル '{table_name}' が見つかりません。"
            }
        
        # 結果をフォーマット
        formatted_result = format_query_results(results)
        
        # 成功の場合はチャンネルに表示
        return {
            "response_type": "in_channel",
            "text": f"*テーブル '{table_name}' の構造*\n\n{formatted_result}"
        }
    
    except Exception as e:
        # エラーの場合はエフェメラルメッセージ（実行者のみに表示）
        return {
            "response_type": "ephemeral",
            "text": f"テーブル構造取得エラー: {str(e)}"
        }

def is_dangerous_query(query: str) -> bool:
    """
    危険なSQLクエリかどうかをチェックする関数
    
    引数:
        query: チェックするSQLクエリ
    
    戻り値:
        危険なクエリの場合はTrue、そうでない場合はFalse
    """
    # 大文字小文字を区別せずにチェック
    query_upper = query.upper()
    
    # データベースの変更を伴うコマンドをチェック
    dangerous_commands = [
        r'\bCREATE\b', r'\bDROP\b', r'\bALTER\b', r'\bTRUNCATE\b',
        r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b'
    ]
    
    for command in dangerous_commands:
        if re.search(command, query_upper):
            return True
    
    return False

def format_query_results(results: list) -> str:
    """
    クエリ結果をSlack用にフォーマットする関数
    
    引数:
        results: クエリ結果のリスト
    
    戻り値:
        フォーマットされた結果の文字列
    """
    if not results:
        return "結果なし"
    
    # 影響を受けた行数の結果の場合
    if len(results) == 1 and "affected_rows" in results[0]:
        return f"影響を受けた行数: {results[0]['affected_rows']}"
    
    # テーブル形式の結果の場合
    # ヘッダー行を取得
    headers = list(results[0].keys())
    
    # 各列の最大幅を計算
    col_widths = {header: len(header) for header in headers}
    for row in results:
        for header in headers:
            value = str(row.get(header, ""))
            col_widths[header] = max(col_widths[header], len(value))
    
    # ヘッダー行を作成
    header_row = " | ".join(f"{header:{col_widths[header]}}" for header in headers)
    separator = "-+-".join("-" * col_widths[header] for header in headers)
    
    # データ行を作成
    data_rows = []
    for row in results:
        data_row = " | ".join(f"{str(row.get(header, '')):{col_widths[header]}}" for header in headers)
        data_rows.append(data_row)
    
    # 結果を結合
    formatted_result = f"{header_row}\n{separator}\n" + "\n".join(data_rows)
    
    # 結果が長すぎる場合は切り詰める
    max_length = 3000  # Slackのメッセージの最大長を考慮
    if len(formatted_result) > max_length:
        return formatted_result[:max_length] + "\n...(結果が長すぎるため切り詰められました)"
    
    return formatted_result

def get_help_text() -> str:
    """
    ヘルプテキストを取得する関数
    
    戻り値:
        ヘルプテキスト
    """
    return """
SQLクエリコマンドの使用方法:

1. 通常のSQLクエリ:
   /sql <SQLクエリ>

   例:
   /sql SELECT * FROM users LIMIT 10
   /sql SELECT count(*) FROM orders WHERE created_at > '2025-01-01'

2. テーブル一覧の取得:
   /sql tables
   /sql list tables

3. スキーマ一覧の取得:
   /sql schemas
   /sql list schemas

4. テーブル構造の取得:
   /sql describe <テーブル名>
   /sql desc <テーブル名>

   例:
   /sql describe users
   /sql desc public.orders

注意:
- セキュリティ上の理由により、データベースの変更を伴うクエリ（CREATE, DROP, ALTER, TRUNCATE, DELETE, UPDATE, INSERT）は許可されていません。
- クエリ結果は全員に表示されます。機密情報を含むクエリは実行しないでください。
- 結果が大きすぎる場合は切り詰められます。
"""
