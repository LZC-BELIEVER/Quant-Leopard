import os
import pickle
import importlib
import traceback
import numpy as np
import pandas as pd
from decimal import Decimal
from typing import Callable, Union
from datetime import datetime, timezone
from autotrader.utilities import get_logger
import apollo
from autotrader.brokers.broker import AbstractBroker,Broker
from autotrader.brokers.trading import Order, Position, Trade, OrderBook


class Broker(Broker):
    def __init__(self, config: dict):
        print("config:",config)

        global_config=config["quantumhedge"]
        #self.lisence = global_config["LISENCE"]
        self.lisence = "s3az29vbx5w3"

        # Assign data broker
        self.data_broker = self
        self._positions: dict[str, Position] = {}
        self._allow_dancing_bears=False

        self.api = apollo.Context(
            lisence=self.lisence
        )
        self.account_id=""
        self.password=""
        self.long_position = 0
        self.short_position = 0

    def __repr__(self):
        return "AutoTrader-QuatumHedge Broker Interface"

    def __str__(self):
        return "AutoTrader-QuatumHedge Broker Interface"

    def data_broker(self):
        return self.data_broker

    #def configure(self, *args, **kwargs):
        """Generic configure method, placeholder for typehinting. Only required
        for the virtual broker."""

    def _check_connection(self) -> None:
        return True

    def get_NAV(self, *args, **kwargs) -> float:
        #get_nav_interface
        pass

    def get_balance(self, *args, **kwargs) -> float:
        # get_balance_interface
        pass

    def place_order(self, order: Order, **kwargs):
        """Submits order to broker."""
        self._check_connection()

        # Call order to set order time
        #order()
        # Submit order
        if order.order_type == "market":
            response = self._place_market_order(order)
        else:
            print("Order type not recognised.")
        '''elif order.order_type == "stop-limit":
            response = self._place_stop_limit_order(order)
        elif order.order_type == "limit":
            response = self._place_limit_order(order)
        elif order.order_type == "close":
            response = self._close_position(order.instrument)
        elif order.order_type == "modify":
            response = self._modify_trade(order)
        else:
            print("Order type not recognised.")'''

        # Check response
        # output = self._check_response(response)

        return response

    def get_orders(self, instrument=None, **kwargs) -> dict:
        pass

    def cancel_order(self, order_id: int, *args, **kwargs) -> None:
        #API->cancel_order
        pass

    def get_trades(self, instrument: str = None, *args, **kwargs) -> dict:
        pass

    def get_candles(
            self,
            instrument: str,
            granularity: str = None,
            count: int = None,
            start_time: datetime = None,
            end_time: datetime = None,
            *args,
            **kwargs,
    ) -> pd.DataFrame:

        '''gran_map = {
            5: "S5",
            10: "S10"
        }
        granularity = gran_map[pd.Timedelta(granularity).total_seconds()]'''

        print("count:", count)

        if count is not None:
            # either of count, start_time+count, end_time+count (or start_time+end_time+count)
            # if count is provided, count must be less than 5000
            '''if start_time is None and end_time is None:
                # fetch count=N most recent candles
                response = self.api.instrument.candles(
                    instrument, granularity=granularity, count=count
                )
                data = self._response_to_df(response)

            elif start_time is not None and end_time is None:
                # start_time + count
                from_time = start_time.timestamp()
                response = self.api.instrument.candles(
                    instrument, granularity=granularity, count=count, fromTime=from_time
                )
                data = self._response_to_df(response)

            elif end_time is not None and start_time is None:
                # end_time + count
                to_time = end_time.timestamp()
                response = self.api.instrument.candles(
                    instrument, granularity=granularity, count=count, toTime=to_time
                )
                data = self._response_to_df(response)
            

            else:

                from_time = start_time.timestamp()
                to_time = end_time.timestamp()

                # try to get data
                response = self.api.instrument.candles(
                    instrument,
                    granularity=granularity,
                    fromTime=from_time,
                    toTime=to_time,
                )

                data = self._response_to_df(response)'''
            response = self.api.instrument.candles(
                instrument, granularity=granularity, count=count
            )
            data = self._response_to_df(response, count, granularity)

        else:
            # count is None
            # Assume that both start_time and end_time have been specified.
            from_time = start_time.timestamp()
            to_time = end_time.timestamp()

            # try to get data
            response = self.api.instrument.candles(
                instrument, granularity=granularity, fromTime=from_time, toTime=to_time
            )

            data = self._response_to_df(response, count, granularity)

        return data

    def _response_to_df(self, response, count, granularity):
        """将API响应转换为Pandas DataFrame的函数。"""
        try:
            candles = response
        except KeyError:
            raise Exception(
                "下载数据时出错 - 请检查仪器格式并重试。"
            )

        times = []
        close_price, high_price, low_price, open_price, volume = [], [], [], [], []

        # 请求为字典时，要用[]访问，不能用.访问

        for candle in candles:
            times.append(candle["actionTimestamp"])
            close_price.append(float(candle["close"]))
            high_price.append(float(candle["high"]))
            low_price.append(float(candle["low"]))
            open_price.append(float(candle["open"]))
            volume.append(float(candle["volume"]))


        dataframe = pd.DataFrame(
            {
                "Open": open_price,
                "High": high_price,
                "Low": low_price,
                "Close": close_price,
                "Volume": volume,
            }
        )

        # 将 'barTime' 转换为正确的日期时间格式，去掉微秒部分
        dataframe.index = pd.to_datetime(times, format='ISO8601')
        #dataframe.drop_duplicates(inplace=True)

        return dataframe

    def _update_positions(
        self,
        instrument: str,
        position_direction: bool,
        position_type: bool,
        num: int,
        dt: datetime = None,
        trade: dict = None,
    ) -> None:
        """Updates orders and open positions based on the latest data.

        Parameters
        ----------
        instrument : str
            The name of the instrument being updated.

        position_direction: Ture为开仓，False为平仓
        position_type : Ture为多仓，False为空仓
        num : 仓位改变数
        ！！！！在多品种时，此函数需修改

        dt : datetime
            The current update datetime.

        trade : dict, optional
            A public trade, used to update virtual limit orders.
        """
        if position_direction:
            if position_type:
                self.long_position = self.long_position + num
            else:
                self.short_position = self.short_position + num
        else:
            if position_type:
                self.long_position = self.long_position - num
            else:
                self.short_position = self.short_position - num

    def change_positions(
            self,
            instrument: str,
            position_direction: bool,
            position_type: bool,
            num: int
    ) -> None:
        """Updates orders and open positions based on the latest data.

        Parameters
        ----------
        position_direction: Ture为开仓，False为平仓
        position_type : Ture为多仓，False为空仓
        num : 仓位改变数
        ！！！！在多品种时，此函数需修改
        """
        if position_direction:
            if position_type:
                self.long_position = self.long_position + num
            else:
                self.short_position = self.short_position + num
        else:
            if position_type:
                self.long_position = self.long_position - num
            else:
                self.short_position = self.short_position - num

    '''def get_positions(self, instrument: str = None):
        # ！！！！在多品种时，此函数需修改
        return self.long_position, self.short_position'''

    def get_positions(
            self,
            instrument: str,
    ) -> list:

        # try to get data
        response = self.api.instrument.positions(
            instrument
        )

        positions_information = response

        return positions_information

    def clear_positions(self,
        instrument: str = 'rb2510',
        ):

        positions_informations = self.get_positions(instrument)
        if positions_informations is None:
            print("已平全部仓位")
            return

        for positions_information in positions_informations:
            china_exchange = positions_information["exchange"]
            china_direction = positions_information["direction"]
            if china_direction==2:
                china_direction=3
            else:
                china_direction=2
            ydPosition = positions_information["ydPosition"]
            tdPosition = positions_information["tdPosition"]
            self.clear_position(instrument,china_exchange,china_direction,ydPosition,tdPosition)
            print("已平全部仓位")
        return
    
    def clear_position(self,
        instrument: str = None,
        china_exchange: str = 'SHFE',
        china_direction: int = 2,
        ydPosition: int = 0,
        tdPosition: int = 0,
        ):
        # ！！！！在多品种时，此函数需修改
        close_orders=[]
        if(tdPosition>0):
            close_orders.append(self.close_position(instrument, china_exchange, china_direction, 4, tdPosition))
        if(ydPosition>0):
            close_orders.append(self.close_position(instrument, china_exchange, china_direction, 5, ydPosition))
        for order in close_orders:
            self._place_market_order(order)
        return

    def close_position(self, instrument: str = None, china_exchange: str = 'SHFE', china_direction: int=2, offset: int = 4, volume: int = 1):
        if china_direction == 2:
            temp = self.get_candles(instrument, granularity="1s", count=1)
            kong_exit_point = temp.iloc[0]['Close'] + 3
            close_order = Order(
                instrument=instrument,
                direction=1,
                china_exchange=china_exchange,
                china_direction=china_direction,
                offset=offset,
                price=kong_exit_point,
                volume=volume,
                size=1,
                stopPrice=0,
                orderPriceType=1
            )
        elif china_direction == 3:
            temp = self.get_candles(instrument, granularity="1s", count=1)
            duo_exit_point = temp.iloc[0]['Close'] - 3
            close_order = Order(
                instrument=instrument,
                direction=1,
                china_exchange=china_exchange,
                china_direction=china_direction,
                offset=offset,
                price=duo_exit_point,
                volume=volume,
                size=1,
                stopPrice=0,
                orderPriceType=1
            )
        else:
            raise ValueError(china_direction)
        return close_order

    def get_precision(self, instrument: str, *arg, **kwargs):
        """Returns the precision of the specified instrument."""
        # TODO - review this - if not configured, do not try round?
        unified_response = {"size": 2, "price": 5}
        return unified_response

    def _place_market_order(self, order: Order):
        """
        self._check_connection()
        stop_loss_order = self._get_stop_loss_order(order)
        take_profit_details = self._get_take_profit_details(order)

        # Check position size
        size = self.check_trade_size(order.instrument, order.size)
        """
        response = self.api.order.market(
            order=order
        )

        return response

    def get_orderbook(self, instrument: str, *args, **kwargs):
        return None

    def get_public_trades(self, instrument: str, *args, **kwargs):
        return None