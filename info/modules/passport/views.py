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




