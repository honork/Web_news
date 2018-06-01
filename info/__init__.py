from flask import Flask
# 导入扩展flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
# 导入扩展flask-session,配置session信息的存储
from flask_session import Session
# 导入扩展flask-wtf
from flask_wtf import CSRFProtect
# 导入配置对象的字典
from config import config
# 导入日志模块
import logging
# 导入日志模块中的文件处理
from logging.handlers import RotatingFileHandler

# 实例化sqlalchemy对象
db = SQLAlchemy()

# 集成项目日志
# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG) # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)


# 创建程序实例的工厂方法，动态的加载配置对象
def create_app(config_name):
    app = Flask(__name__)
    # 使用配置对象
    app.config.from_object(config[config_name])
    # 实例化Session对象
    Session(app)
    # 实例化CSRF
    CSRFProtect(app)
    # 把db对象和app进行关联
    db.init_app(app)


    return app