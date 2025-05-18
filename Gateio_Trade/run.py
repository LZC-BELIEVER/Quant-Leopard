from autotrader import AutoTrader

at = AutoTrader()
at.configure(verbosity=1, show_plot=True, broker='quantumhedge')

at.add_strategy("bdwz")
at.run()
