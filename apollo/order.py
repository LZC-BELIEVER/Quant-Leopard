from apollo.SSEClient import SSEClient

class EntitySpec(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def create(
        self,
        order
    ):
        new_order = order
        print("准备下单")

        response = self.ctx.sse_client.send_order(
            symbol=new_order.instrument,
            exchange=new_order.china_exchange,
            direction=new_order.china_direction,
            offset=new_order.offset,
            price=new_order.price,
            volume=new_order.volume,
            stopPrice=new_order.stopPrice,
            orderPriceType=new_order.orderPriceType
        )

        return response

    def market(self, order):
        """
        Shortcut to create a Market Order in an Account

        Args:
            accountID : The ID of the Account
            kwargs : The arguments to create a MarketOrderRequest

        Returns:
            v20.response.Response containing the results from submitting
            the request
        return self.create(
            accountID,
            order=MarketOrderRequest(**kwargs)
        )
        """

        return self.create(
            order=order
        )

