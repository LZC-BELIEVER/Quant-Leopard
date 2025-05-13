import pandas as pd
from finta import TA
from datetime import datetime
from autotrader.strategy import Strategy
import autotrader.indicators as indicators
from autotrader.brokers.trading import Order
from autotrader.brokers.broker import Broker
import time
import os


class BDWZ(Strategy):
    """BDWZ Strategy

    策略逻辑
    --------
    1. 做空条件：生命线为蓝
    2. 做多条件：生命线为红
    """

    def __init__(
        self, parameters: dict, instrument: str, broker: Broker, *args, **kwargs
    ) -> None:
        self.name = "BDWZ Strategy"
        self.params = parameters
        self.broker = broker
        self.instrument = instrument  # 品种
        self.duo_flag = False  # 多仓标志
        self.kong_flag = False  # 空仓标志
        self.duo_stopping = False  # 多仓止损
        self.kong_stopping = False  # 空仓止损
        self.duo_enter_point = 0  # 做多进场点
        self.kong_enter_point = 0  # 做空进场点

    def create_plotting_indicators(self, data: pd.DataFrame):
        # 构建用于绘图的指标
        ema_long, ema_medium, ema_short, life_line = self.generate_features(data)
        self.indicators = {
            "Life Line": {"type": "MA", "data": life_line},
            "EMA Long": {"type": "MA", "data": ema_long},
            "EMA Medium": {"type": "MA", "data": ema_medium},
            "EMA Short": {"type": "MA", "data": ema_short},
        }

    def generate_features(self, data: pd.DataFrame):
        if isinstance(data.index, pd.DatetimeIndex):
            data.index = data.index.tz_localize(None)

        data.columns = data.columns.get_level_values(0)

        if len(data) < 2*self.params["medium_ema_period"]:
            empty_series = pd.Series(dtype=float, index=data.index)
            return empty_series, empty_series, empty_series, empty_series

        ema_long = TA.EMA(data, self.params["long_ema_period"])
        ema_medium = TA.EMA(data, self.params["medium_ema_period"])
        ema_short = TA.EMA(data, self.params["short_ema_period"])

        #ema = ema_medium.to_frame()
        temp_df = pd.DataFrame({
            'close': ema_medium,
            'open': ema_medium,
            'high': ema_medium,  # 补充high
            'low': ema_medium  # 补充low
        })
        life = TA.EMA(temp_df, self.params["medium_ema_period"])
        life = life.squeeze()

        return ema_long, ema_medium, ema_short, life

    def generate_signal(self, dt: datetime):
        new_orders = []
        data = self.broker.get_candles(self.instrument, granularity="1min", count=30)
        data = data[::-1]
        print(data)

        if len(data) < self.params["medium_ema_period"]:
            print("数据不足!")
            return None

        ema_long, ema_medium, ema_short, life_line = self.generate_features(data)

        RED = life_line.iloc[-1] > life_line.iloc[-2]
        BLUE = life_line.iloc[-1] < life_line.iloc[-2]
        AA = ema_short.iloc[-1] > ema_long.iloc[-1]
        BB = ema_short.iloc[-1] < ema_long.iloc[-1]

        REDPLUS = life_line.iloc[-1] > life_line.iloc[-2] + 0.2
        BLUEPLUS = life_line.iloc[-1] < life_line.iloc[-2] - 0.2

        AAPLUS = ema_short.iloc[-1] > ema_long.iloc[-1] + 0.5
        BBPLUS = ema_short.iloc[-1] < ema_long.iloc[-1] - 0.5

        if self.kong_flag or self.duo_flag:
            new_orders.append(self.dynamic_stop())

        if AA and RED:
            if self.kong_stopping:
                self.kong_stopping = False
            if self.kong_flag:
                print("开始平空仓！！！！！！！！！！！")
                print("life_line.iloc[-1] > life_line.iloc[-2]",life_line.iloc[-1],life_line.iloc[-2])
                print("ema_short.iloc[-1] > ema_long.iloc[-1]", ema_short.iloc[-1], ema_long.iloc[-1])
                self.broker.api.sse_client.login('00123123')
                new_order = Order(
                    instrument=self.instrument,
                    direction=1,
                    china_exchange="SHFE",
                    china_direction=2,
                    offset=4,
                    price=0,
                    volume=1,
                    size=1,
                    stopPrice=0,
                    orderPriceType=2
                )
                new_orders.append(new_order)
                self.kong_flag = False
                self.kong_enter_point = 0
            if not self.duo_flag:
                if not self.duo_stopping:
                    if AAPLUS and REDPLUS:
                        print("开始做多！！！！！！！！！！！")
                        print("life_line.iloc[-1] > life_line.iloc[-2]",life_line.iloc[-1],life_line.iloc[-2])
                        print("ema_short.iloc[-1] > ema_long.iloc[-1]", ema_short.iloc[-1], ema_long.iloc[-1])
                        self.broker.api.sse_client.login('00123123')
                        temp = self.broker.get_candles(self.instrument, granularity="1s", count=1)
                        self.duo_enter_point = temp.iloc[0]['Close']
                        print("duo_enter_point:", self.duo_enter_point)
                        new_order = Order(
                            instrument=self.instrument,
                            direction=1,
                            china_exchange="SHFE",
                            china_direction=2,
                            offset=1,
                            price=0,
                            volume=1,
                            size=1,
                            stopPrice=0,
                            orderPriceType=2
                        )
                        new_orders.append(new_order)
                        self.duo_flag = True
            new_orders = [x for x in new_orders if x is not None]
            if len(new_orders) == 0:
                print("life_line.iloc[-1]  life_line.iloc[-2]", life_line.iloc[-1], life_line.iloc[-2])
                print("ema_short.iloc[-1]  ema_long.iloc[-1]", ema_short.iloc[-1], ema_long.iloc[-1])
                new_orders = None
        elif BB or BLUE:
            if self.duo_stopping:
                self.duo_stopping = False
            if self.duo_flag:
                print("开始平多仓！！！！！！！！！！！")
                print("life_line.iloc[-1] < life_line.iloc[-2]", life_line.iloc[-1], life_line.iloc[-2])
                print("ema_short.iloc[-1] < ema_long.iloc[-1]", ema_short.iloc[-1], ema_long.iloc[-1])
                self.broker.api.sse_client.login('00123123')
                # 做空信号
                new_order = Order(
                    instrument=self.instrument,
                    china_exchange="SHFE",
                    direction=1,
                    china_direction=3,
                    offset=4,
                    price=0,
                    volume=1,
                    size=1,
                    stopPrice=0,
                    orderPriceType=2
                )
                new_orders.append(new_order)
                self.duo_flag = False
                self.duo_enter_point = 0
            if not self.kong_flag:
                if not self.kong_stopping:
                    if BBPLUS and BLUEPLUS:
                        print("开始做空！！！！！！！！！！！")
                        print("life_line.iloc[-1] < life_line.iloc[-2]", life_line.iloc[-1], life_line.iloc[-2])
                        print("ema_short.iloc[-1] < ema_long.iloc[-1]", ema_short.iloc[-1], ema_long.iloc[-1])
                        self.broker.api.sse_client.login('00123123')
                        temp = self.broker.get_candles(self.instrument, granularity="1s", count=1)
                        self.kong_enter_point = temp.iloc[0]['Close']
                        print("kong_enter_point:", self.kong_enter_point)
                        # 做空信号
                        new_order = Order(
                            instrument=self.instrument,
                            china_exchange="SHFE",
                            direction=1,
                            china_direction=3,
                            offset=1,
                            price=0,
                            volume=1,
                            size=1,
                            stopPrice=0,
                            orderPriceType=2
                        )
                        new_orders.append(new_order)
                        self.kong_flag = True
            new_orders = [x for x in new_orders if x is not None]
            if len(new_orders) == 0:
                print("life_line.iloc[-1]  life_line.iloc[-2]", life_line.iloc[-1], life_line.iloc[-2])
                print("ema_short.iloc[-1]  ema_long.iloc[-1]", ema_short.iloc[-1], ema_long.iloc[-1])
                new_orders = None
        else:
            new_orders = [x for x in new_orders if x is not None]
            if len(new_orders) == 0:
                print("life_line.iloc[-1]  life_line.iloc[-2]", life_line.iloc[-1], life_line.iloc[-2])
                print("ema_short.iloc[-1]  ema_long.iloc[-1]", ema_short.iloc[-1], ema_long.iloc[-1])
                new_orders = None

        # print("new_orders", new_orders)
        return new_orders

    def dynamic_stop(self):
        candles = self.broker.get_candles(self.instrument, granularity="1s", count=30)
        data = candles['Close']
        new_order = None
        # 多仓动态止损
        if min(data) < self.duo_enter_point-4:
            if self.duo_flag:
                print("多仓止损")
                self.broker.api.sse_client.login('00123123')
                new_order = Order(
                    instrument=self.instrument,
                    china_exchange="SHFE",
                    direction=1,
                    china_direction=3,
                    offset=4,
                    price=0,
                    volume=1,
                    size=1,
                    stopPrice=0,
                    orderPriceType=2
                )
                self.duo_stopping = True
                self.duo_flag = False
                self.duo_enter_point = 0
        # 空仓动态止损
        if max(data) > self.kong_enter_point+4:
            if self.kong_flag:
                print("空仓止损")
                self.broker.api.sse_client.login('00123123')
                new_order = Order(
                    instrument=self.instrument,
                    direction=1,  # 无关参数
                    china_exchange="SHFE",
                    china_direction=2,
                    offset=4,
                    price=0,
                    volume=1,
                    size=1,  # 无关参数
                    stopPrice=0,
                    orderPriceType=2
                )
                self.kong_stopping = True
                self.kong_flag = False
                self.kong_enter_point = 0
        return new_order


