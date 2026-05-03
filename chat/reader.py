# chat/reader.py
import asyncio
import os
import time
import random
from dotenv import load_dotenv
from chzzkpy import ChatClient
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

CHANNEL_ID  = os.getenv("CHZZK_CHANNEL_ID")
NID_AUT     = os.getenv("CHZZK_NID_AUT")
NID_SES     = os.getenv("CHZZK_NID_SES")
BASE_URL    = os.getenv("OLLAMA_BASE_URL")
THINK_MODEL = os.getenv("OLLAMA_THINK_MODEL")
EXPIRE_SEC  = 30
BUFFER_MAX  = 20

class ChzzkReader:
    def __init__(self, on_chat_callback, on_subscription_callback=None, topic: str = ""):
        self.callback              = on_chat_callback
        self.subscription_callback = on_subscription_callback
        self.buffer                = []
        self.is_busy               = False
        self.topic                 = topic
        self.llm                   = ChatOllama(model=THINK_MODEL, base_url=BASE_URL, temperature=0.1)
        self.client                = ChatClient(CHANNEL_ID)
        self.client.login(NID_AUT, NID_SES)

        @self.client.event
        async def on_connect():
            print("[치지직] 채팅 연결됨!")

        @self.client.event
        async def on_chat(message):
            nickname = message.profile.nickname if message.profile else "익명"
            content  = message.content
            if not content:
                return
            print(f"[채팅] {nickname}: {content}")
            if len(self.buffer) >= BUFFER_MAX:
                self.buffer.pop(0)
            self.buffer.append((nickname, content, time.time()))

        @self.client.event
        async def on_donation(message):
            nickname = message.profile.nickname if message.profile else "익명"
            amount   = message.extras.pay_amount if hasattr(message.extras, 'pay_amount') else 0
            content  = message.content or ""
            print(f"[도네] {nickname}: {amount}원 {content}")
            # 도네는 버퍼 맨 앞에 삽입 (우선처리)
            self.buffer.insert(0, (
                nickname,
                f"[도네 {amount}원] {content}" if content else f"[도네 {amount}원]",
                time.time()
            ))

        @self.client.event
        async def on_subscription(message):
            nickname = message.profile.nickname if message.profile else "익명"
            print(f"[구독] {nickname}")
            if self.subscription_callback:
                asyncio.create_task(self.subscription_callback(nickname, gift=False))

        @self.client.event
        async def on_subscription_gift(message):
            nickname = message.profile.nickname if message.profile else "익명"
            print(f"[구독 선물] {nickname}")
            if self.subscription_callback:
                asyncio.create_task(self.subscription_callback(nickname, gift=True))

    def _pick_by_topic_sync(self) -> tuple:
        candidates = self.buffer[-5:]
        chat_list = "\n".join(
            f"{i+1}. {nick}: {content}"
            for i, (nick, content, _) in enumerate(candidates)
        )
        system = SystemMessage(content="""You are a chat selector for a VTuber stream.
Given a list of chat messages and a topic, select the most relevant message number.
Respond with ONLY a single number. Nothing else.""")
        human = HumanMessage(content=f"""Topic: {self.topic}

Chat messages:
{chat_list}

Which message number is most relevant to the topic? Reply with just the number.""")
        response = self.llm.invoke([system, human])
        try:
            idx = int(response.content.strip()) - 1
            idx = max(0, min(idx, len(candidates) - 1))
            return candidates[idx]
        except:
            return random.choice(candidates)

    async def pick_and_respond(self):
        while True:
            await asyncio.sleep(0.5)

            if self.is_busy or not self.buffer:
                continue

            now = time.time()
            self.buffer = [
                item for item in self.buffer
                if now - item[2] <= EXPIRE_SEC
            ]

            if not self.buffer:
                continue

            loop = asyncio.get_event_loop()
            if self.topic and len(self.buffer) > 1:
                picked = await loop.run_in_executor(None, self._pick_by_topic_sync)
            else:
                picked = random.choice(self.buffer)

            self.buffer.clear()
            nickname, content, _ = picked
            print(f"[응답 중] {nickname}: {content}")

            self.is_busy = True
            asyncio.create_task(self._run_callback(nickname, content))

    async def _run_callback(self, nickname: str, content: str):
        try:
            await self.callback(nickname, content)
        finally:
            self.is_busy = False

    async def start(self):
        asyncio.create_task(self.pick_and_respond())
        await self.client.connect()