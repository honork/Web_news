# 导入蓝图对象
import random

from flask import request, jsonify, current_app, make_response, session

from info.models import User
from . import passport_blu
# 导入自定义的状态码
from info.utils.response_code import RET
# 导入captcha扩展
from info.utils.captcha.captcha import captcha
# 导入redis实例
from info import redis_store,constants,db
# 导入正则模块
import re
# 导入云通讯
from info.libs.yuntongxun import sms



@passport_blu.route('/image_code')
def generate_image_code():
    """
    生成图片验证码
    1、获取参数，前端生成图片验证码的后缀名，uuid
    request.args.get()
    2、校验参数是否存在；
    3、调用扩展包，生成图片验证码，name,text,image
    4、在redis数据库中保存图片验证码的内容；
    5、使用响应对象,来返回图片，修改默认响应的数据类型
    response = make_response(image)
    response.headers['Content-Type'] = 'image/jpg'
    6、返回结果
    return response
    :return:
    """
    # 获取参数
    image_code_id = request.args.get('image_code_id')
    # 判断参数不存在
    if not image_code_id:
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    # 调用扩展来生成图片验证码
    name,text,image = captcha.generate_captcha()
    print(text)
    # 保存图片验证码到redis数据库
    try:
        redis_store.setex('ImageCode_' + image_code_id,constants.IMAGE_CODE_REDIS_EXPIRES,text)
    except Exception as e:
        # 记录操作redis数据库的异常信息
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='保存图片验证码失败')
    else:
        # 使用响应对象返回图片本身
        response = make_response(image)
        # 设置响应的数据类型
        response.headers['Content-Type'] = 'image/jpg'
        # 返回响应
        return response


@passport_blu.route('/sms_code',methods=['POST'])
def send_sms_code():
    """
    发送短信
    1、获取参数，mobile,image_code,image_code_id
    2、判断参数的完整性
    3、验证手机号格式，正则
    4、校验图片验证码，从redis读取真实的图片验证码
    real_image_code = redis_store.get(key)
    5、判断获取结果是否存在，如果不存在，表示已过期
    6、如果图片验证码存在，需要删除图片验证码，本质是任意一个图片验证码，只能读取一次；
    7、比较图片验证码内容是否一致；
    8、查询mysql数据库，确认手机号是否已经注册；
    9、生成短信随机数；六位
    10、把短信随机数保存到redis数据库中，设置有效期
    11、调用云通讯扩展，来发送短信，保存发送结果
    12、判断发送结果是否成功。
    :return:
    """
    # 获取手机号、用户输入的图片验证码内容，图片验证码编号
    mobile = request.json.get('mobile')
    image_code = request.json.get('image_code')
    image_code_id = request.json.get('image_code_id')
    print(image_code)
    # 检查参数的完整性
    # if mobile and image_code and image_code_id
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不完整')
    # 检查手机号格式
    if not re.match(r'^1[3456789]\d{9}$',mobile):
        return jsonify(errno=RET.PARAMERR,errmsg='手机号格式错误')
    # 检查图片验证码，首先从redis获取真实的图片验证码
    try:
        real_image_code = redis_store.get('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='获取图片验证码失败')
    # 判断获取结果是否存在
    if not real_image_code:
        return jsonify(errno=RET.NODATA,errmsg='图片验证码已经过期')
    # 删除图片验证码，因为图片验证码只能校验一次
    try:
        redis_store.delete('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
    # 比较图片验证码是否正确,忽略大小写
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR,errmsg='图片验证码不一致')
    # 查询mysql数据库，确认用户是否注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.loggere.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询用户信息失败')
    else:
        # 判断查询结果是否存在
        if user is not None:
            return jsonify(errno=RET.DATAEXIST,errmsg='手机号已注册')
    # 构造六位数的短信随机数
    sms_code = '%06d' % random.randint(0, 999999)
    # print(sms_code)
    # 保存到redis数据库中
    try:
        redis_store.setex('SMSCode_' + mobile,constants.SMS_CODE_REDIS_EXPIRES,sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    # 调用云通讯发送短信验证码
    try:
        ccp = sms.CCP()
        # 调用模板方法，发送短信，保存发送结果
        result = ccp.send_template_sms(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES/60],1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='发送短信异常')
    # 判断发送结果是否成功
    if result == 0:
        return jsonify(errno=RET.OK,errmsg='发送成功')
    else:
        return jsonify(errno=RET.THIRDERR,errmsg='发送失败')


# http://127.0.0.1:5000/passport/register
@passport_blu.route('/register',methods=['POST'])
def register():
    """
    用户注册
    1、获取参数，mobile/sms_code/password
    2、校验参数的完整性
    3、检查手机号的格式
    4、短信验证码进行比较
    5、尝试从redis数据库中获取真实的短信验证码
    6、判断获取结果是否有数据
    7、比较短信验证码是否正确
    8、如果短信验证码正确，删除redis中的短信验证码
    9、验证手机号是否注册
    10、构造模型类对象，准备存储用户信息
    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    11、需要对密码进行加密存储，
    user.password = password
    12、保存数据到mysql数据库中
    13、把用户信息缓存到redis数据库中
    session['user_id'] = user.id
    14、返回结果
    :return:
    """
    # 获取参数
    # user_datarequest.get_json()
    # mobile = user_data['mobile']
    mobile = request.json.get('mobile')
    sms_code = request.json.get('sms_code')
    password = request.json.get('password')
    # 检查参数的完整性
    if not all([mobile,sms_code,password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不完整')
    # 检查手机号格式
    if not re.match(r'1[3456789]\d{9}$',mobile):
        return jsonify(errno=RET.PARAMERR,errmsg='手机号格式错误')
    # 尝试从redis中获取真实的短信验证码
    try:
        real_sms_code = redis_store.get('SMSCode_' + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询数据失败')
    # 校验查询结果是否存在
    if not real_sms_code:
        return jsonify(errno=RET.NODATA,errmsg='短信验证码已过期')
    # 比较短信验证码是否正确
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR,errmsg='短信验证码错误')
    # 如果短信验证码输入正确，删除redis中的短信验证码
    try:
        redis_store.delete('SMSCode_' + mobile)
    except Exception as e:
        current_app.logger.error(e)
    # 根据手机号进行查询，确认用户是否注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询用户数据失败')
    else:
        # 判断用户是否存在
        if user is not None:
            return jsonify(errno=RET.DATAEXIST,errmsg='手机号已注册')
    # 构造模型类对象，准备存储数据到myqsl数据库中
    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    # 实际上调用了模型类中的对密码加密的方法，sha256
    user.password = password
    # 把用户数据提交到数据库中
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        # 提交数据发生异常，需要进行回滚
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    # 使用session缓存用户信息到redis数据库中
    session['user_id'] = user.id
    session['mobile'] = mobile
    session['nick_name'] = mobile
    # user_id = session.get('user_id')
    # 返回结果
    return jsonify(errno=RET.OK,errmsg='注册成功')









