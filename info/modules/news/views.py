from flask import session
# 导入蓝图对象
from . import news_blu

# 使用蓝图对象
@news_blu.route('/')
def index():
    session['name'] = '2018'
    return 'index2016'