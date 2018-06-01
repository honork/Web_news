from flask import Flask,session
# 导入扩展flask-script
from flask_script import Manager
# 导入扩展flask-migrate
from flask_migrate import Migrate,MigrateCommand
# 导入扩展flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
# 导入扩展flask-session,配置session信息的存储
from flask_session import Session

# 导入配置对象
from config import Config

app = Flask(__name__)
# 使用配置对象
app.config.from_object(Config)

# 实例化Session对象
Session(app)

db = SQLAlchemy(app)

# 实例化管理器对象
manage = Manager(app)
# 使用迁移框架
Migrate(app,db)
# 通过管理器对象集成迁移命令
manage.add_command('db',MigrateCommand)


@app.route('/')
def index():
    session['name'] = '2018'
    return 'index'



if __name__ == '__main__':
    # app.run(debug=True)
    manage.run()