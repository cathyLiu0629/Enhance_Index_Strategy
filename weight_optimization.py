import pandas as pd
import datetime
from config_operate import *
from jqdatasdk import *
my_config = MyConfig()
account,pw = my_config.get_jq_account()
auth(account,pw)
from dateutil.parser import parse
from scipy.optimize import NonlinearConstraint
from functional import *
from scipy.optimize import minimize


def get_weighs(symbol: str, start: str, end: str, method: str = 'cons') -> pd.DataFrame:
    '''
    获取月度指数成份权重
    --------
        mehtod:ind 输出 行业权重
               cons 输出 成份股权重
    '''
    periods = get_trade_period(start, end, 'ME')

    ser_dic = {}
    if method == 'ind':
        for d in periods:
            # 获取当日成份及权重
            index_w = get_index_weights(symbol, date=d)
            # 获取行业
            index_w['ind'] = industry(index_w.index.tolist(), d)
            # 计算行业所占权重
            weight = index_w.groupby('ind')['weight'].sum() / 100

            ser_dic[d] = weight

        ser = pd.concat(ser_dic, names=['date', 'industry']).reset_index()
        ser['date'] = pd.to_datetime(ser['date'])
        return ser.set_index(['date', 'industry'])

    elif method == 'cons':

        df = pd.concat([get_index_weights(symbol, date=d) for d in periods])
        df.drop(columns='display_name', inplace=True)

        df.set_index('date', append=True, inplace=True)
        df = df.swaplevel()
        df['weight'] = df['weight'] / 100
        return df


def get_group(ser: pd.Series, N: int = 3, ascend: bool = True) -> pd.Series:
    '''默认分三组 升序'''
    ranks = ser.rank(ascending=ascend)
    label = ['G' + str(i) for i in range(1, N + 1)]

    return pd.cut(ranks, bins=N, labels=label)


def get_opt_weight(df):
    data = df.copy()
    index_weight = data['weight'].values
    score = data['score'].values
    f = data.drop(columns=['weight','score']).T.values

    df_len = len(data)

    def func(w):
        return w.dot(score)
    # 约束条件1,2
    cons_1 = lambda w: f @ (index_weight - w)

    # 约束条件3:个股相对于基准指数成分股的偏离
    cons_2 = lambda w: w - index_weight

    # 约束条件6:权重之和为1
    cons_3 = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}

    nonlinear_constraint1 = NonlinearConstraint(cons_1, 0.95, 1.05)
    nonlinear_constraint2 = NonlinearConstraint(cons_2, 0., 0.05)

    # 建立约束条件5，个股权重上限，及权重的取值范围
    limit = tuple((0, 1.5) for x in range(df_len))

    # 利用递归最小二乘求解最优权重
    res = minimize(func, index_weight, method='SLSQP', bounds=limit,
                   constraints=[nonlinear_constraint1, nonlinear_constraint2, cons_3])

    if res['success'] != True:
        print(df.name)

    return pd.Series(res['x'], index=data.index.get_level_values(1))


def optimization_result(symbol: str, start: str, end: str, factors: pd.DataFrame) -> pd.DataFrame:
    '''
    获取优化权重后的结果
    '''
    factors = factors.copy()
    ind_weight = get_weighs(symbol, start, end)
    factors['weight'] = ind_weight['weight']

    index_weight = factors['weight'].values
    select_col = [col for col in factors.columns if col not in ['market_cap', 'NEXT_RET']]

    df = pd.get_dummies(factors[select_col], columns=['INDUSTRY_CODE'])

    result_df = df.groupby(level='date').apply(get_opt_weight)

    return result_df.to_frame('w')