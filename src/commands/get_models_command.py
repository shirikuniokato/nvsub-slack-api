from fastapi import Form
from typing import Dict, Any, Optional, List
import os
from openai import OpenAI
import asyncio
from anthropic import Anthropic

async def get_openai_models() -> List[str]:
    """
    OpenAI APIから利用可能なモデルの一覧を取得する関数
    
    戻り値:
        利用可能なモデルのリスト
    """
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return ["APIキーが設定されていません"]
        
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        
        # モデル名のリストを取得
        model_names = [model.id for model in models.data]
        
        # GPTモデルのみをフィルタリング
        gpt_models = [name for name in model_names if "gpt" in name.lower()]
        
        return sorted(gpt_models)
    except Exception as e:
        print(f"OpenAIモデル取得エラー: {str(e)}")
        return [f"エラー: {str(e)}"]

async def get_claude_models() -> List[str]:
    """
    Anthropic APIから利用可能なモデルの一覧を取得する関数
    
    戻り値:
        利用可能なモデルのリスト
    """
    try:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return ["APIキーが設定されていません"]
        
        # Anthropicクライアントの初期化
        client = Anthropic()
        
        # モデル一覧を取得
        models = client.models.list()
        
        # モデル名のリストを取得
        model_names = [model.id for model in models.data]
        
        # Claudeモデルのみをフィルタリング（不要かもしれませんが念のため）
        claude_models = [name for name in model_names if "claude" in name.lower()]
        
        return sorted(claude_models)
    except Exception as e:
        print(f"Claudeモデル取得エラー: {str(e)}")
        return [f"エラー: {str(e)}"]

async def get_grok_models() -> List[str]:
    """
    Grok APIから利用可能なモデルの一覧を取得する関数
    
    戻り値:
        利用可能なモデルのリスト
    """
    try:
        api_key = os.environ.get("GROK_API_KEY")
        api_base = os.environ.get("GROK_API_BASE_URL", "https://api.x.ai/v1")
        
        if not api_key:
            return ["APIキーが設定されていません"]
        
        client = OpenAI(api_key=api_key, base_url=api_base)
        models = client.models.list()
        
        # モデル名のリストを取得
        model_names = [model.id for model in models.data]
        
        # Grokモデルのみをフィルタリング
        grok_models = [name for name in model_names if "grok" in name.lower()]
        
        return sorted(grok_models)
    except Exception as e:
        print(f"Grokモデル取得エラー: {str(e)}")
        return [f"エラー: {str(e)}"]

async def get_available_models(provider: str = None) -> Dict[str, List[str]]:
    """
    指定されたAIプロバイダーで利用可能なモデルの一覧を取得する関数
    
    引数:
        provider: プロバイダー名 ("grok", "openai", または "claude")
    
    戻り値:
        プロバイダーごとのモデル一覧を含む辞書
    """
    result = {}
    
    if provider is None or provider == "openai":
        result["openai"] = await get_openai_models()
    
    if provider is None or provider == "claude":
        result["claude"] = await get_claude_models()
    
    if provider is None or provider == "grok":
        result["grok"] = await get_grok_models()
    
    return result

async def get_models_command(
    text: str = Form(""),
    user_id: str = Form(""),
    team_id: str = Form(""),
    channel_id: str = Form(""),
):
    """
    AIプロバイダーで利用可能なモデルの一覧を取得するスラッシュコマンド
    
    使用方法:
    /get-models            - すべてのプロバイダーのモデル一覧を表示
    /get-models -s grok    - Grokのモデル一覧を表示
    /get-models -s openai  - OpenAIのモデル一覧を表示
    /get-models -s claude  - Claudeのモデル一覧を表示
    /get-models -h         - ヘルプを表示
    
    引数:
        text: コマンドテキスト
        user_id: コマンドを実行したユーザーID
        team_id: チームID
        channel_id: チャンネルID
    
    戻り値:
        Slack応答フォーマットのJSON
    """
    try:
        # コマンドテキストを整形
        text = text.strip()
        
        # コマンドの引数を解析
        args = text.split()
        
        # ヘルプを表示
        if "-h" in args or "--help" in args:
            return {
                "response_type": "ephemeral",
                "text": "AIプロバイダーのモデル一覧取得コマンド\n\n"
                        "使用方法:\n"
                        "`/get-models` - すべてのプロバイダーのモデル一覧を表示\n"
                        "`/get-models -s grok` - Grokのモデル一覧を表示\n"
                        "`/get-models -s openai` - OpenAIのモデル一覧を表示\n"
                        "`/get-models -s claude` - Claudeのモデル一覧を表示\n"
                        "`/get-models -h` - このヘルプを表示"
            }
        
        # プロバイダーを指定
        provider = None
        if "-s" in args or "--set" in args:
            set_index = args.index("-s" if "-s" in args else "--set")
            
            # 次の引数がプロバイダー名
            if len(args) > set_index + 1:
                provider = args[set_index + 1].lower()
                
                if provider not in ["grok", "openai", "claude"]:
                    return {
                        "response_type": "ephemeral",
                        "text": f"エラー: 無効なプロバイダー名 '{provider}'\n"
                                "有効なプロバイダー: grok, openai, claude"
                    }
        
        # モデル一覧を取得
        models_dict = await get_available_models(provider)
        
        # 指定されたプロバイダーのモデル一覧を表示
        if provider:
            provider_name = {
                "grok": "Grok",
                "openai": "OpenAI",
                "claude": "Claude"
            }.get(provider, provider.capitalize())
            
            models = models_dict.get(provider, [])
            
            response_text = f"*{provider_name}* で利用可能なモデル:\n\n"
            
            if models:
                for model in models:
                    response_text += f"• {model}\n"
            else:
                response_text += "利用可能なモデルはありません。\n"
            
            return {
                "response_type": "ephemeral",
                "text": response_text
            }
        
        # すべてのプロバイダーのモデル一覧を表示
        else:
            response_text = "*利用可能なAIモデル一覧:*\n\n"
            
            for provider, models in models_dict.items():
                provider_name = {
                    "grok": "Grok",
                    "openai": "OpenAI",
                    "claude": "Claude"
                }.get(provider, provider.capitalize())
                
                response_text += f"*{provider_name}:*\n"
                
                if models:
                    for model in models:
                        response_text += f"• {model}\n"
                else:
                    response_text += "利用可能なモデルはありません。\n"
                
                response_text += "\n"
            
            return {
                "response_type": "ephemeral",
                "text": response_text
            }
    
    except Exception as e:
        print(f"Error in get_models_command: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "response_type": "ephemeral",
            "text": f"エラーが発生しました: {str(e)}"
        }
