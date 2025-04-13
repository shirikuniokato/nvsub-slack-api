from data.handlers import load_user_display_names, save_user_display_names

def get_display_name(user_id: str, user_name: str, display_name: str = None) -> str:
    """
    ユーザーの表示名を取得する関数
    
    引数:
        user_id: ユーザーID
        user_name: ユーザー名
        display_name: 表示名（設定されていない場合はNone）
    
    戻り値:
        表示名
    """
    # マッピングを読み込む
    user_display_names = load_user_display_names()
    
    # 表示名が指定されている場合は、マッピングを更新して返す
    if display_name:
        user_display_names[user_id] = display_name
        save_user_display_names(user_display_names)
        return display_name
    
    # マッピングに存在する場合は、マッピングから取得
    if user_id in user_display_names:
        return user_display_names[user_id]
    
    # マッピングに存在しない場合は、ユーザー名を返す
    return user_name
