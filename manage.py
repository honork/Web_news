from flask import session
# 导入扩展flask-script
from flask_script import Manager
# 导入扩展flask-migrate
from flask_migrate import Migrate,MigrateCommand
# 导入info模块创建的程序实例app
from info import create_app,db

# 调用工厂方法，获取app
app = create_app('development')

# 实例化管理器对象
manage = Manager(app)
# 使用迁移框架
Migrate(app,db)
# 通过管理器对象集成迁移命令
manage.add_command('db',MigrateCommand)


@app.route('/')
def index():
    session['name'] = '2018'
    return 'index2016'



if __name__ == '__main__':
    # app.run(debug=True)
    manage.run()