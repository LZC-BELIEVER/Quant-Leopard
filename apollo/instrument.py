class EntitySpec(object):
    def __init__(self, ctx):
        self.ctx = ctx

    def candles(self, instrument, **kwargs):
        if self.ctx.sse_client is None:
            print("SSE客户端尚未连接")
            return None

        period = kwargs.get('granularity')
        count = kwargs.get('count')

        # 这里不需要异步，可以直接调用
        response = self.ctx.sse_client.get_data(
            symbol=instrument,
            candlenums=count,
            period=period
        )
        return response

    def positions(self, instrument, **kwargs):
        if self.ctx.sse_client is None:
            print("SSE客户端尚未连接")
            return None

        # 这里不需要异步，可以直接调用
        response = self.ctx.sse_client.get_position(
            symbol=instrument
        )
        return response
