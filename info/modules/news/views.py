from flask import session, render_template, current_app, jsonify, request, g
# 导入蓝图对象
from . import news_blu
# 导入User模型类
from info.models import User, News, Category
# 导入自定义的状态码
from info.utils.response_code import RET
# 导入常量配置信息
from info import constants, db
# 导入自定义的登录验证装饰器
from info.utils.commons import login_required

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
            # return jsonify(errno=RET.DBERR,errmsg='查询数据失败')

    # 项目首页的点击排行：默认按照新闻点击次数进行排序，limit6条
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(6)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据库失败')
    # 判断查询结果
    if not news_list:
        return jsonify(errno=RET.NODATA,errmsg='无新闻数据')
    # 定义容器，存储查询结果对象转成的字典数据
    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_dict())

    # 首页分类数据的加载
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询分类数据失败')
    # 检查查询结果
    if not categories:
        return jsonify(errno=RET.NODATA,errmsg='无分类数据')
    # 定义容器，存储查询结果对象调用to_dict返回的字典数据
    category_list = []
    for category in categories:
        category_list.append(category.to_dict())


    data = {
        'user_info':user.to_dict() if user else None,
        'news_dict_list':news_dict_list,
        'category_list':category_list
    }

    return render_template('news/index.html',data=data)


@news_blu.route('/news_list')
def get_news_list():
    """
    项目首页新闻列表加载
    1、获取参数，cid/page/per_page
    2、校验参数，把参数转成int类型
    3、根据cid进行查询数据库，默认按照新闻的发布时间进行排序，分页，
    paginate = paginate(page,per_page,False)
    paginate.items分页后的总数据
    paginate.pagesf分页后的总页数
    paginate.page当前页数
    4、遍历分页后的数据，转成字典
    5、返回数据
    :return:
    """
    # 获取参数
    cid = request.args.get('cid','1')
    page = request.args.get('page','1')
    per_page = request.args.get('per_page','10')
    # 检查参数
    try:
        cid,page,per_page = int(cid),int(page),int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数格式错误')
    # 根据分类id来查询数据库
    filters = []
    if cid > 1:
        filters.append(News.category_id == cid)
    try:
        # 默认按照新闻分类进行过滤，按照新闻发布时间倒序排序，分页每页10条
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,constants.HOME_PAGE_MAX_NEWS,False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据失败')
    # 使用paginate对象获取分页后的数据
    news_list = paginate.items
    total_page = paginate.pages
    current_page = paginate.page
    # 定义容器，遍历分页后的新闻对象，转成字典
    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_dict())
    data = {
        'news_dict_list':news_dict_list,
        'total_page':total_page,
        'current_page':current_page
    }
    # 返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data=data)


@news_blu.route('/<int:news_id>')
@login_required
def get_news_detail(news_id):
    """
    新闻详情页面
    1、判断用户的登录状态
    2、获取news_id,查询数据库
    3、判断查询结果
    4、返回新闻的详情数据
    :return:
    """
    user = g.user
    # if not user:
    #     return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')
    # 根据新闻id来查询新闻详细的数据
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询新闻数据失败')
    # 判断查询结果
    if not news:
        return jsonify(errno=RET.NODATA,errmsg='无新闻数据')
    # 如果news存在，点击次数加1
    news.clicks += 1
    # SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    data = {
        'user':user.to_dict() if user else None,
        'news':news.to_dict()
    }

    return render_template('news/detail.html',data=data)
















# 加载项目小图标
@news_blu.route('/favicon.ico')
def favicon():
    # 静态路径访问的默认实现，send_static_file,
    # 把静态文件发给浏览器
    return current_app.send_static_file('news/favicon.ico')

