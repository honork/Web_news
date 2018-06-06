

# 自定义过滤器，用来对模板页面进行处理处理
from flask import session, current_app, g

from info.models import User
import functools

def index_class(index):
    if index == 0:
        return 'first'
    elif index == 1:
        return 'second'
    elif index == 2:
        return 'third'
    else:
        return ''

# 自定义装饰器，封装用户的登录信息，登录验证装饰器
def login_required(f):
    # 让被装饰的函数名的属性不会被改变，
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        user_id = session.get('user_id','None')
        user = None
        if user_id:
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
        # 使用g对象用来临时存储数据
        g.user = user
        return f(*args,**kwargs)
    # wrapper.__name__ = f.__name__
    return wrapper

