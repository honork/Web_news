import time
from datetime import datetime, timedelta

from flask import g, render_template, request, session, redirect, url_for, jsonify, current_app, abort

from info import constants, db
from info.models import User, News, Category
from info.utils.commons import login_required
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import admin_blu

@admin_blu.route('/index')
@login_required
def index():
    """后台管理首页"""
    user = g.user
    return render_template('admin/index.html',user=user.to_dict())


@admin_blu.route('/login',methods=['GET','POST'])
def login():
    """
    后台管理员登录
    1、如果为get请求，使用session获取登录信息，user_id,is_admin,
    2、判断用户如果用户id存在并是管理员，重定向到后台管理页面
    3、获取参数，user_name,password
    4、校验参数完整性
    5、查询数据库，确认用户存在，is_admin为true，校验密码
    6、缓存用户信息，user_id,mobile,nick_name,is_admin
    7、跳转到后台管理页面

    :return:
    """
    if request.method == 'GET':
        user_id = session.get('user_id',None)
        is_admin = session.get('is_admin',False)
        if user_id and is_admin:
            return redirect(url_for('admin.index'))
        return render_template('admin/login.html')

    user_name = request.form.get('username')
    password = request.form.get('password')
    if not all([user_name,password]):
        return render_template('admin/login.html', errmsg='参数不完整')
    try:
        user = User.query.filter(User.mobile==user_name,User.is_admin==True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg='数据库查询错误')
    if user is None or not user.check_password(password):
        return render_template('admin/login.html', errmsg='用户名或密码错误')
    session['user_id'] = user.id
    session['mobile'] = user.mobile
    session['nick_name'] = user.nick_name
    session['is_admin'] = user.is_admin
    return redirect(url_for('admin.index'))


@admin_blu.route('/user_count')
def user_count():
    """
    用户数据统计
    1、统计总人数：不含管理员，is_admin=False
    2、统计月人数：User.create_time > mon_begin_date(每月的开始日期2018-06-01)
    3、统计日人数：User.create_time > day_begin_date(每天的开始时间2018-06-09)
    :return:
    """
    # 定义总人数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
    # 月新增人数'2018-06-09' 2018-06-09 tm_year=2018, tm_mon=6, tm_mday=9,
    mon_count = 0
    t = time.localtime()
    # 生成月份开始日期的字符串
    mon_begin_date_str = '%d-%02d-01' % (t.tm_year,t.tm_mon)
    # 把日期字符串转成日期对象
    mon_begin_date = datetime.strptime(mon_begin_date_str,'%Y-%m-%d')
    # 查询每月新增的人数
    try:
        mon_count = User.query.filter(User.is_admin == False,User.create_time > mon_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)
    # 日新增人数
    day_count = 0
    day_begin_date_str = '%d-%02d-%02d' % (t.tm_year, t.tm_mon,t.tm_mday)
    day_begin_date = datetime.strptime(day_begin_date_str,'%Y-%m-%d')
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time > day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)
    # 定义活跃的人数和活跃的时间
    active_time = []
    active_count = []
    # 默认按照31天往前推
    active_begin_date_str = '%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)
    active_begin_date = datetime.strptime(active_begin_date_str, '%Y-%m-%d')
    for x in range(0,31):
        # 今天的0时0分
        # 6月9日 - 6月9日 = 6月9日
        begin_date = active_begin_date - timedelta(days=x)
        # 今天的24时,明天的0时0分
        end_date = active_begin_date - timedelta(days=(x-1))
        # 把日期对象转成字符串
        begin_date_str = datetime.strftime(begin_date,'%Y-%m-%d')
        count = 0
        try:
            count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,User.last_login < end_date).count()
        except Exception as e:
            current_app.logger.error(e)
        # 添加日期和查询结果
        active_time.append(begin_date_str)
        active_count.append(count)
    # 反转列表
    active_time.reverse()
    active_count.reverse()

    data = {
        'total_count':total_count,
        'mon_count':mon_count,
        'day_count':day_count,
        'active_time':active_time,
        'active_count':active_count
    }

    return render_template('admin/user_count.html',data=data)



















@admin_blu.route('/user_list')
def user_list():
    """
    用户列表
    1、获取参数，页数page，默认1
    2、校验参数，int(page)
    3、查询数据库，为管理员，分页
    4、遍历查询结果，转成字典数据
    5、返回模板admin/user_list.html，users,total_page,current_page
    :return:
    """
    page = request.args.get('p', '1')
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
    users = []
    follows = []
    current_page = 1
    total_page = 1
    try:
        paginate = User.query.filter(User.is_admin==False).paginate(page, constants.USER_FOLLOWED_MAX_COUNT, False)
        current_page = paginate.page
        total_page = paginate.pages
        users = paginate.items
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据错误')
    # 定义容器遍历查询结果
    user_dict_list = []
    for user in users:
        user_dict_list.append(user.to_admin_dict())
    data = {
        'users': user_dict_list,
        'current_page': current_page,
        'total_page': total_page
    }
    return render_template('admin/user_list.html', data=data)







@admin_blu.route('/news_review')
def news_review():
    """
    新闻审核列表
    1、获取参数，页数p，默认1，关键字参数keywords，默认None
    2、校验参数，int(page)
    3、定义过滤条件，filter[News.status!=0]，如果keywords存在，添加到过滤条件中
    4、查询新闻数据库,默认按照新闻的发布时间，分页
    5、遍历查询结果
    6、返回模板admin/news_review.html,total_page,current_page,news_list

    :return:
    """
    page = request.args.get("p", 1)
    keywords = request.args.get("keywords", None)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    current_page = 1
    total_page = 1

    filters = [News.status != 0]
    # 如果关键字存在，那么就添加关键字搜索
    if keywords:
        filters.append(News.title.contains(keywords))
    try:
        paginate = News.query.filter(*filters) \
            .order_by(News.create_time.desc()) \
            .paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)

        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_review_dict())

    data = {"total_page": total_page, "current_page": current_page, "news_list": news_dict_list}

    return render_template('admin/news_review.html', data=data)


@admin_blu.route('/news_review_detail/<int:news_id>')
def news_review_detail(news_id):
    """
    新闻详情
    1、根据news_id查询数据库
    2、判断查询结果
    3、返回模板，news:news.to_dict()

    :param news_id:
    :return:
    """
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
    if not news:
        return render_template('admin/news_review_detail.html',data={'errmsg':'未查到数据'})
    data = {"news":news.to_dict()}
    return render_template('admin/news_review_detail.html',data=data)


@admin_blu.route('/news_review_action',methods=['POST'])
def news_review_action():
    """
    新闻审核
    1、获取参数，news_id,action
    2、校验参数完整
    3、校验参数action是否为accept,reject
    4、查询新闻数据，校验查询结果
    5、判断action，如果接受，news_status = 0
    6、否则获取拒绝原因，reason,
        news_status = -1
        news_reason = reason
    7、返回结果

    :return:
    """
    news_id = request.json.get('news_id')
    action = request.json.get('action')
    if not all([news_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    if action not in("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数类型错误")

    # 查询到指定的新闻数据
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据")

    if action == "accept":
        # 代表接受
        news.status = 0
    else:
        # 代表拒绝
        reason = request.json.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="请输入拒绝原因")
        news.status = -1
        news.reason = reason
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')

    return jsonify(errno=RET.OK, errmsg="OK")


@admin_blu.route('/news_edit')
def news_edit():
    """
    新闻板式编辑
    1、获取参数，页数p，默认1，关键字参数keywords，默认None
    2、校验参数，int(page)
    3、初始化变量,news_list[],current_page = 1,total_page = 1
    4、定义过滤条件，filter[News.status==0]，如果keywords存在，添加到过滤条件中
    5、查询新闻数据库,默认按照新闻的发布时间，分页
    6、遍历查询结果
    7、返回模板admin/news_review.html,total_page,current_page,news_list

    :return:
    """
    page = request.args.get('p','1')
    keywords = request.args.get('keywords',None)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
    news_list = []
    current_page = 1
    total_page = 1
    filters = [News.status != 0]
    if keywords:
        filters.append(News.title.contains(keywords))
    try:
        paginate = News.query.filter(*filters).paginate(page,constants.ADMIN_NEWS_PAGE_MAX_COUNT,False)
        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())
    data = {
        'total_page':total_page,
        'current_page':current_page,
        'news_list':news_dict_list
    }
    return render_template('admin/news_edit.html',data=data)



@admin_blu.route('/news_edit_detail',methods=['GET','POST'])
def news_edit_detail():
    """
    新闻编辑详情
    1、如果get请求，获取news_id，校验参数存在，转成int，默认渲染模板
    2、查询数据库，校验查询结果
    3、查询分类数据，Category
    4、遍历查询结果，确认新闻分类属于当前分类，如果是cate_dict['is_selected'] = True
    5、移除'最新'的分类，category_dict_li.pop(0)
    6、返回模板admin/news_edit_detail.html，news，categories
    7、如果post请求，获取表单参数，news_id,title,digest,content,index_image,category_id
    8、判断参数完整性
    9、查询数据库，校验结果，确认新闻的存在
    10、读取图片数据，调用七牛云接口上传图片，获取图片名称，拼接图片绝对路径
    11、保存数据到数据库，title、digest、content、category_id
    12、返回结果

    :return:
    """
    if request.method == 'GET':
        news_id = request.args.get('news_id')
        if not news_id:
            abort(404)
        try:
            news_id = int(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_edit_detail.html',errmsg='参数类型错误')
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_edit_detail.html',errmsg='查询数据错误')
        if not news:
            return render_template('admin/news_edit_detail.html',errmsg='未查询到数据')
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_edit_detail.html',errmsg='查询分类数据错误')
        category_dict_list = []
        # 遍历分类数据，需要判断当前遍历到的分类和新闻所属分类一致
        for category in categories:
            cate_dict = category.to_dict()
            if category.id == news.category_id:
                cate_dict['is_selected'] = True
            category_dict_list.append(cate_dict)
        category_dict_list.pop(0)
        data = {
            'news':news.to_dict(),
            'categories':category_dict_list
        }
        return render_template('admin/news_edit_detail.html',data=data)
    news_id = request.form.get('news_id')
    title = request.form.get('title')
    digest = request.form.get('digest')
    content = request.form.get('content')
    index_image = request.files.get('index_image')
    category_id = request.form.get('category_id')

    if not all([title,digest,content,category_id]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据错误')
    if not news:
        return jsonify(errno=RET.NODATA,errmsg='无新闻数据')
    if index_image:
        image = index_image.read()
        try:
            image_name = storage(image)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR,errmsg='上传图片失败')
        news.image_url = constants.QINIU_DOMIN_PREFIX + image_name
    news.title = title
    news.digest = digest
    news.content = content
    news.category_id = category_id

    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    return jsonify(errno=RET.OK,errmsg='OK')



@admin_blu.route('/news_type',methods=['GET','POST'])
def news_type():
    """
    新闻分类
    1、如果get请求，查询分类数据，遍历查询结果，移除'最新'的分类
    2、返回模板admin/news_type.html,categories
    3、如果post请求，获取参数，name,id(表示编辑已存在的分类)
    4、校验name参数存在
    5、如果id存在(即修改已有的分类)，转成int，根据分类id查询数据库，校验查询结果，category.name = name
    6、实例化分类对象，保存分类名称，提交数据到数据库
    7、返回结果

    :return:
    """
    if request.method == 'GET':
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/news_type.html',errmsg='查询数据错误')
        categories_dict_list = []
        for category in categories:
            categories_dict_list.append(category.to_dict())
        categories_dict_list.pop(0)
        data = {
            'categories':categories_dict_list
        }
        return render_template('admin/news_type.html',data=data)
    cname = request.json.get('name')
    cid = request.json.get('id')
    if not cname:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    if cid:
        try:
            cid = int(cid)
            category = Category.query.get(cid)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='查询数据错误')
        if not category:
            return jsonify(errno=RET.NODATA,errmsg='未查询到分类数据')
        category.name = cname
    else:
        category = Category()
        category.name = cname
        db.session.add(category)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    return jsonify(errno=RET.OK,errmsg='OK')








