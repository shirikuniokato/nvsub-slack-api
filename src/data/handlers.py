import json
import os
import datetime
from typing import Dict, Any, List, Optional

# ファイルパス
SUPERCHAT_DATA_FILE = "./data/superchat_data.json"
USER_DISPLAY_NAME_FILE = "./data/user_display_names.json"
AIBOT_CHARACTERS_FILE = "./data/aibot_characters.json"
SUPERCHAT_HISTORY_FILE = "./data/superchat_history.json"
PERSONA_HISTORY_FILE = "./data/persona_history.json"

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

def load_history(history_file: str) -> List[Dict[str, Any]]:
    """
    履歴データを読み込む関数
    
    引数:
        history_file: 履歴ファイルのパス
    
    戻り値:
        履歴データのリスト
    """
    if not os.path.exists(history_file):
        return []
    
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_history(history_file: str, history_data: List[Dict[str, Any]]) -> None:
    """
    履歴データを保存する関数
    
    引数:
        history_file: 履歴ファイルのパス
        history_data: 履歴データのリスト
    """
    # ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(history_file), exist_ok=True)
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)

def add_history_entry(history_file: str, action: str, details: Dict[str, Any], user_id: Optional[str] = None, 
                     content_before: Optional[str] = None, content_after: Optional[str] = None) -> None:
    """
    履歴エントリを追加する関数
    
    引数:
        history_file: 履歴ファイルのパス
        action: 実行されたアクション（追加、更新、削除など）
        details: 変更の詳細情報
        user_id: 変更を行ったユーザーID（省略可）
        content_before: 変更前の内容（省略可）
        content_after: 変更後の内容（省略可）
    """
    # 現在の履歴を読み込む
    history = load_history(history_file)
    
    # 新しいエントリを作成
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "action": action,
        "details": details
    }
    
    if user_id:
        entry["user_id"] = user_id
    
    # 変更前後の内容を追加（指定されている場合）
    if content_before is not None:
        entry["content_before"] = content_before
    
    if content_after is not None:
        entry["content_after"] = content_after
    
    # 履歴に追加
    history.append(entry)
    
    # 履歴を保存
    save_history(history_file, history)

def save_superchat_data(data: List[Dict[str, Any]], user_id: Optional[str] = None, action: str = "update") -> None:
    """
    スーパーチャットデータを保存する関数
    
    引数:
        data: スーパーチャットデータのリスト
        user_id: 変更を行ったユーザーID（省略可）
        action: 実行されたアクション（デフォルトは "update"）
    """
    # 現在のデータを読み込む（比較用）
    current_data = load_superchat_data()
    
    # データを保存
    with open(SUPERCHAT_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 変更の詳細を作成
    details = {
        "count_before": len(current_data),
        "count_after": len(data)
    }
    
    # 現在のデータと新しいデータをJSON文字列に変換
    current_data_str = json.dumps(current_data, ensure_ascii=False, indent=2)
    new_data_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    # 履歴に追加（変更前後の全文も保存）
    add_history_entry(SUPERCHAT_HISTORY_FILE, action, details, user_id, 
                     content_before=current_data_str, content_after=new_data_str)

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

def save_user_display_names(data: Dict[str, str], user_id: Optional[str] = None, action: str = "update") -> None:
    """
    ユーザーIDと表示名のマッピングを保存する関数
    
    引数:
        data: ユーザーIDと表示名のマッピング辞書
        user_id: 変更を行ったユーザーID（省略可）
        action: 実行されたアクション（デフォルトは "update"）
    """
    # 現在のデータを読み込む（比較用）
    current_data = load_user_display_names()
    
    # データを保存
    with open(USER_DISPLAY_NAME_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 変更の詳細を作成
    details = {
        "count_before": len(current_data),
        "count_after": len(data)
    }
    
    # 現在のデータと新しいデータをJSON文字列に変換
    current_data_str = json.dumps(current_data, ensure_ascii=False, indent=2)
    new_data_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    # 履歴に追加（変更前後の全文も保存）
    add_history_entry(PERSONA_HISTORY_FILE, action, details, user_id,
                     content_before=current_data_str, content_after=new_data_str)

def load_aibot_characters() -> Dict[str, Any]:
    """
    AIボットのキャラクター設定を読み込む関数
    
    戻り値:
        キャラクター設定の辞書
    """
    if not os.path.exists(AIBOT_CHARACTERS_FILE):
        # テンプレートファイルが存在する場合はそれをコピー
        template_file = AIBOT_CHARACTERS_FILE + ".template"
        if os.path.exists(template_file):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                with open(AIBOT_CHARACTERS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return data
            except Exception:
                return {"characters": []}
        return {"characters": []}
    
    try:
        with open(AIBOT_CHARACTERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"characters": []}

def save_aibot_characters(data: Dict[str, Any], user_id: Optional[str] = None, action: str = "update") -> None:
    """
    AIボットのキャラクター設定を保存する関数
    
    引数:
        data: キャラクター設定の辞書
        user_id: 変更を行ったユーザーID（省略可）
        action: 実行されたアクション（デフォルトは "update"）
    """
    # 現在のデータを読み込む（比較用）
    current_data = load_aibot_characters()
    
    # データを保存
    with open(AIBOT_CHARACTERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 変更の詳細を作成
    details = {
        "characters_before": len(current_data.get("characters", [])),
        "characters_after": len(data.get("characters", []))
    }
    
    # 現在のデータと新しいデータをJSON文字列に変換
    current_data_str = json.dumps(current_data, ensure_ascii=False, indent=2)
    new_data_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    # 履歴に追加（変更前後の全文も保存）
    add_history_entry(PERSONA_HISTORY_FILE, action, details, user_id,
                     content_before=current_data_str, content_after=new_data_str)

def get_character_by_id(character_id: str) -> Dict[str, str]:
    """
    指定されたIDのキャラクター設定を取得する関数
    
    引数:
        character_id: キャラクターID
    
    戻り値:
        キャラクター設定の辞書。見つからない場合はデフォルト設定
    """
    characters_data = load_aibot_characters()
    
    # 指定されたIDのキャラクターを検索
    for character in characters_data.get("characters", []):
        if character.get("id") == character_id:
            return character
    
    # 見つからない場合はデフォルト設定を返す
    return {
        "id": "default",
        "name": "AI助手",
        "personality": "親切で丁寧、少しユーモアのある性格",
        "speaking_style": "です・ます調で話します"
    }
