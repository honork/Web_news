from flask import Flask
# 导入扩展flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
# 导入扩展flask-session,配置session信息的存储
from flask_session import Session
# 导入扩展flask-wtf
from flask_wtf import CSRFProtect

# 实例化sqlalchemy对象
db = SQLAlchemy()

# 导入配置对象的字典
from config import config

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
