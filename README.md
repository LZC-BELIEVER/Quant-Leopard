# Quant Leopard 1.0 使用文档

## 简介
- Quant Leopard 1.0是波普尔技术（西安）科技发展有限公司内部量化策略研究人员所使用的直连交易客户端系统，系统可以实现获取期货行情数据并根据自定义策略实现自动化交易。
- 系统基于[AutoTrader](https://github.com/kieran-mackle/AutoTrader)实现。现在只支持中国大陆期货市场单一期货品种交易，更多功能请期待Quant Leopard 2.0 版本。
- 由于系统还处于内部测试阶段，可能会有某些bug，所以建议尽量先在1手范围内下单，且需要时常看一下仓位结果（在随手易等软件）上，避免造成大的损失。
- Author: LZC from XJTU

## 文件结构
- **autotrader**:系统主模块
- **apollo**:系统与服务器连接接口
- **Gateio_Trade**：系统使用模块

## 部署方法
1. 下载PyCharm，并准备一个3.12以上的Python环境
2. 找到Python环境目录，并进入Lib/site-packages目录（即Python库文件目录），将autotrader和apollo复制到此目录中（如果以前下载过autotrader，先删除）
3. 在PyCharm中指定刚才的Python环境新建项目，将Gateio_Trade文件夹下文件复制到此位置，运行 run.py（单次运行）或者 day_and_night.py（一直运行）
4. 在代码中，还需要作以下修改：
    1. 找到apollo中__init__.py文件，将__init__函数参数中的user_id改为你的交易账号，password改为你的交易密码，liscence改为你的lisence（这些没有请在群里要）。
    2. 在根目录下day_and_night.py中的run_strategy函数中，将python路径以及项目路径改为自己的路径
    3. 仿照Gateio_Trade中strategies文件夹下bdwz.py（将bdwz.py中self.broker.api.sse_client.login('')括号内填入自己密码）以及config中的bdwz.ymal写一份自己的策略，并放在对应位置（请看群里的bdwz.py，这里的bdwz.py不准确。）
    4. 若报错“no module named XXX”, 需pip 下载 aiohttp_sse_client，aiohttp，asyncio等所需库
    5. 将run.py中at.add_strategy("bdwz")中的“bdwz”改为你的策略名（你的策略叫xxx.py，就改为xxx）
    6. 将autotrader/brokers/quantumhedge.py中298行的clear_positions(self, instrument: str = 'ao2509')中的“ao2509”改为你自己要交易的品种

## 下单规范
- 下单规范如下：`
```python
    Order(
        instrument=self.instrument, #品种名,ymal文件的watchlist中定义，现在暂时先用rb2510  
        direction=1,  # 无关参数，但需保留
        china_exchange="SHFE", #交易所
        china_direction=2, #2：buy 3：sell
        offset=4, #1:开仓 2：平仓 3：强平 4：平今 5：平昨
        price=3000, #下单价格，限价单填相应价格，市价单不要
        volume=1, #下单手数，对策略自信可以增大下单手数
        size=1,  # 无关参数，但需保留
       stopPrice=0, #止损价，现在无效。止损需通过限价单或动态止损方式
        orderPriceType=1 #1限价单 2市价单
    )
```
- 注意：市价单默认取买一、卖一进行交易，在行情快速变化时，可能产生下单成功但是交易不成功的情况。为避免此情况，可以自己在策略中取买二、卖二甚至买三、买三进行交易，按照价格优先原则，会立即以当前市价成交。取买二、卖二等方法是下单时调用数据接口取一根最新一秒钟的k线并取收盘价，再-2、+2。
