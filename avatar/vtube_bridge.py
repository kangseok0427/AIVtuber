# avatar/vtube_bridge.py
import asyncio
import websockets
import json

VTUBE_WS_URL = "ws://localhost:8001"
PLUGIN_NAME  = "GaonAI"
PLUGIN_DEV   = "Gaon"

class VTubeBridge:
    def __init__(self):
        self.ws          = None
        self.auth_token  = None

    async def connect(self):
        self.ws = await websockets.connect(VTUBE_WS_URL)
        await self._authenticate()
        print("[VTube] 연결 완료!")

    async def _send(self, payload: dict) -> dict:
        await self.ws.send(json.dumps(payload))
        resp = await self.ws.recv()
        return json.loads(resp)

    async def _authenticate(self):
        # 1단계 — 토큰 요청
        resp = await self._send({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "auth_req",
            "messageType": "AuthenticationTokenRequest",
            "data": {
                "pluginName": PLUGIN_NAME,
                "pluginDeveloper": PLUGIN_DEV
            }
        })
        self.auth_token = resp["data"]["authenticationToken"]

        # 2단계 — 토큰으로 인증
        await self._send({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "auth",
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": PLUGIN_NAME,
                "pluginDeveloper": PLUGIN_DEV,
                "authenticationToken": self.auth_token
            }
        })

    async def set_expression(self, expression_name: str | None):
        if not expression_name:
            return

        # 예: "Exp7 Laugh" → "Exp7 Laugh.exp3.json"
        file_name = f"{expression_name}.exp3.json"
        print(f"[VTube] 표정 시도: {file_name}")

        resp = await self._send({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "expr",
            "messageType": "ExpressionActivationRequest",
            "data": {
                "expressionFile": file_name,
                "active": True
            }
        })
        print(f"[VTube] 응답: {resp}")

    async def reset_expression(self, expression_name: str | None):
        """표정 초기화 (일정 시간 후 원래대로)"""
        if not expression_name:
            return

        await self._send({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "expr_reset",
            "messageType": "ExpressionActivationRequest",
            "data": {
                "expressionFile": f"{expression_name}.exp3.json",
                "active": False
            }
        })

    async def trigger_and_reset(self, expression_name: str | None, duration: float = 3.0):
        """표정 켜고 duration초 후 자동 리셋"""
        await self.set_expression(expression_name)
        await asyncio.sleep(duration)
        await self.reset_expression(expression_name)

    async def disconnect(self):
        if self.ws:
            await self.ws.close()