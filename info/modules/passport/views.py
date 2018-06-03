# 导入蓝图对象
from flask import request, jsonify, current_app, make_response

from . import passport_blu
# 导入自定义的状态码
from info.utils.response_code import RET
# 导入captcha扩展
from info.utils.captcha.captcha import captcha
# 导入redis实例
from info import redis_store,constants


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
    real_image_code = redis._store.get(key)
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


    pass



