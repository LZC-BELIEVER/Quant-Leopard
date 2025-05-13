import asyncio
import threading
from apollo.SSEClient import SSEClient
from apollo import instrument
from apollo import order
import time
import sys

class Context:
    """
    apollo interface provides connection to China's products
    author: LZC
    """
    def __init__(self, lisence="s3az29vbx5w3", fc_code="rh", user_id="202500100", password="00123123"):
        self.lisence = lisence
        self.fc_code = fc_code
        self.user_id = user_id
        self.password = password
        self.sse_client = None

        # 子模块接口
        self.instrument = instrument.EntitySpec(self)
        self.order = order.EntitySpec(self)

        #asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self._loop = asyncio.new_event_loop()
        self._stop_event = asyncio.Event()

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        for _ in range(200):
            if self.sse_client:
                if self.sse_client.is_ready:
                    break
            time.sleep(0.1)
        else:
            raise ValueError("连接与登录初始化超时")

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._start_connection())

    def stop(self):
        self._loop.call_soon_threadsafe(self._stop_event.set)
        self._thread.join()
        print("同步登出完成")

    async def _start_connection(self):
        async with SSEClient(license_key=self.lisence) as client:
            if not await client.connect_sse(self.fc_code, self.user_id):
                print("连接 SSE 失败")
                return

            for _ in range(50):
                if client.is_connected:
                    break
                await asyncio.sleep(0.1)
            else:
                print("SSE连接超时")
                return

            self.sse_client = client

            loop = asyncio.get_running_loop()
            login_success = await loop.run_in_executor(None, client.login, self.password)
            if not login_success:
                print("登录失败")
                return

            for _ in range(50):
                if client.is_ready:
                    break
                await asyncio.sleep(0.1)
            else:
                print("登录等待超时")
                return
            print("SSE 登录成功")

            self._keepalive_task = asyncio.create_task(self._keep_alive())
            await self._stop_event.wait()
            print("收到停止信号，断开连接")

    async def _keep_alive(self):
        while not self._stop_event.is_set():
            await asyncio.sleep(1)

    '''def reconnect_if_needed(self):
        """
        同步方法：
        如果 sse_client 为空 或 未登录，重新启动连接线程
        """
        if self.sse_client is not None and self.sse_client.is_logged_in:
            print("已连接且已登录，无需重连。")
            return

        print("连接状态异常，准备重连...")

        # 先停止现有连接
        if self._thread.is_alive():
            self._loop.call_soon_threadsafe(self._stop_event.set)
            self._thread.join()

        # 重置停止事件
        self._stop_event = asyncio.Event()

        # 启动新线程重新连接
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print("重连请求已发起。")'''
