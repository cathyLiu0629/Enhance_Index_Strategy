import pandas as pd
from jqdatasdk import *
import scipy.stats as st

#获取下一期的收益率
def get_next_return(factor_df, keep_last_term, next_date) -> pd.Series:
    securities = factor_df.index.level[1].tolist()
    periods = [i.strftime('%Y-%m-%d') for i in factor_df.index.level[0].tolist()]
    if keep_last_term:
        end = next_date
        periods.append(end)
    close = pd.concat([get_price(securities, end_date=i, count=1, fields='close',panel=False) for i in periods])
    print(close.head())
    close = pd.pivot_table(close, index = 'time', columns = 'code',values = 'close')
    ret = close.pct_change().shift(-1)
    ret = ret.iloc[:-1]
    return ret

def calc_rank_IC(factor_df):
    factor_col = [i for i in factor_df.columns if i not in ['INDUSTRY_CODE','market_cap','NEXT_RET']]
    IC = factor_df.groupby(level='date').apply(lambda x:[st.spearmanr(x[factor_name],x['NEXT_RETURN'])[0]for factor_name in factor_col])
    print('IC：{}'.format(IC))
    return pd.DataFrame(IC.tolist(), index = IC.index, columns=factor_col)

def IR_weight(factor):
    data = factor.copy()
    IC = calc_rank_IC(data)
    abs_IC = IC.abs()
    rolling_IC = abs_IC.rolling(12,min_periods=1).mean()
    rolling_IC_std = abs_IC.rolling(12,min_periods=1).std()
    IR = rolling_IC/rolling_IC_std
    print('IR:{}'.format(IR))
    IR.iloc[0,:] = rolling_IC.iloc[0,:]
    weight = IR.div(IR.sum(axis=1),axis=0)
    return weight
