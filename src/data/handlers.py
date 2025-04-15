import json
import os
from typing import Dict, Any, List

# ファイルパス
SUPERCHAT_DATA_FILE = "./data/superchat_data.json"
USER_DISPLAY_NAME_FILE = "./data/user_display_names.json"
AIBOT_CHARACTERS_FILE = "./data/aibot_characters.json"

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

def save_aibot_characters(data: Dict[str, Any]) -> None:
    """
    AIボットのキャラクター設定を保存する関数
    
    引数:
        data: キャラクター設定の辞書
    """
    with open(AIBOT_CHARACTERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
