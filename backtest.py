import backtrader as bt

import backtrader.indicators as btind # 导入策略分析模块
import backtrader.feeds as btfeeds # 导入数据模块
import pandas as pd
from functional import get_price_info #获取行情数据
import datetime

START_DATE = '2020-01-01'
END_DATE = '2020-12-31'
price_info = get_price_info('000300.XSHG',START_DATE,END_DATE) #'time','code','open','close','low','high','volume','open_interest'
trade_info = pd.read_csv('trade_info.csv',parse_dates=['date']) #date,code,w

cerebro = bt.Cerebro()

for stock in price_info['code'].unique():
    # 日期对齐
    data = pd.DataFrame(index=price_info.index.unique()) # 获取回测区间内所有交易日
    df = price_info.query(f"code=='{stock}'")[['open','high','low','close','volume','open_interest']]
    data_ = pd.merge(data, df, left_index=True, right_index=True, how='left')
    # 缺失值处理：日期对齐时会使得有些交易日的数据为空，所以需要对缺失数据进行填充
    data_.loc[:,['volume','open_interest']] = data_.loc[:,['volume','open_interest']].fillna(0)
    data_.loc[:,['open','high','low','close']] = data_.loc[:,['open','high','low','close']].fillna(method='pad')
    data_.loc[:,['open','high','low','close']] = data_.loc[:,['open','high','low','close']].fillna(0)
    # 导入数据
    datafeed = bt.feeds.PandasData(dataname=data_, fromdate=datetime.datetime(2019,1,2), todate=datetime.datetime(2021,1,28))
    cerebro.adddata(datafeed, name=stock) # 通过 name 实现数据集与股票的一一对应


# 初始资金 100,000,000
cerebro.broker.setcash(100000000.0)
# 佣金，双边各 0.0003
cerebro.broker.setcommission(commission=0.0003)
# 滑点：双边各 0.0001
cerebro.broker.set_slippage_perc(perc=0.0001)


cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='pnl') # 返回收益率时序数据
cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='_AnnualReturn') # 年化收益率
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='_SharpeRatio') # 夏普比率
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='_DrawDown') # 回撤


# 回测策略
class TestStrategy(bt.Strategy):
    '''选股策略'''

    def __init__(self):
        self.buy_stock = trade_info  # 保留调仓列表
        # 读取调仓日期，即每月的最后一个交易日，回测时，会在这一天下单，然后在下一个交易日，以开盘价买入
        self.trade_dates = pd.to_datetime(self.buy_stock['date'].unique()).tolist()
        self.order_list = []  # 记录以往订单，方便调仓日对未完成订单做处理
        self.buy_stocks_pre = []  # 记录上一期持仓

    def next(self):
        dt = self.datas[0].datetime.date(0)  # 获取当前的回测时间点
        # 如果是调仓日，则进行调仓操作
        if dt in self.trade_dates:
            print("--------------{} 为调仓日----------".format(dt))
            # 在调仓之前，取消之前所下的没成交也未到期的订单
            if len(self.order_list) > 0:
                for od in self.order_list:
                    self.cancel(od)  # 如果订单未完成，则撤销订单
                self.order_list = []  # 重置订单列表
            # 提取当前调仓日的持仓列表
            buy_stocks_data = self.buy_stock.query(f"date=='{dt}'")
            long_list = buy_stocks_data['code'].tolist()
            print('long_list', long_list)  # 打印持仓列表
            # 对现有持仓中，调仓后不再继续持有的股票进行卖出平仓
            sell_stock = [i for i in self.buy_stocks_pre if i not in long_list]
            print('sell_stock', sell_stock)  # 打印平仓列表
            if len(sell_stock) > 0:
                print("-----------对不再持有的股票进行平仓--------------")
                for stock in sell_stock:
                    data = self.getdatabyname(stock)
                    if self.getposition(data).size > 0:
                        od = self.close(data=data)
                        self.order_list.append(od)  # 记录卖出订单
            # 买入此次调仓的股票：多退少补原则
            print("-----------买入此次调仓期的股票--------------")
            for stock in long_list:
                w = buy_stocks_data.query(f"code=='{stock}'")['w'].iloc[0]  # 提取持仓权重
                data = self.getdatabyname(stock)
                order = self.order_target_percent(data=data, target=w * 0.95)  # 为减少可用资金不足的情况，留 5% 的现金做备用
                self.order_list.append(order)

            self.buy_stocks_pre = long_list  # 保存此次调仓的股票列表


# 将编写的策略添加给大脑，别忘了 ！
cerebro.addstrategy(TestStrategy)

# 启动回测
result = cerebro.run()
# 从返回的 result 中提取回测结果
strat = result[0]
# 返回日度收益率序列
daily_return = pd.Series(strat.analyzers.pnl.get_analysis())
# 打印评价指标
print("--------------- AnnualReturn -----------------")
print(strat.analyzers._AnnualReturn.get_analysis())
print("--------------- SharpeRatio -----------------")
print(strat.analyzers._SharpeRatio.get_analysis())
print("--------------- DrawDown -----------------")
print(strat.analyzers._DrawDown.get_analysis())