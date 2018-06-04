from flask import session, render_template, current_app, jsonify
# 导入蓝图对象
from . import news_blu
# 导入User模型类
from info.models import User
# 导入自定义的状态码
from info.utils.response_code import RET

# 使用蓝图对象
@news_blu.route('/')
def index():
    """

    展示用户登录信息:检查用户登录状态；
    2、尝试从redis数据库中获取用户的缓存信息，user_id
    3、判断获取结果是否存在
    4、根据user_id查询myql数据库
    5、判断查询结果，
    :return:
    """
    # 从redis数据库中获取用户id
    user_id = session.get('user_id')
    # 如果user_id存在，查询mysql数据库，获取用户信息
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='查询数据失败')
        # if user:
        #     return user.to_dict()
        # else:
        #     return None
    data = {
        'user_info':user.to_dict() if user else None
    }

    return render_template('news/index.html',data=data)


# 加载项目小图标
@news_blu.route('/favicon.ico')
def favicon():
    # 静态路径访问的默认实现，send_static_file,
    # 把静态文件发给浏览器
    return current_app.send_static_file('news/favicon.ico')

