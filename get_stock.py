import pandas as pd
import datetime
from config_operate import *
from jqdatasdk import *
my_config = MyConfig()
account,pw = my_config.get_jq_account()
auth(account,pw)

class FilterStocks():
    '''
    获取某日的成分股股票
    1.过滤ST
    2.过滤上市不足N个月
    3.过滤当月交易不超过N日的股票
    '''
    def __init__(self,index,date,N,active_day):
        '''
        :param index: 'A'全市场
        :param date: 日期
        :param N: 上市日期不足N日
        :param active_day: 过滤交易不足N日的股票
        '''
        self.__index = index
        self.__date = date
        self.__N = N
        self.__active_day = active_day
    @property
    def get_stocks(self):
        if self.__index == 'A':
            stock_list = get_index_stocks('000002.XSHG',date = self.__date) + get_index_stocks('399107.XSHE',date = self.__date)
        else:
            stock_list = get_index_stocks(self.__index,date = self.__date)
        #过滤st
        st_data = get_extras('is_st',stock_list,end_date=self.__date,count=1).iloc[0]
        print(st_data)
        stock_list = st_data[st_data==False].index.tolist()
        stock_list = self.delete_stop(stock_list,self.__date)
        stock_list = self.delete_pause(stock_list,self.__date)
        return stock_list


    @staticmethod
    def delete_stop(stock_list,begin_date,n=90):
        #剔除上市时间不足3个月的股票
        stock_list = [code for code in stock_list if get_security_info(code).start_date < (begin_date - datetime.timedelta(days=n))]
        return stock_list
    @staticmethod
    def delete_pause(stock_list,begin_date,n=15):
        begin_date = get_trade_days(end_date=begin_date,count=1)[0].strftime('%Y-%m-%d')
        df = get_price(stock_list,end_date=begin_date,count=22,fields='paused',panel=False)
        #当天有交易的股票列表
        df_date = df.loc[(df['paused']==0) & (df['time']==begin_date),'code'].unique().tolist()
        paused_days = df[df['code'].isin(df_date)].groupby('code')['paused'].sum()
        return paused_days[paused_days<n].index.tolist()

if __name__=='__main__':
    s1 = FilterStocks('A','2022-01-05',20,30)
    FilterStocks.delete_pause(s1.get_stocks,'2022-01-05')