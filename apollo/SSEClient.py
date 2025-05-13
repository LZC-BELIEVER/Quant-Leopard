import asyncio
import aiohttp
from aiohttp_sse_client import client as sse_client
import json
import requests
import time
import sys,os


class SSEClient:
    def __init__(self, base_url="https://www.quantum-hedge.com", license_key=''):
        """
        初始化交易客户端
        :param base_url: API基础地址
        :param license_key: 许可证密钥
        """
        self.base_url = base_url
        self.license_key = license_key
        self.is_connected = False
        self.is_logged_in = False
        self.is_ready = False
        self.asy_session = None
        self.syn_session = requests.Session()
        self.syn_session.headers.update({
            'license': license_key
        })
        self.user_id = None
        self.fc_code = None
        self.password = None
        self.is_mkt_open = True
        self._loop = asyncio.get_event_loop()

        self.order_conditions = {}

    async def connect_sse(self, fc_code, user_id):
        """
        连接SSE交易通道
        :param fc_code: 柜台代码
        :param user_id: 用户ID
        """
        if self.is_connected:
            print("SSE连接已存在，无需重复连接")
            return True

        url = f"{self.base_url}/apollo-trade/sse/tdConnect?fcCode={fc_code}&userId={user_id}"

        try:
            self.asy_session = aiohttp.ClientSession(
                headers={
                    'license': self.license_key  # 使用传入的 license_key
                }
            )
            self.event_source = await sse_client.EventSource(
                url,
                session=self.asy_session,
                headers={
                    'Content-Type': 'text/event-stream',
                    'Accept': 'text/event-stream',
                    'license': self.license_key  # 使用传入的 license_key
                }
                # timeout=10
            ).__aenter__()

            self.user_id = user_id
            self.fc_code = fc_code

            # 启动事件监听任务
            self.receive_task = asyncio.create_task(self._listen_events())
            return True

        except Exception as e:
            print(f"SSE连接失败: {e}")
            await self._cleanup()
            return False

    async def _listen_events(self):
        """监听服务器推送事件"""
        try:
            print("listening")
            async for event in self.event_source:
                print("event", event)

                # 跳过连接确认/心跳等非业务事件
                if event.type == 'sseTdConnected':
                    self.is_connected = True
                    print(f"SSE连接确认: {event.data}")
                    continue
                if event.type == 'logged_in':
                    self.is_logged_in = True
                    print(f"登陆成功: {event.data}")
                if event.type == "ready":
                    self.is_ready = True
                    print(f"结算单已确认，可以开始交易:{event.data}")
                if event.type == "isMarketOpen":
                    self.is_mkt_open = False
                    print(f"现在{event.data}交易时间")
                if event.type == "trade":
                    print("成交单回报:", event.data)
                    print("已成交单号", event.dara.originOrderId)
                    
                # 只处理业务事件
                if event.type in ('logged_out', 'order', 'trade', 'excption'):
                    try:
                        data = json.loads(event.data) if event.data else {}
                        print(f"收到业务事件: {event.type} - {data}")

                        if event.type == "logged_out":
                            self.is_logged_in = False
                            print("退出成功")
                        elif event.type == "order":
                            print("委托单回报:", data)

                    except json.JSONDecodeError:
                        print(f"非JSON格式的业务数据: {event.data}")
                    except Exception as e:
                        print(f"处理业务事件时出错: {e}")

        except Exception as e:
            print(f"事件监听错误: {e['characters_written']}")
            await self._cleanup()

    '''async def _check_connected(self):
        # 等待连接状态稳定
        await asyncio.sleep(0.1)
        return self.is_connected'''

    def login(self, password):
        """
        交易账号登录
        :param password: 交易密码
        """
        if not self.is_connected:
            raise Exception("请先建立SSE连接")
        '''if not self._loop.run_until_complete(self._check_connected()):
            raise Exception("请先建立SSE连接")'''
        if self.is_ready:
            print("账号已登录，无需重复登录")
            return True

        print("准备登录")
        url = f"{self.base_url}/apollo-trade/api/v1/td/login"
        data = {
            "userId": self.user_id,
            "password": password,
            "fcCode": self.fc_code
        }

        try:
            self.password = password
            resp = self.syn_session.post(
                url,
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'license': self.license_key
                },
                timeout=10
            )
            result = resp.json()
            if result.get('code') == 0:
                print("登录请求已发送，等待登录结果...")
                return True
            else:
                print(f"登录失败: {result.get('message')}")
                return False
        except Exception as e:
            print(f"登录请求出错: {e}")
            return False

    def send_order(self, symbol, exchange, direction, offset, price, volume, stopPrice, orderPriceType):
        """
        期货下单（同步）
        """
        if not self.is_ready:
            raise Exception("未登录")

        url = f"{self.base_url}/apollo-trade/api/v1/td/submitOrder"
        data = {
            "userId": self.user_id,
            "password": self.password,
            "fcCode": self.fc_code,
            "symbol": symbol,
            "exchange": exchange,
            "direction": direction,
            "offset": offset,
            "price": price,
            "volume": volume,
            "stopPrice": stopPrice,
            "orderPriceType": orderPriceType
        }

        try:
            resp = self.syn_session.post(
                url,
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'license': self.license_key
                },
                timeout=10
            )
            result = resp.json()
            if result.get('code') == 0:
                print(f"下单成功，本地单号: {result.get('data')}")
                order_number = result.get('data')
                self.order_conditions[order_number] = 0
                return result.get('data')
            else:
                print(f"下单失败: {result.get('message')}")
                return None
        except Exception as e:
            print(f"下单请求出错: {e}")
            return None

    def get_data(self, symbol, candlenums, period):
        """
        期货下单（同步）
        """
        if not self.is_ready:
            print("离线模式数据")
        else:
            print("在线模式数据")

        url = f"{self.base_url}/apollo-market/api/v1/futureData/queryData"
        data = {
            "symbol": symbol,
            "candleNums": candlenums,
            "period": period,
        }

        try:
            start_time = time.time()  # 记录请求开始时间

            resp = self.syn_session.post(
                url,
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'license': self.license_key
                },
                timeout=10
            )

            elapsed_time = time.time() - start_time  # 计算耗时
            print(f"请求耗时: {elapsed_time:.3f}秒")  # 打印时延，保留3位小数

            result = resp.json()
            if result.get('code') == 0:
                print(f"获取数据成功")
                return result.get('data')
            else:
                print(f"获取数据失败: {result.get('message')}")
                return None
        except Exception as e:
            print(f"获取数据请求出错: {e}")
            return None

    def get_position(self, symbol):
        """
        获取仓位信息（同步）
        """
        if not self.is_connected:
            raise Exception("未连接,不能获取仓位信息")

        url = f"{self.base_url}/apollo-trade/api/v1/account/queryPosition"
        data = {
            "symbol": symbol,
            "fcCode": self.fc_code,
            "userId": self.user_id
        }

        try:
            resp = self.syn_session.post(
                url,
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'license': self.license_key
                },
                timeout=20
            )
            result = resp.json()
            if result.get('code') == 0:
                print(f"获取数据成功")
                return result.get('data')
            else:
                print(f"获取数据失败: {result.get('message')}")
                return None
        except Exception as e:
            print(f"获取数据请求出错: {e}")
            return None

    def logout(self):
        """交易账号退出登录（同步）"""
        if not self.is_ready:
            print("账号未登录，无需退出")
            return True

        url = f"{self.base_url}/apollo-trade/api/v1/td/logout"
        data = {
            "userId": self.user_id,
            "password": self.password,
            "fcCode": self.fc_code
        }

        try:
            resp = self.syn_session.post(
                url,
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'license': self.license_key
                },
                # timeout=10
            )
            result = resp.json()
            if result.get('code') == 0:
                print("退出请求已发送，等待退出结果...")
                self.is_ready = False
                return True
            else:
                print(f"退出失败: {result.get('message')}")
                return False
        except Exception as e:
            print(f"退出请求出错: {e}")
            return False

    def cancel_order(self, order_id):
        """
        撤单（同步）
        """
        if not self.is_ready:
            raise Exception("请先登录交易账号")

        url = f"{self.base_url}/apollo-trade/api/v1/td/cancelOrder"
        data = {
            "userId": self.user_id,
            "password": self.password,
            "fcCode": self.fc_code,
            "originOrderId": order_id
        }

        try:
            resp = self.syn_session.post(
                url,
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'license': self.license_key
                },
                timeout=10
            )
            result = resp.json()
            if result.get('code') == 0:
                print("撤单请求已发送")
                return True
            else:
                print(f"撤单失败: {result.get('message')}")
                return False
        except Exception as e:
            print(f"撤单请求出错: {e}")
            return False

    async def disconnect(self):
        """断开SSE连接"""
        if not self.is_connected:
            print("SSE连接不存在，无需断开")
            return True

        # 先退出登录
        if self.is_ready:
            self.logout()
            # 等待退出完成
            await asyncio.sleep(1)

        await self._cleanup()
        print("SSE连接已断开")
        return True

    async def _cleanup(self):
        """清理资源"""
        try:
            print("开始清理资源")
            if hasattr(self, 'receive_task'):
                self.receive_task.cancel()
                try:
                    await self.receive_task
                except asyncio.CancelledError:
                    pass

            if hasattr(self, 'event_source'):
                await self.event_source.__aexit__(None, None, None)

            if self.asy_session:
                await self.asy_session.close()

        except Exception as e:
            print(f"清理资源时出错: {e}")

        finally:
            self.is_connected = False
            self.is_ready = False
            self.asy_session = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect()