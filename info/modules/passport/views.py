# 导入蓝图对象
from . import passport_blu



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

    pass


