import hashlib
import hmac
import time
import os
from fastapi import Request, HTTPException, Depends
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI
from starlette.responses import JSONResponse

# Slackの署名検証シークレット（環境変数から取得する）
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

class SlackVerificationMiddleware(BaseHTTPMiddleware):
    """
    Slackからのリクエストを検証するミドルウェア
    """
    async def dispatch(self, request: Request, call_next):
        # Slackの署名検証が必要なパスのみ検証
        if request.url.path in ["/superchat", "/events"]:
            # リクエストヘッダーからSlackの署名と時間を取得
            slack_signature = request.headers.get("X-Slack-Signature")
            slack_timestamp = request.headers.get("X-Slack-Request-Timestamp")
            
            # ヘッダーが存在しない場合はエラー
            if not slack_signature or not slack_timestamp:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Slack署名が見つかりません"}
                )
            
            # タイムスタンプが古すぎる場合はリプレイ攻撃の可能性があるため拒否
            # 5分以上前のリクエストは拒否
            if abs(time.time() - int(slack_timestamp)) > 60 * 5:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "リクエストが古すぎます"}
                )
            
            try:
                # リクエストボディをキャッシュ
                body = await request.body()
                
                # リクエストボディを再設定（後続の処理でも使用できるようにする）
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
                
                # 署名の計算
                # 署名の形式: v0=<署名>
                # 署名の計算方法: HMAC SHA256(signing_secret, "v0:" + timestamp + ":" + body)
                sig_basestring = f"v0:{slack_timestamp}:{body.decode()}"
                my_signature = "v0=" + hmac.new(
                    SLACK_SIGNING_SECRET.encode(),
                    sig_basestring.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                # 署名の検証
                if not hmac.compare_digest(my_signature, slack_signature):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "署名が一致しません"}
                    )
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={"detail": f"検証エラー: {str(e)}"}
                )
        
        # 次のミドルウェアまたはエンドポイントを呼び出す
        response = await call_next(request)
        return response

def add_slack_verification_middleware(app: FastAPI):
    """
    FastAPIアプリケーションにSlack検証ミドルウェアを追加する関数
    
    引数:
        app: FastAPIアプリケーションインスタンス
    """
    app.add_middleware(SlackVerificationMiddleware)
