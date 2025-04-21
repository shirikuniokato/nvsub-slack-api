from fastapi import Form
from typing import Dict, Any, Optional
from utils.slack_api import post_message
from utils.ai_provider import get_current_provider, set_current_provider, get_provider_info, set_model

async def nai_command(
    text: str = Form(""),
    user_id: str = Form(""),
    team_id: str = Form(""),
    channel_id: str = Form(""),
):
    """
    野良猫AIプロバイダーを管理するスラッシュコマンド
    
    使用方法:
    /nai                  - 現在のプロバイダーを表示
    /nai -s grok          - プロバイダーをGrokに設定
    /nai -s openai        - プロバイダーをOpenAIに設定
    /nai -m gpt-4o        - 現在のプロバイダーのモデルを設定
    /nai -m gpt-4o -t vision - 現在のプロバイダーのビジョンモデルを設定
    /nai -h               - ヘルプを表示
    
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
                "text": "野良猫AIプロバイダー管理コマンド\n\n"
                        "使用方法:\n"
                        "`/nai` - 現在のプロバイダーを表示\n"
                        "`/nai -s grok` - プロバイダーをGrokに設定\n"
                        "`/nai -s openai` - プロバイダーをOpenAIに設定\n"
                        "`/nai -s claude` - プロバイダーをClaudeに設定\n"
                        "`/nai -s gemini` - プロバイダーをGeminiに設定\n"
                        "`/nai -m gpt-4o` - 現在のプロバイダーのモデルを設定\n"
                        "`/nai -m gpt-4o -t vision` - 現在のプロバイダーのビジョンモデルを設定\n"
                        "`/nai -h` - このヘルプを表示"
            }
        
        # モデルを設定
        if "-m" in args or "--model" in args:
            model_index = args.index("-m" if "-m" in args else "--model")
            
            # 次の引数がモデル名
            if len(args) > model_index + 1:
                model = args[model_index + 1]
                
                # モデルタイプを確認（デフォルトは "default"）
                model_type = "default"
                if "-t" in args or "--type" in args:
                    type_index = args.index("-t" if "-t" in args else "--type")
                    if len(args) > type_index + 1:
                        model_type = args[type_index + 1].lower()
                        
                        if model_type not in ["default", "vision"]:
                            return {
                                "response_type": "ephemeral",
                                "text": f"エラー: 無効なモデルタイプ '{model_type}'\n"
                                        "有効なモデルタイプ: default, vision"
                            }
                
                # 現在のプロバイダーを取得
                provider = get_current_provider()
                
                # モデルを設定
                success = set_model(provider, model, model_type)
                
                if success:
                    provider_info = get_provider_info(provider)
                    provider_name = provider_info.get("name", provider.capitalize())
                    model_type_name = "デフォルト" if model_type == "default" else "ビジョン"
                    
                    return {
                        "response_type": "in_channel",
                        "text": f"野良猫AI *{provider_name}* の{model_type_name}モデルを *{model}* に変更しました。"
                    }
                else:
                    return {
                        "response_type": "ephemeral",
                        "text": "エラー: モデルの変更に失敗しました。"
                    }
            else:
                return {
                    "response_type": "ephemeral",
                    "text": "エラー: -m オプションにはモデル名が必要です。\n"
                            "例: `/nai -m gpt-4o`"
                }
        
        # プロバイダーを設定
        if "-s" in args or "--set" in args:
            set_index = args.index("-s" if "-s" in args else "--set")
            
            # 次の引数がプロバイダー名
            if len(args) > set_index + 1:
                provider = args[set_index + 1].lower()
                
                if provider not in ["grok", "openai", "claude", "gemini"]:
                    return {
                        "response_type": "ephemeral",
                        "text": f"エラー: 無効なプロバイダー名 '{provider}'\n"
                                "有効なプロバイダー: grok, openai, claude, gemini"
                    }
                
                # プロバイダーを設定
                success = set_current_provider(provider)
                
                if success:
                    provider_info = get_provider_info(provider)
                    provider_name = provider_info.get("name", provider.capitalize())
                    
                    return {
                        "response_type": "in_channel",
                        "text": f"野良猫AIプロバイダーを *{provider_name}* に変更しました。"
                    }
                else:
                    return {
                        "response_type": "ephemeral",
                        "text": "エラー: AIプロバイダーの変更に失敗しました。"
                    }
            else:
                return {
                    "response_type": "ephemeral",
                    "text": "エラー: -s オプションにはプロバイダー名が必要です。\n"
                            "例: `/nai -s grok`"
                }
        
        # 引数がない場合は現在のプロバイダーを表示
        current_provider = get_current_provider()
        provider_info = get_provider_info(current_provider)
        provider_name = provider_info.get("name", current_provider.capitalize())
        provider_desc = provider_info.get("description", "")
        default_model = provider_info.get("default_model", "")
        vision_model = provider_info.get("vision_model", "")
        
        return {
            "response_type": "in_channel",
            "text": f"現在の野良猫AIプロバイダー: *{provider_name}* ({provider_desc})\n"
                    f"使用モデル: {default_model}\n"
                    f"使用モデル(画像解析): {vision_model}\n\n"
                    "プロバイダーを変更するには:\n"
                    "`/nai -s grok` または `/nai -s openai` または `/nai -s claude` または `/nai -s gemini`\n\n"
                    "モデルを変更するには:\n"
                    "`/nai -m <モデル名>` または `/nai -m <モデル名> -t vision`"
        }
    
    except Exception as e:
        print(f"Error in nai_command: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "response_type": "ephemeral",
            "text": f"エラーが発生しました: {str(e)}"
        }
