# chat/reader.py
import asyncio
import os
from dotenv import load_dotenv
from chzzkpy import ChatClient

load_dotenv()

CHANNEL_ID = os.getenv("CHZZK_CHANNEL_ID")
NID_AUT    = os.getenv("CHZZK_NID_AUT")
NID_SES    = os.getenv("CHZZK_NID_SES")

class ChzzkReader:
    def __init__(self, on_chat_callback):
        self.callback = on_chat_callback
        self.client = ChatClient(CHANNEL_ID)
        self.client.login(NID_AUT, NID_SES)

        @self.client.event
        async def on_connect():
            print("[치지직] 채팅 연결됨!")

        @self.client.event
        async def on_chat(message):
            nickname = message.profile.nickname if message.profile else "익명"
            content = message.content
            if content:
                print(f"[채팅] {nickname}: {content}")
                await self.callback(nickname, content)

    async def start(self):
        await self.client.connect()