import pandas as pd
from config_operate import *
from jqdatasdk import *
my_config = MyConfig()
account,pw = my_config.get_jq_account()
auth(account,pw)


