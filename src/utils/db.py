import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any, List, Optional, Tuple

# 環境変数からデータベース接続情報を取得
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

def get_db_connection():
    """
    PostgreSQLデータベースへの接続を取得する関数
    
    戻り値:
        データベース接続オブジェクト
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        raise Exception(f"データベース接続エラー: {str(e)}")

def execute_query(query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
    """
    SQLクエリを実行し、結果を辞書のリストとして返す関数
    
    引数:
        query: 実行するSQLクエリ
        params: クエリパラメータ（オプション）
    
    戻り値:
        クエリ結果の辞書のリスト
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            
            # SELECT文の場合は結果を返す
            if query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            
            # SELECT文以外の場合は影響を受けた行数を返す
            affected_rows = cursor.rowcount
            conn.commit()
            return [{"affected_rows": affected_rows}]
    
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"クエリ実行エラー: {str(e)}")
    
    finally:
        if conn:
            conn.close()
