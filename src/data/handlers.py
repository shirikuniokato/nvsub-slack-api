import json
import os
from typing import Dict, Any, List

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
