# 创建蓝图对象
from flask import Blueprint

passport_blu = Blueprint('passport_blu',__name__)


# 把使用蓝图对象的文件导入到创建蓝图对象的下面
from . import views


