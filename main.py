import pandas as pd

from functional import *
from get_stock import FilterStocks
from data_preprocess import *
from expected_return_cal import *

pd.set_option('max_columns',None)
if __name__=='__main__':
    start_date='2020-01-01'
    end_date = '2020-03-31'
    factors = get_factor(query_model_factor,'000300.XSHG',start_date,end_date)
    print(factors.head())
    #此时获得的factor有三个维度，两个level的index：date和code，剩下的列为所有的因子值

    #下面进行数据预处理，相应函数在data_preprocess肿
    factors1 = factors.groupby(level='date').apply(extreme_process_MAD)
    factors2 = factors1.groupby(level='date').apply(factors_null_process)
    factors3 = factors2.groupby(level='date').apply(neutralization)
    factors4 = factors3.groupby(level='date').apply(data_scale_Z_score)
    factors4.to_csv('factor.csv',encoding='utf-8')

    #下面进行预期收益计算（优化模型需要用到的）
    next_return = get_next_return(factors4,True,'2020-04-15')
    factors4['NEXT_RET'] = next_return
    weights = IR_weight(factors4)

