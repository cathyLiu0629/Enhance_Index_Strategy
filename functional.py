import pandas as pd
import datetime
from config_operate import *
from jqdatasdk import *
my_config = MyConfig()
account,pw = my_config.get_jq_account()
auth(account,pw)
from tqdm import tqdm
from get_stock import FilterStocks
import jqfactor_analyzer
import numpy as np


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

#最主要的函数，需要获取交易日历，股票池，以及每天的因子df
def get_factor(func,index_symbol,start,end,freq='ME'):
    #将每天的因子的df整合成一个大的df
    period = get_trade_period(start,end,freq)
    factor_dic={}
    for d in tqdm(period):
        securities = FilterStocks(index_symbol,d.strftime('%Y%m%d'),N=12,active_day=15).get_stocks
        factor_dic[d] = func(securities, d)
    factor_df = pd.concat(factor_dic)
    factor_df.index.names = ['date','code']

    return factor_df

def query_model_factor(securities,date):
    #先获取可以直接获取的因子值
    fields = ['natural_log_of_market_cap', 'book_to_price_ratio',
              'ROC20', 'ROC60',
              'net_profit_growth_rate', 'operating_revenue_growth_rate',
              'total_profit_growth_rate', 'roe_ttm',
              'roa_ttm', 'VOL20',
              'VOL60']
    factors = get_factor_values(securities,fields,date,date)
    factors = dict2frame(factors)

    industry_ser = industry(securities,date)
    market_capitalization = market_cap(securities,date)

    factors = pd.concat([factors,industry_ser,market_capitalization],axis=1)
    #factors为指定股票池，指定日期的因子df
    return factors

def dict2frame(dic):
    tmp_v = [v.T for v in dic.values()]
    name = [s.upper() for s in dic.keys()]
    df = pd.concat(tmp_v,axis=1)
    df.columns=name
    return df

def industry(securities,date,method='industry_code'):
    industry_dict = get_industry(securities,date)
    industry_series = pd.Series({k:v.get('sw_l1',{method: np.nan})[method] for k,v in industry_dict.items()})
    industry_series.name = method.upper()
    return industry_series

def market_cap(securities,date):
    df = get_fundamentals(query(valuation.code,valuation.market_cap).filter(valuation.code.in_(securities)
    ), date=date)
    print(df)
    df.set_index('code',inplace=True)
    return df
securities = FilterStocks('A','2022-03-07',N=12,active_day=15).get_stocks

industry(securities,'2022-03-07')
