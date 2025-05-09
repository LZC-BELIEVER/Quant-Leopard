from autotrader import AutoTrader, Order

at = AutoTrader()
at.configure(broker='ccxt:binance')
at.virtual_account_config(verbosity=1, exchange='ccxt:binance', leverage=10,refresh_freq = "1s")
broker = at.run()

# Create an order
order = Order(
    instrument="ETH/USDT",
    direction=1,
    size=0.1,
)

# Place order
broker.place_order(order)