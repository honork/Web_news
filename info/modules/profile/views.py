from flask import g, redirect, render_template, request, jsonify, current_app, session

from . import profile_blu
# 导入登录验证装饰器
from info.utils.commons import login_required
# 导入自定义的状态码
from info.utils.response_code import RET
# 导入SQLAlchemy对象
from info import db,constants
# 导入七牛云
from info.utils.image_storage import storage
# 导入模型类
from info.models import Category



@profile_blu.route('/info')
@login_required
def user_info():
    """
    用户信息页面
    1、尝试获取用户信息
    2、判断用户如果没有登录，重定向到项目首页
    3、默认加载模板页面

    :return:
    """
    user = g.user
    # 判断用户是否登录
    if not user:
        return redirect('/')
    # 调用模型类中的方法，获取用户的基本信息
    data = {
        'user':user.to_dict()
    }
    # 默认加载模板页面
    return render_template('news/user.html',data=data)

@profile_blu.route('/base_info',methods=['POST','GET'])
@login_required
def base_info():
    """
    个人信息修改
    1、如果是post请求，获取参数，nick_name,signature,gender
    2、检查参数的完整性
    3、判断用户的性别非男即女
    4、保存用户修改的个人信息
    5、提交数据
    6、返回结果


    :return:
    """
    user = g.user
    if request.method == 'GET':
        data = {
            'user':user.to_dict()
        }
        return render_template('news/user_base_info.html',data=data)
    # 如果是post请求，获取参数
    nick_name = request.json.get('nick_name')
    signature = request.json.get('signature')
    gender = request.json.get('gender')
    # 判断参数的完整性
    if not all([nick_name,signature,gender]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    # 判断用户选择的性别
    if gender not in ['MAN','WOMEN']:
        return jsonify(errno=RET.PARAMERR,errmsg='参数格式错误')
    # 保存用户数据
    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender
    # 提交数据到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存用户信息失败')

    session['nick_name'] = user.nick_name
    # 返回结果
    return jsonify(errno=RET.OK,errmsg='OK')

@profile_blu.route('/pic_info',methods=['GET','POST'])
@login_required
def pic_info():
    """
    个人中心：上传头像
    1、如果是get请求，加载模板页面
    2、如果是post请求，获取参数，是模板页面中的form表单中的input表单的name属性
    3、读取图片文件的内容
    4、把读取结果给七牛云上传用户头像
    5、接收七牛云返回的图片的名称
    6、提交用户头像数据,图片的相对路径
    7、拼接图片的绝对路径
    8、返回结果

    :return:
    """
    user = g.user
    if request.method == 'GET':
        data = {
            'user':user.to_dict()
        }
        return render_template('news/user_pic_info.html',data=data)
    # 获取前端post请求的图片文件
    avatar = request.files.get('avatar')
    # 校验参数的存在
    if not avatar:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    # 读取图片数据
    try:
        avatar_data = avatar.read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数格式错误')
    # 调用七牛云，实现图片的上传,保存图片名称
    try:
        image_name = storage(avatar_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='上传图片失败')
    # 保存图片数据到用户数据中,保存的是图片的相对路径（名称）
    user.avatar_url = image_name
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    # 拼接图片的绝对路径，七牛云的空间外链域名+图片名称
    avatar_url = constants.QINIU_DOMIN_PREFIX + image_name
    # 返回结果
    return jsonify(errno=RET.OK,errmsg='OK',data={'avatar_url':avatar_url})

@profile_blu.route("/pass_info",methods=['GET','POST'])
@login_required
def pass_info():
    """
    个人中心：修改密码
    1、判断请求方法，如果get请求，默认渲染模板页面
    2、获取参数，old_password,new_password
    3、检查参数的完整性
    4、获取用户信息，用来对旧密码进行校验是否正确
    5、更新用户新密码
    6、返回结果
    :return:
    """
    # 如果是get请求,默认渲染模板页面
    if request.method == 'GET':
        return render_template('news/user_pass_info.html')
    # 获取参数
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')
    # 检查参数的完整性
    if not all([old_password,new_password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    # 获取用户的登录信息
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')
    # 校验密码是否正确
    if not user.check_password(old_password):
        return jsonify(errno=RET.PWDERR,errmsg='旧密码错误')
    # 如果旧密码正确，更新新密码到数据库
    user.password = new_password
    # 提交数据到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    # 返回结果
    return jsonify(errno=RET.OK,errmsg='OK')

@profile_blu.route('/news_release',methods=['GET','POST'])
@login_required
def news_release():
    """
    个人中心：新闻发布
    1、判断请求方法，get请求加载新闻分类数据
    2、查询所有的分类数据
    3、判断查询结果
    4、遍历查询结果
    5、移除最新的分类id
    6、把分类返回给模板
    :return:
    """
    if request.method == 'GET':
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='查询数据失败')
        # 检查查询结果是否有数据
        if not categories:
            return jsonify(errno=RET.NODATA,errmsg='无分类数据')
        # 定义容器，存储新闻分类的字典数据
        category_list = []
        for category in categories:
            category_list.append(category.to_dict())
        # 移除新闻分类的id为1(最新)
        category_list.pop(0)
        data = {
            'categories':category_list
        }
        return render_template('news/user_news_release.html',data=data)








