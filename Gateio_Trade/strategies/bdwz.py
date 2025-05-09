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
        '''
        某些计算
        '''
        return ema_long, ema_medium, ema_short, life

    def generate_signal(self, dt: datetime):
        ema_long, ema_medium, ema_short, life_line = self.generate_features(data)
        '''
        结合generate_features产生交易信号，按照下单规范下单
        '''
        return new_orders

    def dynamic_stop(self):
        '''
        止损机制
        '''
        return new_order


