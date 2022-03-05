import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import datetime
import talib
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.sans-serif'] = ['SimHei'] # 指定默认字体
plt.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题
plt.style.use('seaborn')
from config_operate import *
from jqdatasdk import *
my_config = MyConfig()
account,pw = my_config.get_jq_account()
auth(account,pw)


def get_trade_period(start_date,end_date,freq):
    """
    :param start_date: YYYY-MM-DD
    :param end_date: YYYY-MM-DD
    :param freq: M/Q/Y(month,quarter,year)+S/E(start,end)
    :return: list(datetime.date)
    """
    days = pd.Index(pd.to_datetime(get_trade_days(start_date,end_date)))

    idx_df = days.to_frame()

    if freq[-1]=='S':
        day_range=idx_df.resample(freq[0]).first()
    else:
        day_range=idx_df.resample(freq[0]).last()
    day_range=day_range[0].dt.date

    return day_range.dropna().values.tolist()

def get_factor(func,stock_code,start,end,freq):
    periods = get_trade_period(start,end,freq)
    factor_dic={}
if __name__=='__main__':
    get_trade_period('2019-01-01','2019-12-31','QS')