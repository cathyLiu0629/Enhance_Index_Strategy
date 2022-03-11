#缺失值处理
import pandas as pd
import numpy as np
import statsmodels.api as sm

#空值处理
def factors_null_process(data: pd.DataFrame) ->pd.DataFrame:
    data = data[data['INDUSTRY_CODE'].notnull()]

    data = data.reset_index().set_index(['INDUSTRY_CODE','code']).sort_index()
    data_ = data.groupby(level=0).apply(lambda factor:factor.fillna(factor.median()))
    data_ = data_.fillna(0)
    data_ = data_.reset_index().set_index('code').sort_index()
    return data_.drop('date',axis=1)

#去极值
def extreme_process_MAD(data, num=3):
    data_ = data.copy()
    feature_names = [i for i in data_.columns.tolist() if i not in ['INDUSTRY_CODE','market_cap']]
    median = data_[feature_names].median(axis=0)
    MAD = abs(data_[feature_names].sub(median,axis=1)).median(axis=0)
    data_.loc[:,feature_names] = data_.loc[:,feature_names].clip(lower = median - num * 1.4826 * MAD, upper = median + num * 1.4826 * MAD,axis=1)
    return data_

#标准化
def data_scale_Z_score(data):
    data_ = data.copy()
    feature_names = [i for i in data_.columns.tolist() if i not in ['INDUSTRY_CODE','market_cap']]
    data_.loc[:,feature_names] = (data_.loc[:,feature_names] - data_.loc[:,feature_names].mean(axis=0))/data.loc[:,feature_names].std()
    return data_

#市值和行业标准化
def neutralization(data):
    data_ = data.copy()
    factor_name = [i for i in data_.columns.tolist() if i not in ['INDUSTRY_CODE','market_cap']]
    X = pd.get_dummies(data_['INDUSTRY_CODE'])
    X['market_cap'] = np.log(data['market_cap']*100000000)
    def get_residual(X,Y):
        result = sm.OLS(Y,X).fit()
        return result.resid
    df = pd.concat([get_residual(X,data_[i]) for i in factor_name],axis=1)
    df.columns = factor_name
    df['INDUSTRY_CODE'] = data_['INDUSTRY_CODE']
    df['market_cap'] = data_['market_cap']
    return df








