#!/bin/bash

# デフォルト値の設定
MODE="production"

# 引数の解析
for arg in "$@"
do
    case $arg in
        --dev)
        MODE="development"
        shift
        ;;
        --prod)
        MODE="production"
        shift
        ;;
        *)
        # 不明なオプション
        echo "不明なオプション: $arg"
        echo "使用方法: $0 [--dev|--prod]"
        exit 1
        ;;
    esac
done

# モードが指定されていない場合のエラー処理
if [ -z "$MODE" ]; then
    echo "エラー: モードが指定されていません。"
    echo "使用方法: $0 [--dev|--prod]"
    exit 1
fi

# 開発モードの処理
if [ "$MODE" = "development" ]; then
    echo "開発モードでアプリケーションを起動します..."
    echo "仮想環境をアクティベートします..."
    source ../../venv/bin/activate
    cd ..
    # 開発モード用のコマンド
    uvicorn main:app --reload
fi

# 本番モードの処理
if [ "$MODE" = "production" ]; then
    echo "本番モードでアプリケーションを起動します..."
    # 本番モード用のコマンド
    sudo systemctl daemon-reload
    sudo systemctl restart nginx
    sudo systemctl restart slack-api
    sudo systemctl status slack-api
fi

exit 0
