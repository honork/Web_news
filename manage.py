from flask import session
# 导入扩展flask-script
from flask_script import Manager
# 导入扩展flask-migrate
from flask_migrate import Migrate,MigrateCommand
# 导入info模块创建的程序实例app
from info import create_app,db
# 导入models
from info import models


# 调用工厂方法，获取app
app = create_app('development')

# 实例化管理器对象
manage = Manager(app)
# 使用迁移框架
Migrate(app,db)
# 通过管理器对象集成迁移命令
manage.add_command('db',MigrateCommand)



if __name__ == '__main__':
    # 输出路由映射
    print(app.url_map)
    manage.run()