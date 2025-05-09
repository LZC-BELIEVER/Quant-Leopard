"""from autotrader import AutoTrader

# Create AutoTrader instance, configure it, and run backtest
at = AutoTrader()
at.configure(verbosity=1, show_plot=True)
# at.add_strategy("long_ema_crossover")
# at.add_strategy("ema_crossover")
at.add_data(data_dict={'RB0': 'RB0.csv'}, data_directory="custom_data")
at.add_strategy("macd")
at.backtest(start="1/6/2023", end="1/2/2024")
at.virtual_account_config(initial_balance=1000, leverage=30)
at.run()
"""
"""from autotrader import AutoTrader, utilities
import os
import pandas as pd

# Create AutoTrader instance, configure it, and run backtest
at = AutoTrader()
at.configure(verbosity=1, show_plot=True)

rb0_path = os.path.join("custom_data", "RB0.csv")
for i in range(1,100):
        # 读取RB0.csv的最后一行
    rb0_data = pd.read_csv(rb0_path)
    last_row = rb0_data.iloc[-1:]

    # 追加写入RealTime.csv
    realtime_path = os.path.join("custom_data", "RealTime.csv")
    last_row.to_csv(realtime_path, mode='a', header=not os.path.exists(realtime_path), index=False)

    at.add_data(
        data_dict={'RealTime': 'RealTime.csv'},
        data_directory="custom_data",
        stream_object=utilities.RealtimeStream,
        dynamic_data=True
    )
at.add_strategy("macd")
at.backtest(start="1/6/2023", end="1/2/2024")
at.virtual_account_config(initial_balance=1000, leverage=30)
at.run()"""

from autotrader import AutoTrader

at = AutoTrader()
at.configure(verbosity=1, show_plot=True, broker='quantumhedge')

at.add_strategy("bdwz")
at.run()