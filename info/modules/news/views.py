from flask import session, render_template, current_app
# 导入蓝图对象
from . import news_blu

# 使用蓝图对象
@news_blu.route('/')
def index():
    session['name'] = '2018'
    return render_template('news/index.html')


# 加载项目小图标
@news_blu.route('/favicon.ico')
def favicon():
    # 静态路径访问的默认实现，send_static_file,
    # 把静态文件发给浏览器
    return current_app.send_static_file('news/favicon.ico')

