import os
import json
from typing import Dict, Any, Optional

# 設定ファイルのパス
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ai_provider_config.json")

def get_default_config() -> Dict[str, Any]:
    """
    デフォルトの設定を取得する関数
    
    戻り値:
        デフォルト設定を含む辞書
    """
    return {
        "current_provider": "grok",
        "providers": {
            "grok": {
                "name": "Grok",
                "description": "Grok AI (X.AI)",
                "default_model": "grok-3-latest",
                "vision_model": "grok-2-vision-latest"
            },
            "openai": {
                "name": "OpenAI",
                "description": "OpenAI GPT",
                "default_model": "gpt-4o",
                "vision_model": "gpt-4o"
            }
        }
    }

def load_config() -> Dict[str, Any]:
    """
    AI プロバイダーの設定を読み込む関数
    
    戻り値:
        設定情報を含む辞書
    """
    try:
        # 設定ファイルが存在するか確認
        if not os.path.exists(CONFIG_PATH):
            print(f"設定ファイルが存在しません: {CONFIG_PATH}")
            # デフォルト設定を作成して保存
            default_config = get_default_config()
            save_config(default_config)
            return default_config
        
        # 設定ファイルを読み込む
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"設定ファイルのJSONパースエラー: {str(e)}")
        # デフォルト設定を返す
        return get_default_config()
    except Exception as e:
        print(f"設定ファイルの読み込みエラー: {str(e)}")
        # デフォルト設定を返す
        return get_default_config()

def save_config(config: Dict[str, Any]) -> bool:
    """
    AI プロバイダーの設定を保存する関数
    
    引数:
        config: 保存する設定情報
    
    戻り値:
        保存に成功した場合はTrue、失敗した場合はFalse
    """
    try:
        # 設定ファイルのディレクトリが存在するか確認
        config_dir = os.path.dirname(CONFIG_PATH)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
            print(f"設定ファイルのディレクトリを作成しました: {config_dir}")
        
        # 設定ファイルを保存
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"設定ファイルの保存エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def get_current_provider() -> str:
    """
    現在選択されている AI プロバイダーを取得する関数
    
    戻り値:
        現在のプロバイダー名 ("grok" または "openai")
    """
    config = load_config()
    return config.get("current_provider", "grok")

def set_current_provider(provider: str) -> bool:
    """
    現在の AI プロバイダーを設定する関数
    
    引数:
        provider: 設定するプロバイダー名 ("grok" または "openai")
    
    戻り値:
        設定に成功した場合はTrue、失敗した場合はFalse
    """
    if provider not in ["grok", "openai"]:
        print(f"無効なプロバイダー名: {provider}")
        return False
    
    config = load_config()
    config["current_provider"] = provider
    return save_config(config)

def get_provider_info(provider: Optional[str] = None) -> Dict[str, Any]:
    """
    指定された AI プロバイダーの情報を取得する関数
    
    引数:
        provider: プロバイダー名 (省略時は現在のプロバイダー)
    
    戻り値:
        プロバイダー情報を含む辞書
    """
    config = load_config()
    
    if provider is None:
        provider = config.get("current_provider", "grok")
    
    providers = config.get("providers", {})
    return providers.get(provider, {})
