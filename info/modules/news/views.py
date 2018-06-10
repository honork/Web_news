from flask import session, render_template, current_app, jsonify, request, g
# 导入蓝图对象
from . import news_blu
# 导入User模型类
from info.models import User, News, Category, Comment, CommentLike
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
    # 收藏,默认为False，如果用户已登录，并且该新闻已被登录用户收藏
    is_collected = False
    if user and news in user.collection_news:
        is_collected = True

    # 评论
    comments = []
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
    comment_like_ids = []
    # 获取当前登录用户的所有评论的id，
    if user:
        try:
            comment_ids = [comment.id for comment in comments]
            # 再查询点赞了哪些评论
            comment_likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids),
                                                     CommentLike.user_id == g.user.id).all()
            # 遍历点赞的评论数据,获取
            comment_like_ids = [comment_like.comment_id for comment_like in comment_likes]
        except Exception as e:
            current_app.logger.error(e)
    comment_dict_li = []
    for comment in comments:
        comment_dict = comment.to_dict()
        # 如果未点赞
        comment_dict['is_like'] = False
        # 如果点赞
        if comment.id in comment_like_ids:
            comment_dict['is_list'] = True
        comment_dict_li.append(comment_dict)

    is_followed = False
    # 用户关注新闻的发布者，即登录用户关注作者。，
    if news.user and user:
        if news.user in user.followers:
            is_followed = True
    # 项目首页的点击排行：默认按照新闻点击次数进行排序，limit6条
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(6)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')
    # 判断查询结果
    if not news_list:
        return jsonify(errno=RET.NODATA, errmsg='无新闻数据')
    # 定义容器，存储查询结果对象转成的字典数据
    news_dict_list = []
    for index in news_list:
        news_dict_list.append(index.to_dict())

    data = {
        'user':user.to_dict() if user else None,
        'news_dict_list':news_dict_list,
        'news_detail':news.to_dict(),
        'is_collected':is_collected,
        'is_followed':is_followed,
        'comments':comment_dict_li
    }

    return render_template('news/detail.html',data=data)


@news_blu.route('/news_collect',methods=['POST'])
@login_required
def news_collect():
    """
    收藏和取消收藏
    1、尝试获取用户的登录信息，
    2、获取参数，news_id,action:collect,cancel_collect
    3、校验参数的完整性
    4、检查action参数的范围
    5、news_id转成int类型，查询数据库
    6、校验查询结果
    7、判断用户选择的是收藏，或取消收藏
    8、提交数据到数据库
    9、返回结果

    :return:
    """
    # 尝试获取用户登录信息
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')
    # 获取参数
    news_id = request.json.get('news_id')
    action = request.json.get('action')
    # 检查参数的完整
    if not all([news_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不完整')
    # 把news_id转成int
    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数格式错误')
    # 对action进行判断
    if action not in ['collect','cancel_collect']:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    # 查询数据库，News
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据失败')
    # 检查查询结果
    if not news:
        return jsonify(errno=RET.NODATA,errmsg='无新闻数据')
    # 判断用户选择的是收藏还是取消收藏
    if action == 'collect':
        # 判断用户没有收藏过
        if news not in user.collection_news:
            user.collection_news.append(news)
    else:
        user.collection_news.remove(news)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    # 返回结果
    return jsonify(errno=RET.OK,errmsg='OK')


@news_blu.route('/news_comment',methods=['POST'])
@login_required
def comments_news():
    """
    评论新闻
    1、判断用户是否登录
    2、获取参数，news_id,comment,parent_id
    3、检查参数的完整
    4、校验news_id,parent_id转成整型
    5、根据news_id查询数据库
    6、实例化评论表对象，保存评论id、新闻id，新闻内容，
    7、提交数据返回结果

    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')
    news_id = request.json.get('news_id')
    parent_id = request.json.get('parent_id')
    content = request.json.get('comment')
    if not all([news_id,content]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失111')
    try:
        news_id = int(news_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误222')
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据失败')
    if not news:
        return jsonify(errno=RET.NODATA,errmsg='数据不存在')
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = content
    if parent_id:
        comment.parent_id = parent_id
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
    return jsonify(errno=RET.OK,errmsg='OK',data=comment.to_dict())


@news_blu.route('/comment_like',methods=['POST'])
@login_required
def comment_like():
    """
    点赞或取消点赞
    1、获取用户登录信息
    2、获取参数，comment_id,action
    3、检查参数的完整性
    4、判断action是否为add，remove
    5、把comment_id转成整型
    6、根据comment_id查询数据库
    7、判断查询结果
    8、判断行为是点赞还是取消点赞
    9、如果为点赞，查询改评论，点赞次数加1，否则减1
    10、提交数据
    11、返回结果

    :return:
    """
    user = g.user
    comment_id = request.json.get('comment_id')
    action = request.json.get('action')
    if not all([comment_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不完整')
    if action not in ['add','remove']:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    try:
        comment_id = int(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='参数错误')
    try:
        comments = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    if not comments:
        return jsonify(errno=RET.NODATA,errmsg='评论不存在')
    if action == 'add':
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,CommentLike.comment_id== comment_id).first()
        if not comment_like_model:
            comment_like_model = CommentLike()
            comment_like_model.user_id = user.id
            comment_like_model.comment_id = comment_id
            db.session.add(comment_like_model)
            comments.like_count += 1
    else:
        comment_like_model = CommentLike.query.filter(CommentLike.user_id==user.id,CommentLike.comment_id==comment_id).first()
        if comment_like_model:
            db.session.delete(comment_like_model)
            comments.like_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')

    return jsonify(errno=RET.OK,errmsg='OK')


@news_blu.route('/followed_user',methods=['POST'])
@login_required
def followed_user():
    """
    关注与取消关注
    1、获取用户信息,如果未登录直接返回
    2、获取参数，user_id和action
    3、检查参数的完整性
    4、校验参数，action是否为followed，unfollow
    5、根据用户id获取被关注的用户
    6、判断获取结果
    7、根据对应的action执行操作，关注或取消关注
    8、返回结果
    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')
    user_id = request.json.get('user_id')
    action = request.json.get('action')
    if not all([user_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不完整')
    if action not in ['follow','unfollow']:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    try:
        other = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据失败')
    if not other:
        return jsonify(errno=RET.NODATA,errmsg='无用户数据')
    # 如果选择关注
    if action == 'follow':
        if other not in user.followed:
            user.followed.append(other)
        else:
            return jsonify(errno=RET.DATAEXIST,errmsg='当前用户已被关注')
    # 取消关注
    else:
        if other in user.followed:
            user.followed.remove(other)

    return jsonify(errno=RET.OK,errmsg='OK')



















# 加载项目小图标
@news_blu.route('/favicon.ico')
def favicon():
    # 静态路径访问的默认实现，send_static_file,
    # 把静态文件发给浏览器
    return current_app.send_static_file('news/favicon.ico')

